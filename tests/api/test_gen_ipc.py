"""IPC framing + gen_client work contract (host; torch-free).

Spec: session_7/specs/generation-plane-inference-channel.md — the length-prefixed
JSON protocol round-trips, and a truncated/oversize frame raises a typed FramingError
(never hangs, never silently truncates).
"""
from __future__ import annotations

import io
import os
import socket
import struct
import threading
import time

import pytest

from app.schemas import JobStatus
from jobs.gen_client import FramingError, build_request, frame, read_reply, unframe, work
from jobs.model import JobRecord
from jobs.runner import WorkResult
from orchestrator.planes import Plane


def _reader(data: bytes):
    """A read(n) callable over a fixed byte buffer (stands in for socket recv)."""
    return io.BytesIO(data).read


def _record(mode: str, params: dict) -> JobRecord:
    return JobRecord(
        id="j1", mode=mode, plane=Plane.GENERATION, status=JobStatus.queued, created_at="t0", params=params
    )


def _serve_one(sock_path: str, reply: dict | None) -> threading.Thread:
    """Bind+listen a one-shot UDS server (synchronously), then accept+reply on a daemon thread.

    ``reply=None`` accepts but never replies (to exercise the client timeout). Listening before we
    return guarantees the client's connect succeeds without a race.
    """
    if os.path.exists(sock_path):
        os.unlink(sock_path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(sock_path)
    srv.listen(1)

    def handle() -> None:
        try:
            conn, _ = srv.accept()
            try:
                unframe(conn.recv)  # drain the request
                if reply is not None:
                    conn.sendall(frame(reply))
                else:
                    time.sleep(2)  # hold without replying → the client times out
            finally:
                conn.close()
        finally:
            srv.close()

    thread = threading.Thread(target=handle, daemon=True)
    thread.start()
    return thread


def test_frame_unframe_roundtrip():
    obj = {"kind": "generation", "mode": "t2v", "params": {"prompt": "a robotic arm", "num_frames": 8}}
    assert unframe(_reader(frame(obj))) == obj


def test_unframe_truncated_body_raises():
    data = frame({"mode": "t2i"})
    with pytest.raises(FramingError):
        unframe(_reader(data[:-2]))  # body short by 2 bytes → closed stream mid-body


def test_unframe_truncated_header_raises():
    with pytest.raises(FramingError):
        unframe(_reader(b"\x00\x01"))  # only 2 of the 4 length bytes


def test_unframe_oversize_frame_raises():
    from jobs.gen_client import _MAX_FRAME

    header = struct.pack(">I", _MAX_FRAME + 1)
    with pytest.raises(FramingError):
        unframe(_reader(header + b"x"))


def test_build_request_maps_kind_and_resolves_conditioning_path(tmp_path):
    cond = tmp_path / "c.png"
    cond.write_bytes(b"\x89PNG")
    rec = _record("forward_dynamics", {"domain_name": "agibotworld", "image_path": str(cond)})
    req = build_request(rec, allowlist=(str(tmp_path),))
    assert req["kind"] == "action" and req["mode"] == "forward_dynamics" and req["job_id"] == "j1"
    assert req["image_path"] == os.path.realpath(str(cond))  # resolved trusted path (INV-8)
    assert req["checkpoint"] == "nvfp4"  # default surfaced
    assert build_request(_record("t2v", {}), allowlist=(str(tmp_path),))["kind"] == "generation"


def _progress_buf(*messages: dict) -> bytes:
    """Build a byte buffer from a sequence of framed JSON messages."""
    return b"".join(frame(m) for m in messages)


def test_read_reply_streams_progress():
    msgs = _progress_buf(
        {"type": "progress", "step": 1, "total": 3},
        {"type": "progress", "step": 2, "total": 3},
        {"type": "progress", "step": 3, "total": 3},
        {"type": "result", "ok": True, "artifact_path": "/a.mp4", "meta": {}},
    )
    reported: list[float] = []
    result = read_reply(_reader(msgs), reported.append)
    assert result["ok"] is True and result["artifact_path"] == "/a.mp4"
    assert reported == pytest.approx([1 / 3, 2 / 3, 1.0])


def test_read_reply_legacy_no_type_field():
    msgs = _progress_buf({"ok": True, "artifact_path": "/a.mp4", "meta": {}})
    reported: list[float] = []
    result = read_reply(_reader(msgs), reported.append)
    assert result["ok"] is True
    assert reported == []


def test_read_reply_zero_total_no_crash():
    msgs = _progress_buf(
        {"type": "progress", "step": 0, "total": 0},
        {"type": "result", "ok": True, "artifact_path": "/a.mp4", "meta": {}},
    )
    reported: list[float] = []
    result = read_reply(_reader(msgs), reported.append)
    assert result["ok"] is True
    assert reported == []


def test_read_reply_single_step():
    """Adversarial case 3: num_inference_steps=1 — one progress tick before result."""
    msgs = _progress_buf(
        {"type": "progress", "step": 1, "total": 1},
        {"type": "result", "ok": True, "artifact_path": "/a.mp4", "meta": {}},
    )
    reported: list[float] = []
    result = read_reply(_reader(msgs), reported.append)
    assert result["ok"] is True
    assert reported == [1.0]


def test_read_reply_broken_pipe_mid_progress():
    partial = _progress_buf(
        {"type": "progress", "step": 1, "total": 5},
        {"type": "progress", "step": 2, "total": 5},
    )
    with pytest.raises(FramingError):
        read_reply(_reader(partial), lambda _: None)


def _serve_with_progress(sock_path: str, steps: int, reply: dict) -> threading.Thread:
    """A one-shot UDS server that sends ``steps`` progress frames then the typed result."""
    if os.path.exists(sock_path):
        os.unlink(sock_path)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(sock_path)
    srv.listen(1)

    def handle() -> None:
        try:
            conn, _ = srv.accept()
            try:
                unframe(conn.recv)
                for i in range(1, steps + 1):
                    conn.sendall(frame({"type": "progress", "step": i, "total": steps}))
                conn.sendall(frame({"type": "result", **reply}))
            finally:
                conn.close()
        finally:
            srv.close()

    thread = threading.Thread(target=handle, daemon=True)
    thread.start()
    return thread


def test_work_receives_progress_from_worker(tmp_path, monkeypatch):
    sock_path = str(tmp_path / "gen.sock")
    monkeypatch.setenv("COSMOS3_GEN_SOCK", sock_path)
    monkeypatch.setenv("COSMOS3_INPUT_ALLOWLIST", str(tmp_path))
    reply = {"ok": True, "artifact_path": str(tmp_path / "a.mp4"),
             "meta": {"engine": "diffusers_oracle", "precision": "fp8"}}
    _serve_with_progress(sock_path, 3, reply)
    reported: list[float] = []
    result = work(_record("t2v", {"prompt": "test"}), reported.append)
    assert isinstance(result, WorkResult)
    assert result.artifact_path.endswith("a.mp4")
    # 0.0 (connect) + 3 step fractions + 1.0 (final safety tick, idempotent with last step)
    assert reported == pytest.approx([0.0, 1 / 3, 2 / 3, 1.0, 1.0])
    assert all(reported[i] <= reported[i + 1] for i in range(len(reported) - 1))  # monotonic


def test_work_ok_reply_returns_workresult(tmp_path, monkeypatch):
    sock_path = str(tmp_path / "gen.sock")
    monkeypatch.setenv("COSMOS3_GEN_SOCK", sock_path)
    monkeypatch.setenv("COSMOS3_INPUT_ALLOWLIST", str(tmp_path))
    reply = {"ok": True, "artifact_path": str(tmp_path / "a.mp4"),
             "meta": {"engine": "diffusers_oracle", "precision": "nvfp4"}}
    _serve_one(sock_path, reply)
    result = work(_record("t2v", {"prompt": "a robotic arm"}), lambda _f: None)
    assert isinstance(result, WorkResult)
    assert result.artifact_path.endswith("a.mp4") and result.meta["precision"] == "nvfp4"


def test_work_error_reply_raises_typed_code(tmp_path, monkeypatch):
    sock_path = str(tmp_path / "gen.sock")
    monkeypatch.setenv("COSMOS3_GEN_SOCK", sock_path)
    monkeypatch.setenv("COSMOS3_INPUT_ALLOWLIST", str(tmp_path))
    _serve_one(sock_path, {"ok": False, "code": "internal_error", "message": "engine boom"})
    with pytest.raises(Exception) as excinfo:  # noqa: PT011 — assert the carried code below
        work(_record("t2v", {"prompt": "x"}), lambda _f: None)
    assert getattr(excinfo.value, "code", None) == "internal_error"


def test_default_gen_timeout_inv_p3_4():
    """INV-P3-4: generation timeout default >= 2400s."""
    import inspect

    from jobs import gen_client

    source = inspect.getsource(gen_client.work)
    # The default is the second argument to os.environ.get("COSMOS3_GEN_TIMEOUT", "<value>")
    assert '"2400"' in source, f"Expected default '2400' in work() source; INV-P3-4 violated"


def test_work_timeout_raises(tmp_path, monkeypatch):
    sock_path = str(tmp_path / "gen.sock")
    monkeypatch.setenv("COSMOS3_GEN_SOCK", sock_path)
    monkeypatch.setenv("COSMOS3_INPUT_ALLOWLIST", str(tmp_path))
    monkeypatch.setenv("COSMOS3_GEN_TIMEOUT", "0.3")
    _serve_one(sock_path, None)  # accepts but never replies
    with pytest.raises(Exception):  # noqa: B017,PT011 — a socket timeout (no .code) → runner maps internal_error
        work(_record("t2v", {"prompt": "x"}), lambda _f: None)
