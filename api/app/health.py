"""Health endpoints — Actions (thin shell): read injected state, call pure calc, return.

Liveness is always 200 once the process serves; readiness is 200 only after warmup
completes, else 503 'warming' (RK-07/EC-S5). The readiness source is injected (never a
global), so the route stays a thin Action over the pure readiness Calculations.
"""
from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, Response, status

from app.readiness import WarmupState, is_ready, liveness_payload, readiness_payload
from app.schemas import HealthStatus


class ReadinessSource(Protocol):
    """Structural type for whatever holds the current immutable WarmupState."""

    state: WarmupState


def build_health_router(holder: ReadinessSource) -> APIRouter:
    """Build the ``/v1/health`` router bound to an injected readiness source."""
    router = APIRouter(prefix="/v1/health", tags=["health"])

    @router.get("/live", response_model=HealthStatus)
    def live() -> HealthStatus:
        return liveness_payload()

    @router.get(
        "/ready",
        response_model=HealthStatus,
        responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthStatus}},
    )
    def ready(response: Response) -> HealthStatus:
        state = holder.state
        if not is_ready(state):
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return readiness_payload(state)

    return router
