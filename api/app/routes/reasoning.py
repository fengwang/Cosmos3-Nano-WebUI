"""Reasoning capability endpoint (S7; FR3): text+image/video → text, streamed as SSE.

`POST /v1/reason` validates the public context cap at the edge (CPU tokenizer or a conservative
heuristic → 422 `context_over_cap` BEFORE any GPU touch), resolves conditioning paths (→ 422
`untrusted_path`), then — holding the shared **GPU lease** for the whole stream (so no job evicts the
reasoner mid-stream, INV-4) — acquires the reasoning plane and **proxy-streams** the out-of-process
vLLM OpenAI server's deltas as SSE. The upstream is an injectable `ReasonerStream` seam: host tests
inject a fake generator; gated-live uses `VllmReasonerStream` (stdlib `urllib`, no httpx dependency).
Refs: session_7/specs/reasoning-endpoint.md; design.md D-4/D-8.
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import threading
from collections.abc import Iterator
from typing import Protocol

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.jobs_router import _input_allowlist
from app.schemas import ReasoningBody
from engines.vllm.context_cap import ContextCapConfig, ReasoningValidationFailed, validate_context
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId
from preprocessing.paths import resolve_within


class ReasonerStream(Protocol):
    """The injectable upstream seam: yield content delta strings for one chat request."""

    def stream(self, payload: dict) -> Iterator[str]: ...


def count_tokens(tokenizer, prompt: str) -> int:
    """Count prompt tokens with a CPU tokenizer, or a conservative ceil(len/3) over-estimate fallback (D-8)."""
    if tokenizer is not None:
        try:
            return len(tokenizer.encode(prompt))
        except Exception:  # noqa: BLE001 — a tokenizer hiccup must not 500; fall back to the heuristic
            pass
    return math.ceil(len(prompt) / 3)


def _sse(kind: str, value: str = "") -> str:
    if kind == "token":
        return f"event: token\ndata: {json.dumps({'delta': value})}\n\n"
    if kind == "error":
        return f"event: error\ndata: {json.dumps({'message': value})}\n\n"
    if kind == "heartbeat":
        return "event: heartbeat\ndata: {}\n\n"
    return "event: done\ndata: {}\n\n"


async def _relay(stream: ReasonerStream, payload: dict, *, heartbeat_seconds: float):
    """Bridge the (blocking) upstream iterator to an async SSE event stream, with idle heartbeats.

    The blocking `stream.stream(...)` runs in the default executor; deltas cross via a queue. A pending
    `get` is preserved across heartbeat ticks (never cancelled mid-item) so no delta is dropped. On
    consumer disconnect (the generator is `aclose`-d) the `finally` sets the stop flag — so the pump
    breaks out of the upstream read on its next line — and cancels the pending `get`, so neither the
    executor thread nor a pending task leaks while the client is gone (the upstream `urlopen` carries a
    timeout, so even a stalled read unwinds).
    """
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    sentinel = object()
    stop = threading.Event()

    def pump() -> None:
        upstream = stream.stream(payload)
        try:
            for delta in upstream:
                if stop.is_set():
                    break  # consumer gone → stop iterating the upstream
                loop.call_soon_threadsafe(queue.put_nowait, delta)
        except Exception as exc:  # noqa: BLE001 — surface an upstream failure as a stream 'error' event
            loop.call_soon_threadsafe(queue.put_nowait, RuntimeError(str(exc)))
        finally:
            closer = getattr(upstream, "close", None)
            if closer is not None:
                closer()  # run the upstream generator's finally → closes its urlopen response handle
            loop.call_soon_threadsafe(queue.put_nowait, sentinel)

    loop.run_in_executor(None, pump)
    get_task: asyncio.Task | None = None
    try:
        while True:
            if get_task is None:
                get_task = asyncio.ensure_future(queue.get())
            done, _ = await asyncio.wait({get_task}, timeout=heartbeat_seconds)
            if not done:
                yield _sse("heartbeat")
                continue
            item = get_task.result()
            get_task = None
            if item is sentinel:
                yield _sse("done")
                return
            if isinstance(item, Exception):
                yield _sse("error", str(item))
                yield _sse("done")
                return
            yield _sse("token", item)
    finally:
        stop.set()  # disconnect / done: release the pump thread + the pending get (no leak)
        if get_task is not None:
            get_task.cancel()


def build_reasoning_router(
    orchestrator, gpu_lease: asyncio.Lock, *, stream: ReasonerStream,
    cap: ContextCapConfig, tokenizer=None,
) -> APIRouter:
    """Build the ``/v1/reason`` router. ``stream``/``cap``/``tokenizer`` are injected (real or test)."""
    router = APIRouter(prefix="/v1", tags=["reasoning"])
    heartbeat = float(os.environ.get("COSMOS3_SSE_HEARTBEAT_SECONDS", "15"))

    @router.post("/reason")
    async def reason(body: ReasoningBody) -> StreamingResponse:
        # --- validate BEFORE any GPU acquisition (errors here become a clean 4xx) ---
        prompt_tokens = count_tokens(tokenizer, body.prompt)
        # An omitted budget means "as much as the context allows": the smaller of the configured output
        # ceiling and the remaining context window. Under the default config (ceiling == context window)
        # this is (max_context_tokens − prompt_tokens), so reasoning is bounded only by the context and is
        # never truncated at the old 256/1024 cap (FR-10, INV-12). A prompt that fills the window leaves
        # no room → validate_context surfaces context_over_cap below.
        if body.max_output_tokens is None:
            effective = min(cap.max_output_tokens, max(1, cap.max_context_tokens - prompt_tokens))
        else:
            effective = body.max_output_tokens
        error = validate_context(prompt_tokens, effective, cap)
        if error is not None:
            raise ReasoningValidationFailed(error)  # → 422 (empty_prompt / bad_max_tokens / context_over_cap)
        allowlist = _input_allowlist()
        image_path = resolve_within(body.image_path, allowlist) if body.image_path else None  # → 422 on escape
        video_path = resolve_within(body.video_path, allowlist) if body.video_path else None
        payload = {
            "prompt": body.prompt, "max_tokens": effective,
            "image_path": image_path, "video_path": video_path,
        }

        async def gen():
            async with gpu_lease:  # held for the whole stream → no job evicts the reasoner mid-stream
                try:
                    await orchestrator.acquire(ResidencyId(Plane.REASONING))
                except Exception as exc:  # noqa: BLE001 — 200+headers already sent: surface as an SSE error
                    yield _sse("error", f"reasoning plane unavailable: {exc}")
                    yield _sse("done")
                    return
                try:
                    async for chunk in _relay(stream, payload, heartbeat_seconds=heartbeat):
                        yield chunk
                finally:
                    orchestrator.notify_idle()

        return StreamingResponse(
            gen(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
        )

    return router


class VllmReasonerStream:
    """Production upstream (gated-live): stream the vLLM OpenAI server via stdlib ``urllib`` (no httpx)."""

    def __init__(self, *, host: str = "127.0.0.1", port: int | None = None, model: str = "cosmos3-reasoner") -> None:
        self._host = host
        self._port = port or int(os.environ.get("COSMOS3_VLLM_PORT", "8765"))
        self._model = model

    def _messages(self, payload: dict) -> list:
        content: list = []
        for key, kind in (("image_path", "image_url"), ("video_path", "video_url")):
            if payload.get(key):
                content.append({"type": kind, kind: {"url": _data_uri(payload[key])}})
        content.append({"type": "text", "text": payload["prompt"]})
        return [{"role": "user", "content": content}]

    def stream(self, payload: dict) -> Iterator[str]:
        import urllib.request  # noqa: PLC0415 — gated-live only; stdlib

        body = json.dumps({
            "model": self._model, "messages": self._messages(payload), "stream": True,
            "max_tokens": payload["max_tokens"], "temperature": 0,
        }).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310 — fixed localhost vLLM endpoint
            f"http://{self._host}:{self._port}/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json"},
        )
        timeout = float(os.environ.get("COSMOS3_REASONER_TIMEOUT", "300"))  # bound a stalled upstream read
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            for raw in resp:
                line = raw.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    return
                delta = json.loads(data).get("choices", [{}])[0].get("delta", {}).get("content")
                if delta:
                    yield delta


def _data_uri(path: str) -> str:
    """Action: read a trusted-mount media file into a base64 data URI for the vLLM chat API (INV-8)."""
    import base64  # noqa: PLC0415
    import mimetypes  # noqa: PLC0415

    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as handle:
        return f"data:{mime};base64,{base64.b64encode(handle.read()).decode('ascii')}"
