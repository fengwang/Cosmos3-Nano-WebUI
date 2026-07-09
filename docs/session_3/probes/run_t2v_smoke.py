#!/usr/bin/env python3
"""T7: best-effort, direct-only T2V smoke (docs/session_3/specs/t2v-smoke-verification.md).

NVFP4 is attempted first (lower bit-width leaves more VRAM headroom); FP8 is tried once if
NVFP4 does not fit. Outcome is always recorded (PASS/FAIL/SCOPED_OUT) — a T2V failure never
blocks the session and never looks like a crashed probe.

Usage: uv run python run_t2v_smoke.py
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from compose_lifecycle import bring_up, compose_file, tear_down
from constants import ARTIFACT_DIR, CHECKPOINTS, REDACT_PREFIXES, VLLM_OMNI_COMMIT
from container_http import exec_http_in_container
from env_probe import get_hardware_and_driver
from evidence_io import write_fragment
from lib import (
    Verdict,
    build_evidence_record,
    check_job_terminal,
    check_valid_video,
    content_hash,
    encode_multipart,
    sanitize_error_text,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
READY_TIMEOUT_S = 1900.0
READY_POLL_INTERVAL_S = 15.0
POLL_INTERVAL_S = 10.0
OVERALL_TIMEOUT_S = 900.0  # a smoke, not a full run — tighter than the T2I probes' budget

PROMPT = "a red apple slowly rotating on a wooden table"
SEED = 42
DIMENSION = 256  # lowest documented supported size (docs/model_setup.md §9)
NUM_FRAMES = 9
FPS = 8
BOUNDARY = "gpus3t2vsmokeboundary"


def _wait_ready(compose_file: str) -> None:
    deadline = time.monotonic() + READY_TIMEOUT_S
    last_error = "never attempted"
    while time.monotonic() < deadline:
        try:
            status, _ = exec_http_in_container(
                compose_file, "vllm-omni", method="GET", path="/v1/models", timeout=10,
            )
            if status == 200:
                return
            last_error = f"HTTP {status}"
        except subprocess.CalledProcessError as exc:
            last_error = f"exec failed: {exc}"
        except subprocess.TimeoutExpired:
            last_error = "exec timed out"
        time.sleep(READY_POLL_INTERVAL_S)
    raise TimeoutError(f"vllm-omni did not become ready within {READY_TIMEOUT_S:.0f}s (last: {last_error})")


def _build_form() -> dict[str, str]:
    return {
        "prompt": PROMPT,
        "size": f"{DIMENSION}x{DIMENSION}",
        "num_frames": str(NUM_FRAMES),
        "fps": str(FPS),
        "num_inference_steps": "20",
        "guidance_scale": "6.0",
        "flow_shift": "10.0",
        "seed": str(SEED),
        "max_sequence_length": "4096",
        "extra_params": json.dumps(
            {"use_resolution_template": False, "use_duration_template": False, "guardrails": False}
        ),
    }


def _poll_video_until_terminal(compose_path: str, video_id: str) -> tuple[str, ...]:
    deadline = time.monotonic() + OVERALL_TIMEOUT_S
    history: list[str] = []
    while time.monotonic() < deadline:
        status, poll_bytes = exec_http_in_container(
            compose_path, "vllm-omni", method="GET", path=f"/v1/videos/{video_id}", timeout=30,
        )
        if status != 200:
            raise RuntimeError(f"poll /v1/videos/{video_id} -> HTTP {status}")
        doc = json.loads(poll_bytes)
        history.append(str(doc.get("status", "")).lower())
        if check_job_terminal(tuple(history), success_status="completed") == Verdict.PASS:
            return tuple(history)
        if history[-1] == "failed":
            raise RuntimeError(f"video {video_id} reported failed: {doc}")
        time.sleep(POLL_INTERVAL_S)
    raise TimeoutError(f"video {video_id} did not complete within {OVERALL_TIMEOUT_S:.0f}s")


def _attempt(checkpoint: str) -> tuple[Verdict, str, str | None, dict | None]:
    """Try one T2V smoke on `checkpoint`. Returns (verdict, notes, artifact_path, artifact_metadata).

    Single narrow exception boundary (matching the other three run_*.py scripts) — every
    failure raises internally and is caught once, rather than returning SCOPED_OUT inline at
    each call site. SCOPED_OUT (not FAIL) for every failure remains the deliberate, documented
    simplification in design.md's error-strategy table — this only fixes the boundary shape.
    """
    compose_path = compose_file(checkpoint)
    try:
        bring_up(checkpoint)
        _wait_ready(compose_path)
        content_type, body = encode_multipart(_build_form(), boundary=BOUNDARY)
        status, resp_bytes = exec_http_in_container(
            compose_path, "vllm-omni", method="POST", path="/v1/videos",
            body=body, content_type=content_type, timeout=OVERALL_TIMEOUT_S,
        )
        if status != 200:
            raise RuntimeError(f"POST /v1/videos -> HTTP {status}: {resp_bytes[:300]!r}")
        video_id = json.loads(resp_bytes).get("id")
        if not video_id:
            raise RuntimeError(f"submit response carried no video id: {resp_bytes[:300]!r}")

        _poll_video_until_terminal(compose_path, video_id)

        status, video_bytes = exec_http_in_container(
            compose_path, "vllm-omni", method="GET", path=f"/v1/videos/{video_id}/content", timeout=60,
        )
        if status != 200 or check_valid_video(video_bytes) == Verdict.FAIL:
            raise RuntimeError(f"downloaded content failed video validity check (HTTP {status})")

        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = ARTIFACT_DIR / f"t2v_smoke_{checkpoint}.mp4"
        out_path.write_bytes(video_bytes)
        metadata = {
            "format": "mp4/webm", "size_bytes": len(video_bytes),
            "dims": [DIMENSION, DIMENSION], "num_frames": NUM_FRAMES, "fps": FPS,
            "sha256": content_hash(video_bytes),
        }
        return Verdict.PASS, "", out_path.name, metadata  # filename only (INV-1); see run_direct_t2i.py
    except Exception as exc:  # noqa: BLE001 — single narrow boundary; a T2V failure is never a crash
        notes = sanitize_error_text(f"{type(exc).__name__}: {exc}", REDACT_PREFIXES)
        return Verdict.SCOPED_OUT, notes, None, None
    finally:
        # Always tear down, even if bring_up only partially succeeded —
        # `make down` is a no-op-safe idempotent call.
        tear_down()


def run() -> Verdict:
    try:
        hardware, driver_cuda = get_hardware_and_driver()
    except Exception as exc:  # noqa: BLE001 — a T2V probe never crashes; see module docstring
        hardware, driver_cuda = "unknown", "unknown"
        print(f"[t2v_smoke] hardware probe failed, continuing with unknown: {exc}")
    request_shape = {"mode": "t2v", **_build_form()}
    attempt_order = ["nvfp4", "fp8"]
    notes_by_checkpoint: dict[str, str] = {}
    checkpoint = attempt_order[0]
    verdict, notes, artifact_path, artifact_metadata = (
        Verdict.SCOPED_OUT, "attempt_order was empty", None, None,
    )
    for checkpoint in attempt_order:
        verdict, notes, artifact_path, artifact_metadata = _attempt(checkpoint)
        notes_by_checkpoint[checkpoint] = notes
        if verdict == Verdict.PASS:
            break
    # `checkpoint`/`verdict` hold the last-attempted values whether the loop broke early
    # (success) or ran through both entries (neither passed) — no `else:` branch needed.

    if verdict != Verdict.PASS:
        notes = "; ".join(f"{cp}: {n}" for cp, n in notes_by_checkpoint.items() if n) or "no attempt succeeded"

    spec = CHECKPOINTS[checkpoint]
    record = build_evidence_record(
        task_id="t2v_smoke",
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
    path = write_fragment("t2v_smoke", record)
    print(f"[t2v_smoke:{checkpoint}] verdict={verdict.name} notes={notes!r} -> {path}")
    return verdict


if __name__ == "__main__":
    run()
    raise SystemExit(0)  # T2V outcome never fails the session (SHOULD, not MUST)
