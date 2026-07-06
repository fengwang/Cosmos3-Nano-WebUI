"""The `Work`-shaped vllm-omni adapter (Action shell; torch-free).

``vllm_omni_work(record, report) -> WorkResult`` mirrors ``jobs.gen_client.work`` (same signature,
progress contract, and ``WorkResult``) so the app injects it as ``job_work``. It reduces a ``JobRecord``
to the mode-appropriate vllm-omni request, runs the client, persists the returned bytes under the
artifact volume (INV-8; byte-passthrough preserves fps/frames, INV-P5-3), and returns the artifact path
+ verified precision/parameter metadata (INV-P5-1). Any client failure raises a typed error and writes
no partial artifact.

Mode dispatch (design D-2): t2v/i2v/t2v_audio → async `/v1/videos` (i2v adds an `input_reference` file
part); t2i → `/v1/images/generations` → a PNG; forward_dynamics → sync `/v1/videos/sync` (action
`extra_params`) → the rollout MP4. The base URL is the single deployed generation endpoint
(``endpoint_for``) — a standalone deployment has exactly one plane the orchestrator makes resident.
Refs: session_6/specs/single-checkpoint-serving.md.
"""
from __future__ import annotations

import mimetypes
import os
import re
from collections.abc import Callable
from typing import Any

from engines.vllm_omni.client import (
    FilePart,
    UrllibVideoTransport,
    VideoJobError,
    VideoTransport,
    fd_resolved_params,
    resolved_params,
    run_forward_dynamics_job,
    run_image_job,
    run_video_job,
)
from engines.vllm_omni.endpoints import deployed_checkpoint, endpoint_for
from jobs import artifacts
from jobs.runner import WorkResult
from preprocessing.limits import MediaLimits
from preprocessing.paths import UntrustedPathError, resolve_within

DEFAULT_GEN_TIMEOUT = 7200.0

# Modes served by the vllm-omni plane. Async video: t2v, i2v (adds an input_reference file part),
# t2v_audio (generate_sound). Images API: t2i (-> PNG). Sync action: forward_dynamics (-> rollout MP4).
# Any other mode (inverse_dynamics, policy, ...) fails TYPED — never a silent wrong artifact.
_ASYNC_VIDEO_MODES = frozenset({"t2v", "i2v", "t2v_audio"})
_SUPPORTED_MODES = _ASYNC_VIDEO_MODES | frozenset({"t2i", "forward_dynamics"})
_CONDITIONING_KEYS = ("image_path", "video_path", "audio_path")
_META_KEYS = ("seed", "num_inference_steps", "guidance_scale", "flow_shift", "width", "height", "num_frames")


def _input_allowlist() -> tuple[str, ...]:
    """Action: the trusted conditioning-path allowlist (env, default the artifact volume) — mirrors the edge."""
    raw = os.environ.get("COSMOS3_INPUT_ALLOWLIST")
    return tuple(raw.split(os.pathsep)) if raw else (artifacts.artifacts_dir(),)


def _resolve_conditioning(record: Any) -> dict:
    """Re-resolve any conditioning path through ``resolve_within`` (INV-8, defense-in-depth vs the edge)."""
    allowlist = _input_allowlist()
    resolved: dict[str, str] = {}
    for key in _CONDITIONING_KEYS:
        value = record.params.get(key)
        if value:
            resolved[key] = resolve_within(str(value), allowlist)
    return resolved


def _param_record(record: Any) -> dict:
    """Pure-ish: the INV-P5-1 parameter record for job metadata, from the SAME source as the submitted
    request (``fd_resolved_params`` for forward_dynamics, ``resolved_params`` for the video/image modes),
    so the recorded metadata can never drift from what was actually sent.
    """
    rp = fd_resolved_params(record) if record.mode == "forward_dynamics" else resolved_params(record)
    return {key: rp[key] for key in _META_KEYS}


def _read_filepart(path: str) -> FilePart:
    """Action: read a trusted (already ``resolve_within``-checked) conditioning image into a multipart part.

    Enforces the same image byte cap as the inline edge (INV-5: conditioning media is probed and capped;
    a trusted path must not bypass it and read an unbounded file into the api process), and sanitizes the
    multipart filename (defense-in-depth vs CR/LF header injection).
    """
    cap = MediaLimits.from_env().max_image_bytes
    size = os.path.getsize(path)
    if size > cap:
        raise VideoJobError("payload_too_large", f"conditioning image is {size} bytes, exceeds the {cap}-byte cap")
    with open(path, "rb") as handle:
        data = handle.read()
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    filename = re.sub(r'[\r\n"\\]', "_", os.path.basename(path))
    return FilePart(filename=filename, content_type=content_type, data=data)


def _write_png(job_id: str, data: bytes) -> str:
    """Action: persist decoded image bytes as a PNG under the artifact volume (image ext/MIME).

    ``jobs/artifacts.py`` is outside the S6 blast radius, so the adapter uses the public
    ``artifact_path_for`` (sanitized + realpath-contained, INV-8) + a direct write, mirroring
    ``artifacts.write_video_bytes``. Guarantees a `.png` artifact (never a video container for t2i).
    """
    directory = artifacts.artifacts_dir()
    os.makedirs(directory, exist_ok=True)
    path = artifacts.artifact_path_for(job_id, directory=directory, ext="png")
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def vllm_omni_work(
    record: Any,
    report: Callable[[float], None],
    *,
    transport: VideoTransport | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
) -> WorkResult:
    """Action (the runner's real ``work`` for the vllm-omni plane): dispatch by mode → submit → persist.

    ``transport``/``base_url``/``timeout`` are keyword-only with production defaults, so the runner's
    2-arg ``work(record, report)`` call works unchanged while tests inject a fake transport. The base
    URL is the single deployed generation endpoint (``endpoint_for``) unless one is injected; the
    reported precision is the deployed checkpoint (INV-3), never a request-supplied value.
    """
    checkpoint = deployed_checkpoint()
    base_url = base_url or endpoint_for().base_url
    timeout = timeout if timeout is not None else float(os.environ.get("COSMOS3_GEN_TIMEOUT", DEFAULT_GEN_TIMEOUT))
    transport = transport or UrllibVideoTransport(base_url)

    try:
        conditioning = _resolve_conditioning(record)  # INV-8 first (security boundary, before any submit)
    except UntrustedPathError as exc:
        raise VideoJobError("untrusted_path", str(exc)) from exc

    if record.mode not in _SUPPORTED_MODES:
        raise VideoJobError("unsupported_mode", f"mode {record.mode!r} is not served by the vllm-omni adapter")

    if record.mode == "t2i":
        data = run_image_job(record, transport=transport, overall_timeout=timeout)
        path = _write_png(record.id, data)
    elif record.mode == "forward_dynamics":
        image_path = conditioning.get("image_path")
        if not image_path:  # FD needs a first-frame image; never submit without it
            raise VideoJobError("invalid_input", "forward_dynamics requires a conditioning first-frame image")
        data = run_forward_dynamics_job(
            record, report, transport=transport,
            input_reference=_read_filepart(image_path), overall_timeout=timeout,
        )
        path = artifacts.write_video_bytes(data, record.id)  # byte-passthrough rollout MP4 (INV-P5-3)
    else:  # async video: t2v / i2v / t2v_audio
        input_reference = None
        if record.mode == "i2v":
            image_path = conditioning.get("image_path")
            if not image_path:  # never submit a text-only t2v in place of an i2v (spec forbids a silent wrong artifact)
                raise VideoJobError("invalid_input", "i2v requires a conditioning image")
            input_reference = _read_filepart(image_path)
        data = run_video_job(
            record, report, transport=transport, input_reference=input_reference, overall_timeout=timeout,
        )
        path = artifacts.write_video_bytes(data, record.id)  # byte-passthrough (INV-P5-3, INV-8)

    report(1.0)  # terminal progress after the artifact is persisted
    meta = {"engine": "vllm_omni", "precision": checkpoint, **_param_record(record)}
    if conditioning:
        meta["conditioning"] = sorted(conditioning)
    return WorkResult(path, meta)
