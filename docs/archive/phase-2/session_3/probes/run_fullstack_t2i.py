#!/usr/bin/env python3
"""T5/T6: full-stack T2I through the api (X-API-Key -> job -> artifact), never bypassing auth
and never reading the artifact straight from the generation container
(docs/session_3/specs/gpu-validation-probes.md, "Full-stack generation verification").

Usage: uv run python run_fullstack_t2i.py --checkpoint {fp8,nvfp4}
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from compose_lifecycle import bring_up, tear_down
from constants import (
    ARTIFACT_DIR,
    CHECKPOINTS,
    FULLSTACK_TEST_API_KEY,
    REDACT_PREFIXES,
    T2I_DIMENSION,
    T2I_PROMPT,
    T2I_SEED,
    VLLM_OMNI_COMMIT,
)
from env_probe import get_hardware_and_driver
from evidence_io import write_fragment
from lib import (
    Verdict,
    build_evidence_record,
    check_job_terminal,
    check_valid_image,
    content_hash,
    sanitize_error_text,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
API_BASE = "http://localhost:8000"
API_READY_TIMEOUT_S = 120.0
JOB_TERMINAL_TIMEOUT_S = 2400.0  # covers vLLM-Omni cold start (docs/model_setup.md §9: up to 1800s) + generation
JOB_POLL_INTERVAL_S = 10.0


def _http_json(method: str, path: str, *, headers: dict, body: bytes | None = None, timeout: float = 30.0):
    req = urllib.request.Request(API_BASE + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — fixed local base URL
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(body_text)
        except json.JSONDecodeError:
            return exc.code, {"raw": body_text}


def _wait_api_ready() -> None:
    deadline = time.monotonic() + API_READY_TIMEOUT_S
    last_error = "never attempted"
    while time.monotonic() < deadline:
        try:
            status, _ = _http_json("GET", "/v1/health/ready", headers={}, timeout=10)
            if status == 200:
                return
            last_error = f"HTTP {status}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
        time.sleep(5.0)
    raise TimeoutError(f"api did not become ready within {API_READY_TIMEOUT_S:.0f}s (last: {last_error})")


def _poll_job_until_terminal(job_id: str, api_key: str) -> tuple[str, ...]:
    history: list[str] = []
    deadline = time.monotonic() + JOB_TERMINAL_TIMEOUT_S
    while time.monotonic() < deadline:
        status, doc = _http_json("GET", f"/v1/jobs/{job_id}", headers={"X-API-Key": api_key}, timeout=30)
        if status != 200:
            raise RuntimeError(f"GET /v1/jobs/{job_id} -> HTTP {status}: {doc!r}")
        history.append(str(doc.get("status")))
        if check_job_terminal(tuple(history)) == Verdict.PASS or history[-1] in ("failed", "cancelled"):
            return tuple(history)
        time.sleep(JOB_POLL_INTERVAL_S)
    history.append("timeout")
    return tuple(history)


def run(checkpoint: str) -> Verdict:
    spec = CHECKPOINTS[checkpoint]
    task_id = f"fullstack_t2i_{checkpoint}"
    hardware, driver_cuda = "unknown", "unknown"
    request_body = {"prompt": T2I_PROMPT, "seed": T2I_SEED, "resolution": T2I_DIMENSION}
    request_shape = {"mode": "t2i", **request_body}
    notes = ""
    artifact_path = None
    artifact_metadata = None
    try:
        hardware, driver_cuda = get_hardware_and_driver()
        api_key = FULLSTACK_TEST_API_KEY
        bring_up(checkpoint, extra_env={"COSMOS3_API_KEY": api_key})
        _wait_api_ready()
        status, submitted = _http_json(
            "POST", "/v1/generation/t2i",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            body=json.dumps(request_body).encode(), timeout=30,
        )
        if status != 202:
            raise RuntimeError(f"POST /v1/generation/t2i -> HTTP {status}: {submitted!r}")
        job_id = submitted["id"]
        history = _poll_job_until_terminal(job_id, api_key)
        request_shape["job_status_history"] = list(history)
        if check_job_terminal(history) == Verdict.FAIL:
            raise RuntimeError(f"job {job_id} did not succeed: status history {history}")
        artifact_req = urllib.request.Request(
            f"{API_BASE}/v1/jobs/{job_id}/artifact", headers={"X-API-Key": api_key},
        )
        with urllib.request.urlopen(artifact_req, timeout=60) as resp:  # noqa: S310 — fixed local base URL
            image_bytes = resp.read()
        if check_valid_image(image_bytes, expected_dims=(T2I_DIMENSION, T2I_DIMENSION)) == Verdict.FAIL:
            raise RuntimeError("retrieved artifact failed the image validity/dimension check")
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = ARTIFACT_DIR / f"fullstack_t2i_{checkpoint}.png"
        out_path.write_bytes(image_bytes)
        artifact_path = out_path.name  # filename only; the scratch dir's absolute path is host-specific (INV-1)
        artifact_metadata = {
            "format": "png", "size_bytes": len(image_bytes), "dims": [T2I_DIMENSION, T2I_DIMENSION],
            "job_id": job_id, "sha256": content_hash(image_bytes),
        }
        verdict = Verdict.PASS
    except Exception as exc:  # noqa: BLE001 — single narrow boundary; see gpu-validation-probes.md
        verdict = Verdict.FAIL
        notes = sanitize_error_text(f"{type(exc).__name__}: {exc}", REDACT_PREFIXES)
    finally:
        # Always tear down, even if bring_up only partially succeeded or was never reached —
        # `make down` is a no-op-safe idempotent call.
        tear_down()

    record = build_evidence_record(
        task_id=task_id,
        hardware=hardware,
        driver_cuda=driver_cuda,
        checkpoint_repo=spec.repo_id,
        checkpoint_revision=spec.revision,
        vllm_omni_commit=VLLM_OMNI_COMMIT,
        request_shape=request_shape,
        artifact_path=artifact_path,
        artifact_metadata=artifact_metadata,
        verdict=verdict,
        run_at=datetime.now(UTC).isoformat(),
        notes=notes,
    )
    path = write_fragment(task_id, record)
    print(f"[{checkpoint}] verdict={verdict.name} notes={notes!r} -> {path}")
    return verdict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", choices=sorted(CHECKPOINTS), required=True)
    args = parser.parse_args()
    result = run(args.checkpoint)
    raise SystemExit(0 if result == Verdict.PASS else 1)
