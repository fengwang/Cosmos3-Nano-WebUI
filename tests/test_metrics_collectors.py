"""S11: scrape-time gauge collectors — queue depth from a read-only store snapshot + resident plane.

Host-loop (torch-free). Anchors the core seam: instrument the frozen ``JobStore`` without mutating it, and
report the queue depth + job-state distribution + resident plane (spec: metrics-endpoint — queue-depth gauge,
resident-plane; design D3).
"""
from __future__ import annotations

from prometheus_client import CollectorRegistry

from app.observability.collectors import StateCollector
from app.schemas import JobStatus
from jobs.store import JobStore
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId


class _StubOrch:
    def __init__(self, resident: ResidencyId | None = None) -> None:
        self.resident = resident


def _registry_with(store: JobStore, orch: _StubOrch) -> CollectorRegistry:
    reg = CollectorRegistry()
    reg.register(StateCollector(store, orch))
    return reg


def test_queue_depth_from_store_snapshot():
    store = JobStore()
    store.submit("t2v", Plane.GENERATION, {"prompt": "a"})
    store.submit("t2i", Plane.GENERATION, {"prompt": "b"})
    reg = _registry_with(store, _StubOrch())

    assert reg.get_sample_value("cosmos3_jobs", {"state": "queued"}) == 2.0
    # all five lifecycle states present (incl. zeros) so a dashboard never sees a missing series
    for status in JobStatus:
        assert reg.get_sample_value("cosmos3_jobs", {"state": status.value}) is not None


def test_scrape_is_side_effect_free():
    store = JobStore()
    rec, _ = store.submit("t2v", Plane.GENERATION, {"prompt": "a"})
    reg = _registry_with(store, _StubOrch())

    before_events = len(store.log(rec.id))
    list(reg.collect())  # scrape
    list(reg.collect())  # scrape again

    assert store.get(rec.id).status is JobStatus.queued  # not transitioned by the scrape
    assert len(store.log(rec.id)) == before_events  # no event appended by the scrape


def test_resident_plane_reflected():
    reg = _registry_with(JobStore(), _StubOrch(resident=ResidencyId(Plane.GENERATION)))
    assert reg.get_sample_value("cosmos3_plane_resident", {"plane": "generation"}) == 1.0
    assert reg.get_sample_value("cosmos3_plane_resident", {"plane": "reasoning"}) == 0.0


def test_cold_slot_has_no_resident_plane():
    reg = _registry_with(JobStore(), _StubOrch(resident=None))
    assert reg.get_sample_value("cosmos3_plane_resident", {"plane": "generation"}) == 0.0
    assert reg.get_sample_value("cosmos3_plane_resident", {"plane": "reasoning"}) == 0.0
