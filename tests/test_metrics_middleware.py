"""S11: the pure-ASGI HTTP metrics middleware — route-template label, status, and SSE-safety.

Spec: app-layer-instrumentation (HTTP, SSE-safe, bounded cardinality).
"""
from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import StreamingResponse

from app.observability.metrics import build_metrics
from app.observability.middleware import MetricsMiddleware


def _app():
    metrics, reg = build_metrics()
    app = FastAPI()
    app.add_middleware(MetricsMiddleware, metrics=metrics)

    @app.get("/v1/items/{item_id}")
    def item(item_id: str):
        return {"id": item_id}

    return app, reg


def _req_count(reg, route, status):
    return reg.get_sample_value(
        "cosmos3_http_requests_total", {"method": "GET", "route": route, "status": status}
    )


def test_request_counted_and_timed_by_route_and_status():
    app, reg = _app()
    client = TestClient(app)
    assert client.get("/v1/items/abc").status_code == 200
    assert _req_count(reg, "/v1/items/{item_id}", "200") == 1.0
    assert (
        reg.get_sample_value(
            "cosmos3_http_request_duration_seconds_count",
            {"method": "GET", "route": "/v1/items/{item_id}"},
        )
        == 1.0
    )


def test_param_route_collapses_ids_to_one_series():
    app, reg = _app()
    client = TestClient(app)
    for jid in ("a", "b", "c"):
        client.get(f"/v1/items/{jid}")
    # one series for the template, not three id-specific ones (bounded cardinality)
    assert _req_count(reg, "/v1/items/{item_id}", "200") == 3.0


async def _streaming_inner(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    for i in range(3):
        await send({"type": "http.response.body", "body": f"c{i}".encode(), "more_body": i < 2})


def test_streaming_response_is_not_buffered():
    metrics, _reg = build_metrics()
    mw = MetricsMiddleware(_streaming_inner, metrics)
    sent_types: list[str] = []

    async def send(message):
        sent_types.append(message["type"])

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    scope = {"type": "http", "method": "GET", "path": "/v1/stream"}
    asyncio.run(mw(scope, receive, send))
    # all three body chunks passed straight through (not coalesced/buffered into one)
    assert sent_types.count("http.response.body") == 3


def test_non_http_scope_passes_through():
    metrics, _reg = build_metrics()
    seen = {"called": False}

    async def inner(scope, receive, send):
        seen["called"] = True

    mw = MetricsMiddleware(inner, metrics)
    asyncio.run(mw({"type": "lifespan"}, None, None))
    assert seen["called"] is True


def test_streaming_route_through_real_app_still_streams():
    metrics, reg = build_metrics()
    app = FastAPI()
    app.add_middleware(MetricsMiddleware, metrics=metrics)

    @app.get("/v1/stream")
    def stream():
        def gen():
            for i in range(3):
                yield f"chunk{i}\n"

        return StreamingResponse(gen(), media_type="text/plain")

    client = TestClient(app)
    r = client.get("/v1/stream")
    assert r.status_code == 200
    assert r.text == "chunk0\nchunk1\nchunk2\n"
    assert _req_count(reg, "/v1/stream", "200") == 1.0
