"""vllm-omni client — async video, synchronous action, and images (Action shell + pure Calculations).

Three flows, all torch-free and host-testable via an injected ``VideoTransport`` port:
- **async video** (t2v/i2v/t2v_audio): `POST /v1/videos` (multipart) -> poll `GET /v1/videos/{id}` ->
  download `GET /v1/videos/{id}/content`; DELETE on client timeout (R-14). i2v adds an `input_reference`
  multipart file part.
- **synchronous action** (forward_dynamics): `POST /v1/videos/sync` (multipart, first-frame
  `input_reference` + action `extra_params`) -> the rollout MP4 bytes directly (GATE-S5-ACTION).
- **images** (t2i): `POST /v1/images/generations` (JSON, `response_format=b64_json`) -> decode the
  base64 image bytes.

The production transport is stdlib ``urllib`` (no new production dependency, INV-3). Form/body building
is pure so the submitted request and the recorded metadata never desync. Refs:
session_6/specs/vllm-omni-generation-adapter.md; session_5/outputs/action_mapping.md; design.md D-2/D-3.
"""
from __future__ import annotations

import base64
import binascii
import contextlib
import json
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from engines.base import default_dimensions  # torch-free shared mode-aware resolution default

# Terminal statuses (fork `VideoGenerationStatus`); `queued`/`in_progress` are pending.
_COMPLETED = "completed"
_FAILED = "failed"

# Progress-ramp denominator when the server reports no `progress` field (fallback only).
# Conservative upper bound on the measured flagship duration (720p x189 ~ 617-628 s, S1/S3).
_DEFAULT_EXPECTED_SECONDS = 650.0

# Cap the reported fraction below 1.0 while polling — the terminal 1.0 is the caller's
# to emit after the artifact is persisted (a premature 100% would misreport the job).
_POLL_PROGRESS_CAP = 0.95


@dataclass(frozen=True)
class FilePart:
    """A multipart file field (inert Data): the conditioning image for i2v / the first frame for FD."""

    filename: str
    content_type: str
    data: bytes


class VideoTransport(Protocol):
    """The minimal HTTP surface the client needs (real impl: `UrllibVideoTransport`; tests fake it)."""

    def post_form(self, path: str, form: dict) -> dict: ...
    def get_json(self, path: str) -> tuple[int, dict]: ...
    def get_bytes(self, path: str) -> bytes: ...
    def delete(self, path: str) -> None: ...
    def post_form_bytes(self, path: str, form: dict, *, timeout: float) -> bytes: ...  # sync video (FD)
    def post_json(self, path: str, obj: dict, *, timeout: float) -> dict: ...          # images API (t2i)


class VideoJobError(Exception):
    """A typed vllm-omni failure carrying a ``code`` so the runner fails the job with it."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def resolved_params(record: Any) -> dict:
    """Pure: the gated generation params with pinned defaults (INV-P5-1) — the SINGLE source used
    both to build the request form and to record job metadata, so the two can never desync.

    Reads only ``record.params`` (no env, no clock). Guardrails-off + fps 24 match the S1/S3 diag
    harness / protocol DEFAULT_FPS (INV-P5-3).
    """
    p = dict(getattr(record, "params", {}) or {})
    p_res = p.get("resolution")
    # Mode-aware default (UX-S2): video omitting dims -> 1280x720, t2i -> 480; explicit dims/resolution win.
    dw, dh = default_dimensions(str(getattr(record, "mode", "") or ""), int(p_res) if p_res is not None else None)
    return {
        "prompt": str(p.get("prompt", "") or ""),
        "negative_prompt": str(p["negative_prompt"]) if p.get("negative_prompt") else None,
        "width": int(p.get("width", dw)),
        "height": int(p.get("height", dh)),
        "num_frames": int(p.get("num_frames", 1)),
        "num_inference_steps": int(p.get("num_inference_steps", 35)),
        "guidance_scale": float(p.get("guidance_scale", 6.0)),
        "flow_shift": float(p.get("flow_shift", 10.0)),
        "seed": int(p.get("seed", 123)),
        "fps": int(p.get("fps", 24)),
        "max_sequence_length": int(p.get("max_sequence_length", 4096)),
        "generate_sound": bool(p.get("generate_sound")),
    }


def build_video_form(record: Any, *, input_reference: FilePart | None = None) -> dict:
    """Pure: a job's params -> the multipart form fields for the async video API (INV-P5-1).

    Derived from ``resolved_params`` (the shared source). ``input_reference`` (i2v conditioning image)
    is added as a multipart file part when present.
    """
    rp = resolved_params(record)
    form: dict[str, Any] = {
        "prompt": rp["prompt"],
        "size": f'{rp["width"]}x{rp["height"]}',
        "num_frames": str(rp["num_frames"]),
        "fps": str(rp["fps"]),
        "num_inference_steps": str(rp["num_inference_steps"]),
        "guidance_scale": str(rp["guidance_scale"]),
        "flow_shift": str(rp["flow_shift"]),
        "seed": str(rp["seed"]),
        "max_sequence_length": str(rp["max_sequence_length"]),
        "extra_params": json.dumps(
            {"use_resolution_template": False, "use_duration_template": False, "guardrails": False}
        ),
    }
    if rp["negative_prompt"]:
        form["negative_prompt"] = rp["negative_prompt"]
    if rp["generate_sound"]:
        form["generate_sound"] = "true"
    if input_reference is not None:
        form["input_reference"] = input_reference  # i2v conditioning (multipart file part)
    return form


def build_image_body(record: Any) -> dict:
    """Pure: a t2i job's params -> the `/v1/images/generations` JSON body (S5 run_t2i shape)."""
    rp = resolved_params(record)
    body: dict[str, Any] = {
        "prompt": rp["prompt"],
        "size": f'{rp["width"]}x{rp["height"]}',
        "n": 1,
        "response_format": "b64_json",
        "num_inference_steps": rp["num_inference_steps"],
        "guidance_scale": rp["guidance_scale"],
        "seed": rp["seed"],
    }
    if rp["negative_prompt"]:
        body["negative_prompt"] = rp["negative_prompt"]
    return body


def action_extra_params(params: dict, mode: str) -> dict:
    """Pure: the forward_dynamics ``extra_params`` from action params (session_5/action_mapping.md)."""
    return {
        "action_mode": mode,
        "domain_name": params.get("domain_name"),
        "raw_action_dim": params.get("raw_action_width"),
        "action_chunk_size": params.get("chunk_size"),
        "action": params.get("raw_actions"),
    }


def fd_resolved_params(record: Any) -> dict:
    """Pure: the resolved forward_dynamics params — the SINGLE source for ``build_fd_form`` + the job meta,
    so the submitted request and the recorded metadata never desync (as ``resolved_params`` is for video).

    FD recipe defaults (fps 10, steps 30, guidance 1.0, flow_shift 5.0; num_frames = chunk+1; landscape
    4:3 from the resolution tier — tier 480 -> 640x480, the S5-proven size), each overridable via params.
    """
    p = dict(getattr(record, "params", {}) or {})
    tier = int(p.get("resolution_tier", 480))
    width = round(tier * 4 / 3)
    width -= width % 2  # even dimension
    chunk = int(p.get("chunk_size", 0))
    return {
        "prompt": str(p.get("prompt", "") or ""),
        "width": width,
        "height": tier,
        "num_frames": int(p.get("num_frames", chunk + 1)),
        "fps": int(p.get("fps", 10)),
        "num_inference_steps": int(p.get("num_inference_steps", 30)),
        "guidance_scale": float(p.get("guidance_scale", 1.0)),
        "flow_shift": float(p.get("flow_shift", 5.0)),
        "seed": int(p.get("seed", 123)),
        "extra_params": action_extra_params(p, record.mode),
    }


def build_fd_form(record: Any, *, input_reference: FilePart) -> dict:
    """Pure: a forward_dynamics job -> the `/v1/videos/sync` multipart form (S5-proven FD mapping).

    The first-frame ``input_reference`` and the action ``extra_params`` are attached.
    """
    fp = fd_resolved_params(record)
    return {
        "prompt": fp["prompt"],
        "size": f'{fp["width"]}x{fp["height"]}',
        "num_frames": str(fp["num_frames"]),
        "fps": str(fp["fps"]),
        "num_inference_steps": str(fp["num_inference_steps"]),
        "guidance_scale": str(fp["guidance_scale"]),
        "flow_shift": str(fp["flow_shift"]),
        "seed": str(fp["seed"]),
        "extra_params": json.dumps(fp["extra_params"]),
        "input_reference": input_reference,
    }


def parse_status(js: dict) -> tuple[str, float | None]:
    """Pure: status JSON -> (state in {completed, failed, pending}, progress-fraction | None)."""
    status = str(js.get("status", "")).lower()
    prog = js.get("progress")
    fraction = max(0.0, min(1.0, float(prog) / 100.0)) if isinstance(prog, (int, float)) else None
    if status == _COMPLETED:
        return "completed", fraction
    if status == _FAILED:
        return "failed", fraction
    return "pending", fraction


def _progress_fraction(server_fraction: float | None, elapsed: float, expected: float) -> float:
    """Pure: prefer the server fraction; else a bounded elapsed ramp. Never returns >= 1.0."""
    if server_fraction is not None:
        return min(_POLL_PROGRESS_CAP, max(0.0, server_fraction))
    if expected <= 0:
        return 0.0
    return min(_POLL_PROGRESS_CAP, max(0.0, elapsed / expected))


def _safe_report(report: Callable[[float], None], fraction: float) -> None:
    """Action-agnostic: relay progress, swallowing any sink error (FR-5 non-gating, fail-open)."""
    with contextlib.suppress(Exception):
        report(fraction)


def encode_multipart(form: dict, *, boundary: str | None = None) -> tuple[str, bytes]:
    """Pure: encode a ``str -> str | FilePart`` form as multipart/form-data. Returns (content_type, body).

    A ``FilePart`` value emits a file part (Content-Disposition filename + Content-Type + raw bytes);
    any other value is a text field. ``boundary`` is injectable for deterministic tests.
    """
    boundary = boundary or ("----cosmos3omni" + uuid.uuid4().hex)
    parts: list[bytes] = []
    for key, value in form.items():
        if isinstance(value, FilePart):
            parts += [
                f"--{boundary}".encode(),
                f'Content-Disposition: form-data; name="{key}"; filename="{value.filename}"'.encode(),
                f"Content-Type: {value.content_type}".encode(),
                b"",
                value.data,
            ]
        else:
            parts += [
                f"--{boundary}".encode(),
                f'Content-Disposition: form-data; name="{key}"'.encode(),
                b"",
                str(value).encode("utf-8"),
            ]
    parts += [f"--{boundary}--".encode(), b""]
    return f"multipart/form-data; boundary={boundary}", b"\r\n".join(parts)


def run_video_job(
    record: Any,
    report: Callable[[float], None],
    *,
    transport: VideoTransport,
    input_reference: FilePart | None = None,
    base_path: str = "/v1/videos",
    poll_interval: float = 5.0,
    overall_timeout: float = 7200.0,
    expected_seconds: float | None = None,
    now: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> bytes:
    """Action: submit -> poll to completion -> download bytes; DELETE + raise on client-timeout.

    ``now``/``sleep`` are injected so the timeout path is deterministic in tests. Progress is
    relayed best-effort (fail-open); the terminal 1.0 is left to the caller (after the artifact
    is written). Any failed/non-200 poll raises a typed ``VideoJobError``.
    """
    submitted = transport.post_form(base_path, build_video_form(record, input_reference=input_reference))
    video_id = submitted.get("id")
    if not video_id:
        raise VideoJobError("internal_error", f"submit response carried no job id: {submitted!r}")
    _safe_report(report, 0.0)

    expected = expected_seconds if expected_seconds is not None else _DEFAULT_EXPECTED_SECONDS
    start = now()
    reported = 0.0  # monotonic floor: a server that reports `progress` intermittently must not regress the bar
    while True:
        if now() - start > overall_timeout:
            with contextlib.suppress(Exception):
                transport.delete(f"{base_path}/{video_id}")  # orphan prevention (R-14)
            raise VideoJobError("timeout", f"video job {video_id} exceeded {overall_timeout:.0f}s")
        code, body = transport.get_json(f"{base_path}/{video_id}")
        if code != 200:  # retrieve_video returns non-200 JSON when the job has FAILED
            raise VideoJobError("generation_failed", f"job {video_id} poll returned HTTP {code}: {body!r}")
        state, server_fraction = parse_status(body)
        if state == "failed":
            raise VideoJobError("generation_failed", str(body.get("error") or f"job {video_id} failed"))
        if state == "completed":
            break
        reported = max(reported, _progress_fraction(server_fraction, now() - start, expected))
        _safe_report(report, reported)
        sleep(poll_interval)
    return transport.get_bytes(f"{base_path}/{video_id}/content")


def run_forward_dynamics_job(
    record: Any,
    report: Callable[[float], None],
    *,
    transport: VideoTransport,
    input_reference: FilePart,
    overall_timeout: float = 7200.0,
) -> bytes:
    """Action: synchronous forward_dynamics — `POST /v1/videos/sync` returns the rollout MP4 bytes.

    Sync gives no intermediate progress; FD is short (~4.5 s, S5). The terminal 1.0 is the caller's.
    """
    _safe_report(report, 0.0)
    form = build_fd_form(record, input_reference=input_reference)
    return transport.post_form_bytes("/v1/videos/sync", form, timeout=overall_timeout)


def run_image_job(record: Any, *, transport: VideoTransport, overall_timeout: float = 7200.0) -> bytes:
    """Action: t2i — `POST /v1/images/generations` (JSON) -> decode `data[0].b64_json` -> image bytes."""
    doc = transport.post_json("/v1/images/generations", build_image_body(record), timeout=overall_timeout)
    try:
        b64 = doc["data"][0]["b64_json"]
    except (KeyError, IndexError, TypeError) as exc:
        raise VideoJobError("generation_failed", f"images response missing b64_json: {doc!r}") from exc
    try:
        return base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise VideoJobError("generation_failed", f"images response b64 undecodable: {exc}") from exc


class UrllibVideoTransport:
    """Production transport over stdlib ``urllib`` (no new production dependency, INV-3).

    Every call is bounded by a per-request timeout so the poll loop can never hang; the overall
    job deadline is enforced by ``run_video_job``. The base URL comes only from operator config.
    """

    def __init__(self, base_url: str, *, request_timeout: float = 30.0, content_timeout: float = 120.0) -> None:
        # Per-call timeouts are kept tight so a poll thread orphaned by a cancel/kill (the runner runs
        # work in a non-cancellable to_thread that holds the gpu_lease) unwinds promptly rather than
        # stalling the GPU for the full call budget. The overall job budget lives in run_video_job.
        self._base = base_url.rstrip("/")
        self._request_timeout = request_timeout
        self._content_timeout = content_timeout

    def post_form(self, path: str, form: dict) -> dict:
        import urllib.request  # noqa: PLC0415 — stdlib, deferred to keep import cost trivial

        content_type, body = encode_multipart(form)
        req = urllib.request.Request(  # noqa: S310 — fixed operator-config base URL, not request-derived
            self._base + path, data=body, method="POST", headers={"Content-Type": content_type}
        )
        with urllib.request.urlopen(req, timeout=self._request_timeout) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))

    def get_json(self, path: str) -> tuple[int, dict]:
        import urllib.error  # noqa: PLC0415
        import urllib.request  # noqa: PLC0415

        try:
            with urllib.request.urlopen(self._base + path, timeout=self._request_timeout) as resp:  # noqa: S310
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # non-2xx: surface the code + body to the poll loop
            body: dict = {}
            with contextlib.closing(exc):  # exc holds an open socket; close it (no handle leak)
                with contextlib.suppress(Exception):
                    body = json.loads(exc.read().decode("utf-8"))
            return exc.code, body

    def get_bytes(self, path: str) -> bytes:
        import urllib.request  # noqa: PLC0415

        with urllib.request.urlopen(self._base + path, timeout=self._content_timeout) as resp:  # noqa: S310
            return resp.read()

    def delete(self, path: str) -> None:
        import urllib.request  # noqa: PLC0415

        req = urllib.request.Request(self._base + path, method="DELETE")  # noqa: S310
        with urllib.request.urlopen(req, timeout=self._request_timeout):  # noqa: S310
            return None

    @staticmethod
    def _http_error(path: str, exc) -> VideoJobError:  # exc: urllib.error.HTTPError
        """Map a non-2xx from a synchronous endpoint to a typed ``generation_failed`` (mirrors get_json)."""
        detail = ""
        with contextlib.closing(exc), contextlib.suppress(Exception):  # exc holds an open socket
            detail = exc.read().decode("utf-8")[:300]
        return VideoJobError("generation_failed", f"POST {path} -> HTTP {exc.code}: {detail}")

    def post_form_bytes(self, path: str, form: dict, *, timeout: float) -> bytes:
        """Synchronous multipart POST returning the raw response bytes (the FD rollout MP4)."""
        import urllib.error  # noqa: PLC0415
        import urllib.request  # noqa: PLC0415

        content_type, body = encode_multipart(form)
        req = urllib.request.Request(  # noqa: S310 — fixed operator-config base URL
            self._base + path, data=body, method="POST", headers={"Content-Type": content_type}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — sync gen may run long
                return resp.read()
        except urllib.error.HTTPError as exc:  # non-2xx → typed generation_failed (not a bare internal_error)
            raise self._http_error(path, exc) from exc

    def post_json(self, path: str, obj: dict, *, timeout: float) -> dict:
        """JSON POST returning the parsed JSON response (the images API)."""
        import urllib.error  # noqa: PLC0415
        import urllib.request  # noqa: PLC0415

        body = json.dumps(obj).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310 — fixed operator-config base URL
            self._base + path, data=body, method="POST", headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — sync gen may run long
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # non-2xx → typed generation_failed
            raise self._http_error(path, exc) from exc
