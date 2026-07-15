#!/usr/bin/env python3
"""T3/T4: direct vLLM-Omni T2I generation, bypassing the api layer entirely
(docs/session_3/specs/gpu-validation-probes.md, "Direct generation verification").

Usage: uv run python run_direct_t2i.py --checkpoint {fp8,nvfp4}
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from compose_lifecycle import bring_up, compose_file, tear_down
from constants import (
    ARTIFACT_DIR,
    CHECKPOINTS,
    REDACT_PREFIXES,
    T2I_DIMENSION,
    T2I_PROMPT,
    T2I_SEED,
    VLLM_OMNI_COMMIT,
)
from container_http import exec_http_in_container
from env_probe import get_hardware_and_driver
from evidence_io import write_fragment
from lib import Verdict, build_evidence_record, check_valid_image, content_hash, sanitize_error_text

REPO_ROOT = Path(__file__).resolve().parents[3]
READY_TIMEOUT_S = 1900.0  # matches the documented --init-timeout 1800 (model_setup.md §9) + margin
READY_POLL_INTERVAL_S = 15.0
GENERATION_TIMEOUT_S = 300.0
_UNKNOWN_HW = ("unknown", "unknown")


def _wait_ready(compose_file: str) -> None:
    """Action: poll vLLM-Omni's own /v1/models until it responds 200, or raise on timeout."""
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


def _build_request() -> dict:
    return {
        "prompt": T2I_PROMPT,
        "size": f"{T2I_DIMENSION}x{T2I_DIMENSION}",
        "n": 1,
        "response_format": "b64_json",
        "num_inference_steps": 35,
        "guidance_scale": 6.0,
        "seed": T2I_SEED,
    }


def run(checkpoint: str) -> Verdict:
    spec = CHECKPOINTS[checkpoint]
    compose_path = compose_file(checkpoint)
    task_id = f"direct_t2i_{checkpoint}"
    hardware, driver_cuda = _UNKNOWN_HW
    request_shape = {"mode": "t2i", **_build_request()}
    notes = ""
    artifact_path = None
    artifact_metadata = None
    try:
        hardware, driver_cuda = get_hardware_and_driver()
        bring_up(checkpoint)
        _wait_ready(compose_path)
        status, resp_bytes = exec_http_in_container(
            compose_path, "vllm-omni", method="POST", path="/v1/images/generations",
            body=json.dumps(_build_request()).encode(), content_type="application/json",
            timeout=GENERATION_TIMEOUT_S,
        )
        if status != 200:
            raise RuntimeError(f"POST /v1/images/generations -> HTTP {status}: {resp_bytes[:300]!r}")
        doc = json.loads(resp_bytes)
        image_bytes = base64.b64decode(doc["data"][0]["b64_json"])
        if check_valid_image(image_bytes, expected_dims=(T2I_DIMENSION, T2I_DIMENSION)) == Verdict.FAIL:
            raise RuntimeError("generated artifact failed the image validity/dimension check")
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = ARTIFACT_DIR / f"direct_t2i_{checkpoint}.png"
        out_path.write_bytes(image_bytes)
        artifact_path = out_path.name  # filename only; the scratch dir's absolute path is host-specific (INV-1)
        artifact_metadata = {
            "format": "png", "size_bytes": len(image_bytes), "dims": [T2I_DIMENSION, T2I_DIMENSION],
            "sha256": content_hash(image_bytes),
        }
        verdict = Verdict.PASS
    except Exception as exc:  # noqa: BLE001 — single narrow boundary; see gpu-validation-probes.md
        verdict = Verdict.FAIL
        notes = sanitize_error_text(f"{type(exc).__name__}: {exc}", REDACT_PREFIXES)
    finally:
        # Always tear down, even if bring_up only partially succeeded (e.g. api/webui built
        # but vllm-omni's build failed) — `make down` is a no-op-safe idempotent call.
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
