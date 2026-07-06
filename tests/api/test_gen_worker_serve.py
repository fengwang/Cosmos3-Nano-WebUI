"""gen_worker dispatch + socket/ready ordering (host; fake adapters + stubbed encoders).

Spec: session_7/specs/generation-plane-inference-channel.md — one pipeline serves both generation and
action; readiness is signalled only after the socket is accepting. The real pipeline runs gated-live.
"""
from __future__ import annotations

import os
import socket
import threading
import time

import pytest

from engines.base import EngineInfo, GenerationResult, Precision
from engines.diffusers_action.adapter import ActionResult
from jobs.gen_client import frame, read_reply
from orchestrator import gen_worker


class _FakeGen:
    def __init__(self) -> None:
        self.calls: list = []

    def generate(self, request, on_progress=None) -> GenerationResult:
        self.calls.append(request)
        return GenerationResult(
            case_id="ec", latents=[[0.1, 0.2]], frames=["f0", "f1"], audio=None,
            vram_peak_bytes=123, info=EngineInfo("diffusers_oracle", Precision.NVFP4, "/d"),
        )


class _FakeAction:
    def __init__(self) -> None:
        self.calls: list = []

    def generate_action(self, request) -> ActionResult:
        self.calls.append(request)
        return ActionResult(
            case_id="a", trajectory=[[1.0] * 9], frames=["f0"], vram_peak_bytes=99,
            info=EngineInfo("diffusers_action", Precision.NVFP4, "/d"),
        )


@pytest.fixture
def _enc(monkeypatch, tmp_path):
    """Stub the heavy encoders (numpy/imageio absent on host); record what was asked to be written."""
    monkeypatch.setattr(gen_worker.artifacts, "write_image_png", lambda f, jid, **k: f"{tmp_path}/{jid}.png")
    monkeypatch.setattr(gen_worker.artifacts, "write_video_mp4", lambda f, jid, **k: f"{tmp_path}/{jid}.mp4")
    monkeypatch.setattr(
        gen_worker.artifacts, "write_video_with_audio",
        lambda f, a, jid, **k: (f"{tmp_path}/{jid}.mp4", {"audio": "muxed"}),
    )
    monkeypatch.setattr(gen_worker.artifacts, "write_trajectory_json", lambda t, jid, **k: f"{tmp_path}/{jid}.json")
    monkeypatch.setattr(gen_worker.artifacts, "write_latents_npy", lambda x, jid, **k: f"{tmp_path}/{jid}.npy")
    return tmp_path


def _gen_req(mode, want_latents=False, **params):
    return {"job_id": "j1", "kind": "generation", "mode": mode, "params": params, "want_latents": want_latents}


def test_dispatch_generation_t2v_routes_to_gen_adapter(_enc):
    gen, action = _FakeGen(), _FakeAction()
    reply = gen_worker.dispatch(_gen_req("t2v", prompt="a robotic arm", num_frames=4), gen, action)
    assert reply["ok"] and reply["artifact_path"].endswith("j1.mp4")
    assert reply["meta"] == {"engine": "diffusers_oracle", "precision": "nvfp4", "vram_peak_bytes": 123}
    assert len(gen.calls) == 1 and not action.calls  # routed to the generation adapter
    assert gen.calls[0].prompt == "a robotic arm" and gen.calls[0].num_frames == 4


def test_dispatch_t2i_writes_png(_enc):
    reply = gen_worker.dispatch(_gen_req("t2i", prompt="x"), _FakeGen(), _FakeAction())
    assert reply["artifact_path"].endswith("j1.png")


def test_dispatch_t2v_audio_muxes(_enc):
    reply = gen_worker.dispatch(_gen_req("t2v_audio", prompt="x", generate_sound=True), _FakeGen(), _FakeAction())
    assert reply["artifact_path"].endswith("j1.mp4") and reply["meta"]["audio"] == "muxed"


def test_dispatch_want_latents_writes_sidecar(_enc):
    reply = gen_worker.dispatch(_gen_req("t2v", want_latents=True, prompt="x"), _FakeGen(), _FakeAction())
    assert reply["meta"]["latents_path"].endswith("j1.npy")  # EC-G1 boundary check needs the M1 latents


def test_dispatch_action_inverse_dynamics_trajectory_primary(_enc):
    gen, action = _FakeGen(), _FakeAction()
    reply = gen_worker.dispatch(
        {"job_id": "j1", "kind": "action", "mode": "inverse_dynamics", "params": {"domain_name": "av"}}, gen, action
    )
    assert reply["ok"] and reply["artifact_path"].endswith("j1.json")  # trajectory is the primary artifact
    assert len(action.calls) == 1 and not gen.calls


def test_dispatch_action_forward_dynamics_video_plus_trajectory(_enc):
    reply = gen_worker.dispatch(
        {"job_id": "j1", "kind": "action", "mode": "forward_dynamics",
         "params": {"domain_name": "agibotworld", "chunk_size": 17}}, _FakeGen(), _FakeAction()
    )
    assert reply["artifact_path"].endswith("j1.mp4")  # rollout video
    assert reply["meta"]["trajectory_path"].endswith("j1.json")  # + trajectory sidecar


def test_dispatch_engine_error_is_typed_failure(_enc):
    class _Boom:
        def generate(self, request, on_progress=None):
            raise RuntimeError("cuda oom")

    reply = gen_worker.dispatch(_gen_req("t2v", prompt="x"), _Boom(), _FakeAction())
    assert reply["ok"] is False and reply["code"] == "internal_error" and "cuda oom" in reply["message"]


def _recorder() -> tuple[list[tuple[int, int]], object]:
    """A (step, total) recorder and its on_progress callback."""
    calls: list[tuple[int, int]] = []
    return calls, lambda step, total: calls.append((step, total))


def test_dispatch_passes_progress_to_gen_adapter(_enc):
    calls, cb = _recorder()

    class _ProgressGen(_FakeGen):
        def generate(self, request, on_progress=None):
            if on_progress:
                on_progress(1, 2)
                on_progress(2, 2)
            return super().generate(request)

    reply = gen_worker.dispatch(_gen_req("t2v", prompt="x"), _ProgressGen(), _FakeAction(), on_progress=cb)
    assert reply["ok"]
    assert calls == [(1, 2), (2, 2)]


def test_dispatch_progress_callback_exception_becomes_error_reply(_enc):
    def _exploding_progress(step, total):
        raise BrokenPipeError("client gone")

    class _CallbackGen(_FakeGen):
        def generate(self, request, on_progress=None):
            if on_progress:
                on_progress(1, 5)
            return super().generate(request)

    reply = gen_worker.dispatch(_gen_req("t2v", prompt="x"), _CallbackGen(), _FakeAction(), on_progress=_exploding_progress)
    assert reply["ok"] is False and reply["code"] == "internal_error"
    assert "client gone" in reply["message"]


def test_dispatch_action_ignores_progress(_enc):
    calls, cb = _recorder()
    reply = gen_worker.dispatch(
        {"job_id": "j1", "kind": "action", "mode": "inverse_dynamics", "params": {"domain_name": "av"}},
        _FakeGen(), _FakeAction(), on_progress=cb,
    )
    assert reply["ok"]
    assert calls == []


def _wait_ready(ready_path: str, timeout: float = 3.0) -> None:
    for _ in range(int(timeout / 0.01)):
        if os.path.exists(ready_path):
            return
        time.sleep(0.01)
    raise TimeoutError(f"ready file {ready_path} not created")


def test_serve_sends_progress_frames_over_socket(_enc, tmp_path, monkeypatch):
    """T1 review fix: verify serve()'s per-connection on_progress closure sends progress frames."""
    sock_path, ready = str(tmp_path / "gen.sock"), str(tmp_path / "ready")
    monkeypatch.setenv("COSMOS3_GEN_SOCK", sock_path)

    class _SteppingGen(_FakeGen):
        def generate(self, request, on_progress=None):
            if on_progress:
                for i in range(1, 4):
                    on_progress(i, 3)
            return super().generate(request)

    threading.Thread(target=gen_worker.serve, args=(ready, _SteppingGen(), _FakeAction()), daemon=True).start()
    _wait_ready(ready)
    reported: list[float] = []
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect(sock_path)
        sock.sendall(frame(_gen_req("t2v", prompt="x")))
        reply = read_reply(sock.recv, reported.append)
    assert reply["ok"] and reply["artifact_path"].endswith("j1.mp4")
    assert reported == pytest.approx([1 / 3, 2 / 3, 1.0])


def test_serve_callback_exception_sends_error_frame(_enc, tmp_path, monkeypatch):
    """T2 review fix: verify that a BrokenPipeError in the callback produces a typed error reply on the socket."""
    sock_path, ready = str(tmp_path / "gen.sock"), str(tmp_path / "ready")
    monkeypatch.setenv("COSMOS3_GEN_SOCK", sock_path)

    class _ExplodingGen(_FakeGen):
        def generate(self, request, on_progress=None):
            if on_progress:
                on_progress(1, 5)  # first progress succeeds...
                raise BrokenPipeError("client gone")  # ...then the pipe breaks
            return super().generate(request)

    threading.Thread(target=gen_worker.serve, args=(ready, _ExplodingGen(), _FakeAction()), daemon=True).start()
    _wait_ready(ready)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)
        sock.connect(sock_path)
        sock.sendall(frame(_gen_req("t2v", prompt="x")))
        reply = read_reply(sock.recv, lambda _: None)
    assert reply["ok"] is False and reply["code"] == "internal_error"
    assert "client gone" in reply["message"]


def test_serve_signals_ready_only_after_listening(_enc, tmp_path, monkeypatch):
    sock_path, ready = str(tmp_path / "gen.sock"), str(tmp_path / "ready")
    monkeypatch.setenv("COSMOS3_GEN_SOCK", sock_path)
    gen, action = _FakeGen(), _FakeAction()
    threading.Thread(target=gen_worker.serve, args=(ready, gen, action), daemon=True).start()
    _wait_ready(ready)
    # ready ⇒ the socket is accepting: a client connect + request must succeed (proves the ordering).
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(sock_path)
        sock.sendall(frame(_gen_req("t2v", prompt="x")))
        reply = read_reply(sock.recv, lambda _: None)
    assert reply["ok"] and reply["artifact_path"].endswith("j1.mp4")
