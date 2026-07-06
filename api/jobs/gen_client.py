"""The generation-plane IPC client + wire framing (Action shell + pure Calculations; torch-free).

The runner's real ``work`` (S7): connect to the resident ``gen_worker``'s Unix-domain socket,
send one length-prefixed JSON request, await the reply, and return a ``WorkResult``. Because the
generation runs **inside** the resident worker process group, ``os.killpg`` eviction stops in-flight
work (INV-4) and no second model is ever loaded in the api process. The wire framing (``frame`` /
``unframe``) is a pure, host-testable Calculation; only ``work`` touches the socket.

Refs: session_7/specs/generation-plane-inference-channel.md; design.md D-1.
"""
from __future__ import annotations

import json
import os
import socket
import struct
from collections.abc import Callable

from jobs.artifacts import artifacts_dir
from jobs.model import JobRecord
from jobs.runner import WorkResult
from preprocessing.paths import resolve_within

# 64 MiB ceiling: requests carry small JSON (prompt + params + inline raw_actions); media + latents
# cross via trusted-volume *paths*, never inline — so a frame this large signals corruption, not data.
_MAX_FRAME = 64 * 1024 * 1024

DEFAULT_GEN_SOCK = "/tmp/cosmos3_gen.sock"
ACTION_MODES = frozenset({"forward_dynamics", "inverse_dynamics", "policy"})


class FramingError(Exception):
    """A malformed / oversize / truncated IPC frame (never hang, never silently truncate)."""


def frame(obj: dict) -> bytes:
    """Pure: encode ``obj`` as a 4-byte big-endian length prefix + a UTF-8 JSON body."""
    body = json.dumps(obj).encode("utf-8")
    return struct.pack(">I", len(body)) + body


def _read_exact(read: Callable[[int], bytes], n: int) -> bytes:
    """Action-agnostic: pull exactly ``n`` bytes from ``read`` (a socket recv / buffer read), or raise.

    A ``read`` that returns ``b""`` means the peer closed mid-frame → ``FramingError`` (never an
    infinite loop, never a short read masquerading as a complete body).
    """
    chunks: list[bytes] = []
    remaining = n
    while remaining > 0:
        chunk = read(remaining)
        if not chunk:
            raise FramingError(f"stream closed with {remaining} of {n} bytes unread")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def unframe(read: Callable[[int], bytes]) -> dict:
    """Pure (over an injected reader): decode one framed JSON message; raise ``FramingError`` on a bad frame."""
    (length,) = struct.unpack(">I", _read_exact(read, 4))
    if length > _MAX_FRAME:
        raise FramingError(f"frame too large: {length} > {_MAX_FRAME}")
    return json.loads(_read_exact(read, length).decode("utf-8"))


def read_reply(read: Callable[[int], bytes], report: Callable[[float], None]) -> dict:
    """Pure Calculation: read progress + result frames from the worker; relay progress to ``report``.

    The worker sends N ``{type: "progress", step, total}`` frames (``step`` is 1-based) followed by
    one ``{type: "result", ...}`` frame.  A message with no ``type`` field is treated as a legacy
    result (backward-compatible with old workers).
    """
    while True:
        msg = unframe(read)
        if msg.get("type") == "progress":
            step, total = msg["step"], msg["total"]
            if total > 0:
                report(step / total)
            continue
        return msg


class GenWorkerError(Exception):
    """A typed worker-side failure: carries the reply ``code`` so the job fails with it (not a bare 500)."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _input_allowlist() -> tuple[str, ...]:
    """Action: the trusted conditioning-path allowlist (env, default the artifact volume) — mirrors the edge."""
    raw = os.environ.get("COSMOS3_INPUT_ALLOWLIST")
    return tuple(raw.split(os.pathsep)) if raw else (artifacts_dir(),)


def build_request(record: JobRecord, *, allowlist: tuple[str, ...], want_latents: bool = False) -> dict:
    """Pure: reduce a JobRecord to the worker request — map mode→kind, resolve conditioning paths (INV-8).

    Conditioning paths are re-resolved through ``resolve_within`` so only a contained, canonical path
    reaches the worker (closes the RK-11 carry: the worker opens the *resolved* path, never raw input).
    """
    params = dict(record.params)
    request = {
        "job_id": record.id,
        "kind": "action" if record.mode in ACTION_MODES else "generation",
        "mode": record.mode,
        "params": params,
        "checkpoint": params.get("checkpoint", "nvfp4"),
        "want_latents": bool(want_latents),
    }
    for key in ("image_path", "video_path", "audio_path"):
        value = params.get(key)
        if value:
            request[key] = resolve_within(str(value), allowlist)
    return request


def work(record: JobRecord, report: Callable[[float], None]) -> WorkResult:
    """Action (the runner's real ``work``): IPC to the resident ``gen_worker``; return its ``WorkResult``.

    A ``{ok:false}`` reply raises ``GenWorkerError`` (the job fails with its ``code``); a connect/timeout
    failure raises (→ ``internal_error`` via the runner). The generation runs INSIDE the resident worker
    process group, so ``os.killpg`` eviction stops it and no second model loads in the api process (INV-4).
    """
    sock_path = os.environ.get("COSMOS3_GEN_SOCK", DEFAULT_GEN_SOCK)
    timeout = float(os.environ.get("COSMOS3_GEN_TIMEOUT", "2400"))
    request = build_request(
        record, allowlist=_input_allowlist(), want_latents=os.environ.get("COSMOS3_WANT_LATENTS") == "1"
    )
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(sock_path)
        sock.sendall(frame(request))
        report(0.0)
        reply = read_reply(sock.recv, report)
    report(1.0)
    if not reply.get("ok"):
        raise GenWorkerError(reply.get("code", "internal_error"), reply.get("message", "worker error"))
    return WorkResult(reply["artifact_path"], reply.get("meta", {}))
