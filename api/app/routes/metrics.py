"""The ``/v1/metrics`` operational endpoint (Action shell; S11 observability).

Returns the Prometheus exposition for the app's private registry. ``include_in_schema=False`` (a plaintext
operational endpoint — not a JSON API contract, so it stays out of the OpenAPI ⇒ no ``schemas/openapi.json``
drift) and is mounted WITHOUT the auth dependency (mirrors ``/v1/health/*``; the ``api`` is private-network
only per INV-1, so the scraper reaches it directly). Refs: session_11/specs/metrics-endpoint.md.
"""
from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Response


def build_metrics_router(render_fn: Callable[[], tuple[bytes, str]]) -> APIRouter:
    """Build the metrics router; ``render_fn`` returns (exposition_bytes, content_type) for the registry."""
    router = APIRouter(tags=["metrics"])

    @router.get("/v1/metrics", include_in_schema=False)
    def metrics() -> Response:
        body, content_type = render_fn()
        return Response(content=body, media_type=content_type)

    return router
