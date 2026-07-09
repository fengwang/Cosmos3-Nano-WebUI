"""The versioned async job HTTP surface (Action shell; INV-5 / E4 / RK-09).

Thin routes over the job store + runner + orchestrator: submit (202 + id; idempotency), get, SSE
progress (heartbeat + Last-Event-ID replay, no proxy buffering), artifact fetch, cancel. The submit
route runs the modality/trust-boundary validators **before** enqueue (errors-as-data → the installed
handlers map them to 413/415/422/409). Media is carried inline as base64 or by a trusted-volume path
(the dep-free S6 ingress; multipart via the BFF is S7/S8). Refs: session_6/specs/api-surface-and-errors.md.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import mimetypes
import os
from typing import TYPE_CHECKING

from fastapi import APIRouter, Request, Response, status
from fastapi.responses import FileResponse, StreamingResponse

from app.schemas import Job, JobSubmit
from jobs import artifacts
from jobs.events import HEARTBEAT, JobEvent, events_since
from jobs.model import JobRecord
from jobs.runner import JobRunner
from jobs.store import JobStore
from orchestrator.planes import Plane
from preprocessing.action_schema import ActionMode, ActionSpec, ActionValidationFailed
from preprocessing.action_schema import validate as validate_action
from preprocessing.limits import MediaLimits
from preprocessing.media import (
    MediaErrorCode,
    MediaValidationError,
    MediaValidationFailed,
    probe_audio,
    probe_image,
    probe_video,
    validate_audio,
    validate_image,
    validate_dimension,
    validate_num_frames,
    validate_resolution,
    validate_video,
)
from preprocessing.paths import resolve_within

if TYPE_CHECKING:
    from app.observability.metrics import Metrics

GENERATION_MODES = frozenset({"t2i", "t2v", "i2v", "t2v_audio"})
ACTION_MODES = frozenset({"forward_dynamics", "inverse_dynamics", "policy"})

_TERMINAL_EVENT_TYPES = frozenset({"succeeded", "failed", "cancelled"})
_PROBE = {"image": (probe_image, validate_image), "video": (probe_video, validate_video),
          "audio": (probe_audio, validate_audio)}


def _heartbeat_seconds() -> float:
    return float(os.environ.get("COSMOS3_SSE_HEARTBEAT_SECONDS", "15"))


def _input_allowlist() -> tuple[str, ...]:
    raw = os.environ.get("COSMOS3_INPUT_ALLOWLIST")
    return tuple(raw.split(os.pathsep)) if raw else (artifacts.artifacts_dir(),)


def _fail_media(code: MediaErrorCode, message: str) -> MediaValidationFailed:
    return MediaValidationFailed(MediaValidationError(code, message))


def _require_int(params: dict, key: str) -> int:
    """Coerce a param to int, or raise a typed 422 (a non-numeric/null/list value is INVALID_PARAM)."""
    try:
        return int(params[key])
    except (TypeError, ValueError) as exc:
        raise _fail_media(MediaErrorCode.INVALID_PARAM, f"{key!r} must be an integer") from exc


def _int_or(params: dict, key: str, default: int) -> int:
    """Coerce an int param with a default (absent/null → default); a bad type is a typed 422."""
    if key not in params or params[key] is None:
        return default
    return _require_int(params, key)


def _opt_int(params: dict, key: str) -> int | None:
    """Coerce a genuinely-optional int param (absent/null → None); a bad type is a typed 422."""
    if key not in params or params[key] is None:
        return None
    return _require_int(params, key)


def _plane_for_mode(mode: str) -> Plane:
    if mode in GENERATION_MODES or mode in ACTION_MODES:
        return Plane.GENERATION  # all S6 job modes run on the generation plane (reasoning is sync — S7)
    raise _fail_media(MediaErrorCode.INVALID_PARAM, f"unknown job mode {mode!r}")


def _validate_output_params(params: dict, limits: MediaLimits) -> None:
    if "resolution" in params:
        error = validate_resolution(_require_int(params, "resolution"), limits)
        if error is not None:
            raise MediaValidationFailed(error)
    for key in ("height", "width"):
        if key in params:
            error = validate_dimension(_require_int(params, key), limits)
            if error is not None:
                raise MediaValidationFailed(error)
    if "num_frames" in params:
        error = validate_num_frames(_require_int(params, "num_frames"), limits)
        if error is not None:
            raise MediaValidationFailed(error)


def _validate_action_params(mode: str, params: dict, has_inline_image: bool, has_inline_video: bool) -> None:
    spec = ActionSpec(
        mode=ActionMode(mode),
        domain_name=str(params.get("domain_name", "")),
        chunk_size=_int_or(params, "chunk_size", 0),
        raw_action_width=_opt_int(params, "raw_action_width"),
        resolution_tier=_int_or(params, "resolution_tier", 480),
        has_image=bool(params.get("image_path")) or has_inline_image,
        has_video=bool(params.get("video_path")) or has_inline_video,
    )
    error = validate_action(spec)
    if error is not None:
        raise ActionValidationFailed(error)


def _validate_inline_media(media, limits: MediaLimits) -> None:
    if media.kind not in _PROBE:
        raise _fail_media(MediaErrorCode.UNSUPPORTED_MEDIA_TYPE, f"unknown media kind {media.kind!r}")
    cap = {"image": limits.max_image_bytes, "video": limits.max_video_bytes, "audio": limits.max_audio_bytes}
    if len(media.data_base64) > cap[media.kind] * 2:  # reject before decoding a decode-bomb (RK-11)
        raise _fail_media(MediaErrorCode.PAYLOAD_TOO_LARGE, f"{media.kind} payload exceeds the byte cap")
    try:
        raw = base64.b64decode(media.data_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise _fail_media(MediaErrorCode.INVALID_PARAM, f"invalid base64 media: {exc}") from exc
    probe, validate = _PROBE[media.kind]
    error = validate(probe(raw), limits)
    if error is not None:
        raise MediaValidationFailed(error)


def _validate_conditioning_paths(params: dict, allowlist: tuple[str, ...]) -> None:
    for key in ("image_path", "video_path", "audio_path"):
        value = params.get(key)
        if value:
            resolve_within(str(value), allowlist)  # raises UntrustedPathError (→ 422) on escape / URL


def validate_submission(submit: JobSubmit, *, limits: MediaLimits, allowlist: tuple[str, ...]) -> Plane:
    """Validate a submission against every edge rule; raise a typed error (→ handlers) or return the plane."""
    plane = _plane_for_mode(submit.mode)
    _validate_conditioning_paths(submit.params, allowlist)  # INV-8/EC-S6 containment before anything else
    if submit.media is not None:
        _validate_inline_media(submit.media, limits)
    _validate_output_params(submit.params, limits)
    if submit.mode in ACTION_MODES:
        _validate_action_params(
            submit.mode, submit.params,
            has_inline_image=submit.media is not None and submit.media.kind == "image",
            has_inline_video=submit.media is not None and submit.media.kind == "video",
        )
    return plane


def _to_job(rec: JobRecord) -> Job:
    meta = rec.result_meta or {}
    return Job(
        id=rec.id, status=rec.status, mode=rec.mode, created_at=rec.created_at, progress=rec.progress,
        artifact_url=f"/v1/jobs/{rec.id}/artifact" if rec.artifact_path else None, error=rec.error,
        precision=meta.get("precision"),  # the served checkpoint precision the worker reported (S7)
        trajectory_url=f"/v1/jobs/{rec.id}/trajectory" if meta.get("trajectory_path") else None,
    )


def _sse(event: JobEvent) -> str:
    return f"id: {event.id}\nevent: {event.type}\ndata: {json.dumps(event.data)}\n\n"


def _persist_inline_media(media, params: dict) -> dict:
    """Write inline base64 conditioning media to a contained trusted file; inject its path into params.

    Closes the inline channel (design D-5 / INV-8): the worker opens a realpath-contained file under the
    artifact volume, never raw request bytes. The name is content-addressed + sanitized, so identical
    media replays the same path (idempotency-stable). Returns a new params dict (no mutation of input).
    """
    raw = base64.b64decode(media.data_base64, validate=True)  # already validated in validate_submission
    ext = {"image": "png", "video": "mp4", "audio": "wav"}.get(media.kind, "bin")
    directory = artifacts.artifacts_dir()
    os.makedirs(directory, exist_ok=True)
    path = artifacts.artifact_path_for(
        f"cond_{hashlib.sha256(raw).hexdigest()[:16]}", directory=directory, ext=ext
    )
    with open(path, "wb") as handle:
        handle.write(raw)
    return {**params, f"{media.kind}_path": path}


async def submit_and_enqueue(
    submit: JobSubmit, store: JobStore, runner: JobRunner, *, idempotency_key: str | None = None,
    metrics: Metrics | None = None,
) -> Job:
    """Validate → store (idempotency-aware) → enqueue → the Job view. Shared by ``/v1/jobs`` and the S7
    capability routes, so every submission path runs the SAME edge validation (INV-6) and one runner.
    Inline media is persisted to a trusted path so the worker consumes it (never silently dropped — D-5).
    Typed validation errors propagate to the installed handlers (413/415/422/409)."""
    plane = validate_submission(submit, limits=MediaLimits.from_env(), allowlist=_input_allowlist())
    params = _persist_inline_media(submit.media, submit.params) if submit.media is not None else submit.params
    record, replayed = store.submit(submit.mode, plane, params, key=idempotency_key)
    if not replayed:
        if metrics is not None:
            metrics.job_submitted.labels(submit.mode).inc()  # count new submissions by mode (never replays)
        await runner.submit(record)
    return _to_job(record)


def build_jobs_router(store: JobStore, runner: JobRunner, metrics: Metrics | None = None) -> APIRouter:
    """Build the ``/v1/jobs`` router bound to the injected store + runner."""
    router = APIRouter(prefix="/v1/jobs", tags=["jobs"])

    @router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=Job)
    async def submit_job(submit: JobSubmit, request: Request) -> Job:
        return await submit_and_enqueue(
            submit, store, runner, idempotency_key=request.headers.get("idempotency-key"), metrics=metrics
        )

    @router.get("/{job_id}", response_model=Job)
    def get_job(job_id: str) -> Job:
        return _to_job(store.get(job_id))  # JobNotFound → 404

    @router.get("/{job_id}/events")
    def stream_events(job_id: str, request: Request) -> StreamingResponse:
        store.get(job_id)  # 404 if unknown, before opening the stream
        raw = request.headers.get("last-event-id")
        last_event_id = int(raw) if raw and raw.isdigit() else None

        async def gen():
            import asyncio  # noqa: PLC0415 — local to the streaming coroutine

            sent = last_event_id or 0
            done = False
            while not done:
                for event in events_since(store.log(job_id), sent):
                    sent = event.id
                    yield _sse(event)
                    if event.type in _TERMINAL_EVENT_TYPES:
                        done = True
                record = store.try_get(job_id)
                # Stop on: terminal event just sent, job gone, OR already-terminal record with nothing
                # left to replay (a reconnect whose Last-Event-ID is at/after the terminal id — else the
                # heartbeat loop would never exit). A still-running job continues with heartbeats.
                if done or record is None or record.status.value in _TERMINAL_EVENT_TYPES:
                    break
                yield _sse(JobEvent(id=sent, type=HEARTBEAT))  # keep-alive; id is the last real event
                await asyncio.sleep(_heartbeat_seconds())

        return StreamingResponse(
            gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
        )

    @router.get("/{job_id}/artifact")
    def get_artifact(job_id: str) -> FileResponse:
        record = store.get(job_id)  # 404 if unknown
        if record.artifact_path and os.path.exists(record.artifact_path):
            media_type = mimetypes.guess_type(record.artifact_path)[0] or "application/octet-stream"
            return FileResponse(record.artifact_path, media_type=media_type)
        return Response(  # type: ignore[return-value] — 404 body via the error contract
            content=json.dumps({"code": "not_found", "message": "artifact not available"}),
            status_code=status.HTTP_404_NOT_FOUND, media_type="application/json",
        )

    @router.get("/{job_id}/trajectory")
    def get_trajectory(job_id: str) -> FileResponse:
        record = store.get(job_id)  # 404 if unknown
        traj = (record.result_meta or {}).get("trajectory_path")  # FD/policy sidecar (ID's is the artifact)
        if traj and os.path.exists(traj):
            return FileResponse(traj, media_type="application/json")
        return Response(  # type: ignore[return-value] — 404 body via the error contract
            content=json.dumps({"code": "not_found", "message": "trajectory not available"}),
            status_code=status.HTTP_404_NOT_FOUND, media_type="application/json",
        )

    @router.post("/{job_id}/cancel", response_model=Job)
    async def cancel_job(job_id: str) -> Job:
        return _to_job(await runner.cancel(job_id))  # JobNotFound→404; terminal→JobTransitionError→409

    return router
