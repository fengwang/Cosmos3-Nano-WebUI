"""S11: MeteredOrchestrator — faithful pass-through + plane-acquire timing/transition labels.

Spec: app-layer-instrumentation (plane-acquire). Verifies the wrapper instruments without altering behavior
(INV-4): same inner calls, exceptions propagate, ``resident`` proxied, no plane marked by the wrapper itself.

S2: updated to use ResidencyId instead of bare Plane.
"""
from __future__ import annotations

import asyncio

import pytest

from app.observability.instruments import MeteredOrchestrator
from app.observability.metrics import build_metrics
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId

GEN = ResidencyId(Plane.GENERATION)
REASON = ResidencyId(Plane.REASONING)


class _StubOrch:
    def __init__(self, resident: ResidencyId | None = None, raise_exc: Exception | None = None) -> None:
        self._resident = resident
        self._raise = raise_exc
        self.calls: list[tuple] = []

    @property
    def resident(self) -> ResidencyId | None:
        return self._resident

    async def acquire(self, target: ResidencyId) -> None:
        self.calls.append(("acquire", target))
        if self._raise is not None:
            raise self._raise
        self._resident = target

    async def evict_all(self) -> None:
        self.calls.append(("evict_all",))
        self._resident = None

    def notify_idle(self) -> None: ...


def _acq_count(reg, plane, transition):
    return reg.get_sample_value(
        "cosmos3_plane_acquire_duration_seconds_count", {"plane": plane, "transition": transition}
    )


def test_cold_load_labelled_and_delegated():
    metrics, reg = build_metrics()
    inner = _StubOrch(resident=None)
    mo = MeteredOrchestrator(inner, metrics)
    asyncio.run(mo.acquire(GEN))
    assert inner.calls == [("acquire", GEN)]
    assert inner.resident == GEN
    assert mo.resident == GEN
    assert _acq_count(reg, "generation", "cold_load") == 1.0


def test_swap_labelled_distinctly():
    metrics, reg = build_metrics()
    mo = MeteredOrchestrator(_StubOrch(resident=REASON), metrics)
    asyncio.run(mo.acquire(GEN))
    assert _acq_count(reg, "generation", "swap") == 1.0
    assert _acq_count(reg, "generation", "cold_load") is None


def test_failing_acquire_recorded_and_reraised():
    metrics, reg = build_metrics()
    inner = _StubOrch(resident=None, raise_exc=RuntimeError("worker not ready"))
    mo = MeteredOrchestrator(inner, metrics)
    with pytest.raises(RuntimeError, match="worker not ready"):
        asyncio.run(mo.acquire(GEN))
    assert _acq_count(reg, "generation", "cold_load") == 1.0
    assert mo.resident is None


def test_evict_all_delegated():
    metrics, _reg = build_metrics()
    inner = _StubOrch(resident=GEN)
    mo = MeteredOrchestrator(inner, metrics)
    asyncio.run(mo.evict_all())
    assert ("evict_all",) in inner.calls
    assert mo.resident is None
