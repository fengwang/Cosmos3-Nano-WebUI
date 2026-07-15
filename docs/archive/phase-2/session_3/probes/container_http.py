"""Action shell: relay one HTTP request to a compose service's own localhost — needed because
`deploy/docker-compose.fp8.yml`/`.nvfp4.yml` do not publish the `vllm-omni` service's port 8000
to the host (only `api`'s is published). This session cannot edit the compose files (not in
session_3_contract.yaml's allowed blast radius), so "direct" calls run *inside* the container's
own network namespace via `docker compose exec`, using a static stdlib-only relay script piped
over stdin/stdout — no shell interpolation of request content, no new production dependency.
"""
from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

_RELAY_SCRIPT = """
import sys, json, base64, urllib.request, urllib.error
req = json.loads(sys.stdin.read())
body = base64.b64decode(req["body_b64"]) if req.get("body_b64") else None
headers = {"Content-Type": req["content_type"]} if req.get("content_type") else {}
r = urllib.request.Request("http://localhost:8000" + req["path"], data=body,
                            method=req["method"], headers=headers)
try:
    with urllib.request.urlopen(r, timeout=req.get("timeout", 60)) as resp:
        status, payload = resp.status, resp.read()
except urllib.error.HTTPError as exc:
    status, payload = exc.code, exc.read()
print(json.dumps({"status": status, "body_b64": base64.b64encode(payload).decode()}))
"""


def exec_http_in_container(
    compose_file: str,
    service: str,
    *,
    method: str,
    path: str,
    body: bytes = b"",
    content_type: str = "",
    timeout: float = 60.0,
) -> tuple[int, bytes]:
    """Action: run one HTTP request against `service`'s own `localhost:8000` via `docker
    compose exec`. Returns (status_code, response_body_bytes).

    Raises `subprocess.CalledProcessError`/`subprocess.TimeoutExpired` on an exec failure
    (container not running, `python3` missing, etc.) — an environment failure, left to
    propagate to the caller's single narrow boundary rather than masked here.
    """
    request = json.dumps(
        {
            "method": method,
            "path": path,
            "content_type": content_type,
            "body_b64": base64.b64encode(body).decode() if body else "",
            "timeout": timeout,
        }
    )
    result = subprocess.run(
        ["docker", "compose", "-f", compose_file, "exec", "-T", service, "python3", "-c", _RELAY_SCRIPT],
        input=request,
        capture_output=True,
        text=True,
        timeout=timeout + 30,
        check=True,
        cwd=REPO_ROOT,  # `compose_file` is repo-root-relative; the caller's own cwd may differ
    )
    response = json.loads(result.stdout.strip().splitlines()[-1])
    return response["status"], base64.b64decode(response["body_b64"])
