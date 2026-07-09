"""HTTP request instrumentation — a pure-ASGI middleware (Action shell; SSE-safe).

Records ``cosmos3_http_requests_total{method,route,status}`` +
``cosmos3_http_request_duration_seconds{method,route}`` for every HTTP request, where ``route`` is the matched
route **template** (bounded cardinality — a concrete job id is never a label value). It is a *pure ASGI*
middleware (not ``BaseHTTPMiddleware``, which buffers the response body and would break the SSE streams), so
it observes ``http.response.start`` for the status and the wall-clock for the duration without ever buffering
the body. A metrics error is swallowed (debug-logged) — instrumentation must never break the request path.
"""
from __future__ import annotations

import logging
from time import perf_counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.observability.metrics import Metrics

_log = logging.getLogger("cosmos3.metrics.http")

_UNMATCHED = "__unmatched__"


def _route_template(scope) -> str:
    """The matched route template (e.g. ``/v1/jobs/{job_id}``), or a single bucket for unmatched paths."""
    route = scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else _UNMATCHED


class MetricsMiddleware:
    """Pure-ASGI middleware counting + timing HTTP requests by method / matched-route / status."""

    def __init__(self, app, metrics: Metrics) -> None:
        self.app = app
        self._metrics = metrics

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        start = perf_counter()
        status_holder = {"code": 0}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
            await send(message)  # pass through immediately — never buffer (SSE-safe)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = perf_counter() - start
            try:
                method = scope.get("method", "UNKNOWN")
                route = _route_template(scope)
                self._metrics.http_requests.labels(method, route, str(status_holder["code"])).inc()
                self._metrics.http_duration.labels(method, route).observe(elapsed)
            except Exception as exc:  # noqa: BLE001 — never break the request path on a metrics error
                _log.debug("http metrics observe failed: %s", exc)
