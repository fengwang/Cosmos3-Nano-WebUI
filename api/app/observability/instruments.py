"""Metered pass-through wrappers — instrument the frozen orchestrator + job-work from the app edge.

``MeteredOrchestrator`` wraps the real ``Orchestrator`` (identical surface), timing ``acquire()`` and
labelling the ``transition`` (cold_load | swap | reacquire) read from the public ``resident`` — delegating
**verbatim** (the FSM/lock inside the inner orchestrator are untouched, so INV-4 is unchanged). ``metered_work``
wraps a ``Work`` callable, timing the job + counting the outcome, and **re-raises** on failure so the frozen
runner's failure/cancel handling is preserved. Torch-free; the only coupling is the injected ``Metrics`` handle.
"""
from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.observability.metrics import Metrics
    from jobs.model import JobRecord
    from jobs.runner import ProgressCb, Work, WorkResult
    from orchestrator.residency import ResidencyId


class MeteredOrchestrator:
    """A pass-through proxy over ``Orchestrator`` that times ``acquire`` and labels the plane transition."""

    def __init__(self, inner, metrics: Metrics) -> None:
        self._inner = inner
        self._metrics = metrics

    @property
    def resident(self) -> ResidencyId | None:
        return self._inner.resident

    async def acquire(self, target: ResidencyId) -> None:
        before = self._inner.resident
        transition = "cold_load" if before is None else ("reacquire" if before == target else "swap")
        start = perf_counter()
        try:
            await self._inner.acquire(target)
        finally:
            self._metrics.plane_acquire.labels(target.plane.value, transition).observe(perf_counter() - start)

    async def evict_all(self) -> None:
        await self._inner.evict_all()

    def notify_idle(self) -> None:
        self._inner.notify_idle()


def metered_work(inner: Work, metrics: Metrics) -> Work:
    """Wrap a ``Work`` callable to observe job duration + the terminal outcome, re-raising on failure."""

    def wrapped(record: JobRecord, report: ProgressCb) -> WorkResult:
        start = perf_counter()
        mode = record.mode
        try:
            result = inner(record, report)
        except Exception:
            metrics.job_duration.labels(mode, "failed").observe(perf_counter() - start)
            metrics.job_terminal.labels(mode, "failed").inc()
            raise  # preserve the frozen runner's failure/cancel handling
        metrics.job_duration.labels(mode, "succeeded").observe(perf_counter() - start)
        metrics.job_terminal.labels(mode, "succeeded").inc()
        return result

    return wrapped
