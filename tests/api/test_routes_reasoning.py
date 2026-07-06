"""Reasoning endpoint: context-cap gate (before acquire), SSE relay, GPU lease (host; fake stream).

Spec: session_7/specs/reasoning-endpoint.md — over-cap/empty/untrusted reject before any acquire;
the upstream deltas are relayed as SSE token events and the stream terminates.
"""
from __future__ import annotations

import asyncio
import threading
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import install_error_handlers
from app.routes.reasoning import _relay, build_reasoning_router
from engines.vllm.context_cap import ContextCapConfig
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId


class _SpyOrch:
    def __init__(self) -> None:
        self.acquired: list = []

    async def acquire(self, target) -> None:
        self.acquired.append(target)

    async def evict_all(self) -> None: ...

    def notify_idle(self) -> None: ...


class _FakeStream:
    def __init__(self, deltas) -> None:
        self.deltas = list(deltas)
        self.payloads: list[dict] = []

    def stream(self, payload: dict):
        self.payloads.append(payload)
        yield from self.deltas


class _WordTokenizer:
    def encode(self, text: str) -> list[str]:
        return text.split()


def _app(stream, *, cap: ContextCapConfig | None = None) -> FastAPI:
    app = FastAPI()
    orch = _SpyOrch()
    cap = cap or ContextCapConfig(max_context_tokens=32768, max_output_tokens=1024)
    app.include_router(
        build_reasoning_router(orch, asyncio.Lock(), stream=stream, cap=cap, tokenizer=_WordTokenizer())
    )
    install_error_handlers(app)
    app.state.orch = orch
    return app


def test_over_cap_rejected_before_acquire():
    app = _app(_FakeStream(["x"]), cap=ContextCapConfig(max_context_tokens=5, max_output_tokens=4))
    with TestClient(app) as client:
        resp = client.post("/v1/reason", json={"prompt": "one two three four five six", "max_output_tokens": 2})
        assert resp.status_code == 422 and resp.json()["code"] == "context_over_cap"
    assert app.state.orch.acquired == []  # the reasoning plane was NOT acquired (rejected at the edge)


def test_empty_prompt_rejected_before_acquire():
    app = _app(_FakeStream(["x"]))
    with TestClient(app) as client:
        resp = client.post("/v1/reason", json={"prompt": ""})
        assert resp.status_code == 422 and resp.json()["code"] == "empty_prompt"
    assert app.state.orch.acquired == []


def test_relay_streams_deltas_and_terminates():
    stream = _FakeStream(["Hello", ", ", "world"])
    app = _app(stream)
    with TestClient(app) as client:
        resp = client.post("/v1/reason", json={"prompt": "why did the arm slip?", "max_output_tokens": 16})
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        assert resp.headers.get("x-accel-buffering") == "no"
        body = resp.text
    assert '"delta": "Hello"' in body and '"delta": "world"' in body  # deltas relayed in order
    assert "event: done" in body  # stream terminates
    assert app.state.orch.acquired == [ResidencyId(Plane.REASONING)]  # acquired exactly once, after validation
    assert stream.payloads[0]["max_tokens"] == 16  # the budget is forwarded


def test_untrusted_image_path_rejected_before_acquire(tmp_path, monkeypatch):
    monkeypatch.setenv("COSMOS3_INPUT_ALLOWLIST", str(tmp_path))
    app = _app(_FakeStream(["x"]))
    with TestClient(app) as client:
        resp = client.post("/v1/reason", json={"prompt": "look", "image_path": "/etc/passwd"})
        assert resp.status_code == 422 and resp.json()["code"] == "untrusted_path"
    assert app.state.orch.acquired == []


def test_relay_releases_upstream_on_consumer_close():
    # sharded-review H1: when the consumer disconnects (aclose), _relay must stop the pump + close the
    # upstream generator — so the reader thread + the GPU work don't leak while the client is gone.
    closed = threading.Event()

    def _infinite():
        try:
            i = 0
            while True:
                yield f"tok{i}"
                i += 1
                time.sleep(0.005)
        finally:
            closed.set()  # the upstream generator's finally (== closing its urlopen response)

    class _InfStream:
        def stream(self, payload):
            return _infinite()

    async def run():
        relay = _relay(_InfStream(), {"prompt": "x"}, heartbeat_seconds=5.0)
        first = await relay.__anext__()  # pull one token
        assert '"delta"' in first
        await relay.aclose()  # consumer disconnects → _relay finally sets stop + the pump closes upstream

    asyncio.run(run())
    assert closed.wait(2.0), "upstream generator was not closed on consumer disconnect (thread/GPU leak)"


# --- S7 reasoning uncap: an omitted budget is bounded only by the context window (FR-10) ---


def test_omitted_budget_uses_full_remaining_context():
    # Default config (output ceiling == context window): omitting max_output_tokens forwards the FULL
    # remaining context as max_tokens — reasoning is no longer truncated at 256 (FR-10, INV-12).
    stream = _FakeStream(["hi"])
    app = _app(stream, cap=ContextCapConfig(max_context_tokens=32768, max_output_tokens=32768))
    with TestClient(app) as client:
        resp = client.post("/v1/reason", json={"prompt": "why did the arm slip"})  # 5 words → 5 tokens
        assert resp.status_code == 200
    assert stream.payloads[0]["max_tokens"] == 32768 - 5


def test_supplied_budget_is_forwarded_unchanged():
    stream = _FakeStream(["hi"])
    app = _app(stream)
    with TestClient(app) as client:
        resp = client.post("/v1/reason", json={"prompt": "explain", "max_output_tokens": 500})
        assert resp.status_code == 200
    assert stream.payloads[0]["max_tokens"] == 500


def test_omitted_budget_respects_an_operator_clamp():
    # An operator hard-ceiling below the window: an omitted budget resolves to the clamp, not a 422.
    stream = _FakeStream(["hi"])
    app = _app(stream, cap=ContextCapConfig(max_context_tokens=32768, max_output_tokens=2048))
    with TestClient(app) as client:
        resp = client.post("/v1/reason", json={"prompt": "explain the pick"})  # 3 words
        assert resp.status_code == 200
    assert stream.payloads[0]["max_tokens"] == 2048


def test_supplied_budget_over_context_rejected_before_acquire():
    app = _app(_FakeStream(["x"]), cap=ContextCapConfig(max_context_tokens=10, max_output_tokens=10))
    with TestClient(app) as client:
        resp = client.post("/v1/reason", json={"prompt": "a b c d e", "max_output_tokens": 9})  # 5+9 > 10
        assert resp.status_code == 422 and resp.json()["code"] == "context_over_cap"
    assert app.state.orch.acquired == []


def test_omitted_budget_when_prompt_fills_window_rejected_before_acquire():
    # The omitted-budget path when the prompt fills the window: effective floors at 1, so the combined
    # total exceeds the cap → context_over_cap (never a silent 1-token truncation), before any acquire.
    app = _app(_FakeStream(["x"]), cap=ContextCapConfig(max_context_tokens=5, max_output_tokens=5))
    with TestClient(app) as client:
        resp = client.post("/v1/reason", json={"prompt": "a b c d e"})  # 5 words == the whole window
        assert resp.status_code == 422 and resp.json()["code"] == "context_over_cap"
    assert app.state.orch.acquired == []
