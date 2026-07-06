"""Scrape-time gauge collectors (Action: read-only observation at ``collect()``).

``cosmos3_jobs{state}`` (queue depth = ``queued``) from a GIL-atomic read-only snapshot of the frozen
``JobStore``, and ``cosmos3_plane_resident{plane}`` from the orchestrator's public ``resident`` property.
Both are computed fresh at scrape time (no background task → no drift) and **never mutate** the observed
objects — the snapshot reads ``store._jobs`` (no public enumerator exists; ``api/jobs/**`` is not edited).
"""
from __future__ import annotations

from collections import Counter as _Counter
from typing import Protocol

from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector, CollectorRegistry

from app.observability.gpu import GpuCollector, gpu_sample
from app.schemas import JobStatus
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId

_STATES = tuple(s.value for s in JobStatus)
_PLANES = tuple(p.value for p in Plane)


class _StoreLike(Protocol):
    _jobs: dict


class _OrchLike(Protocol):
    @property
    def resident(self) -> ResidencyId | None: ...


class StateCollector(Collector):
    """Yields ``cosmos3_jobs{state}`` + ``cosmos3_plane_resident{plane}`` from injected read-only sources."""

    def __init__(self, store: _StoreLike, orchestrator: _OrchLike) -> None:
        self._store = store
        self._orch = orchestrator

    def collect(self):
        # GIL-atomic snapshot of the current statuses — read-only; never mutates the frozen store.
        counts = _Counter(r.status.value for r in list(self._store._jobs.values()))
        jobs = GaugeMetricFamily(
            "cosmos3_jobs", "Async jobs by lifecycle state (queue depth = state=queued).", labels=["state"]
        )
        for state in _STATES:
            jobs.add_metric([state], float(counts.get(state, 0)))
        yield jobs

        resident = getattr(self._orch, "resident", None)
        resident_value = resident.plane.value if resident is not None else None
        planes = GaugeMetricFamily(
            "cosmos3_plane_resident", "Resident orchestrator plane (1=resident, 0=not).", labels=["plane"]
        )
        for plane in _PLANES:
            planes.add_metric([plane], 1.0 if plane == resident_value else 0.0)
        yield planes


def register_collectors(
    registry: CollectorRegistry, store: _StoreLike, orchestrator: _OrchLike, *, gpu_sampler=gpu_sample
) -> None:
    """Register the scrape-time gauge collectors (job state + resident plane + guarded GPU) on the registry."""
    registry.register(StateCollector(store, orchestrator))
    registry.register(GpuCollector(gpu_sampler))
