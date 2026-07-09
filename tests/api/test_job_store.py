"""Spec: async-job-model — in-memory store + idempotency + event log (INV-5)."""
from __future__ import annotations

import itertools

import pytest

from app.schemas import JobStatus
from jobs.model import cancel, start
from jobs.store import IdempotencyConflict, JobNotFound, JobStore, fingerprint
from orchestrator.planes import Plane


def _store() -> JobStore:
    counter = itertools.count(1)
    return JobStore(id_factory=lambda: f"job{next(counter)}", clock=lambda: "t0")


def test_submit_creates_queued_job_with_event():
    store = _store()
    rec, replayed = store.submit("t2i", Plane.GENERATION, {"prompt": "x"})
    assert rec.id == "job1" and rec.status is JobStatus.queued and replayed is False
    assert [e.type for e in store.log("job1")] == ["queued"]
    assert store.get("job1") is rec


def test_idempotent_replay_same_key_same_payload():
    store = _store()
    rec1, r1 = store.submit("t2i", Plane.GENERATION, {"prompt": "x"}, key="abc")
    rec2, r2 = store.submit("t2i", Plane.GENERATION, {"prompt": "x"}, key="abc")
    assert r1 is False and r2 is True
    assert rec1.id == rec2.id  # same job replayed, not duplicated


def test_idempotency_conflict_on_different_payload():
    store = _store()
    store.submit("t2i", Plane.GENERATION, {"prompt": "x"}, key="abc")
    with pytest.raises(IdempotencyConflict):
        store.submit("t2i", Plane.GENERATION, {"prompt": "DIFFERENT"}, key="abc")


def test_get_unknown_raises_jobnotfound():
    with pytest.raises(JobNotFound):
        _store().get("nope")


def test_update_is_atomic_transition():
    store = _store()
    rec, _ = store.submit("t2i", Plane.GENERATION, {})
    running = store.update(rec.id, start)
    assert running.status is JobStatus.running
    assert store.get(rec.id).status is JobStatus.running


def test_update_propagates_transition_error():
    from jobs.model import JobTransitionError

    store = _store()
    rec, _ = store.submit("t2i", Plane.GENERATION, {})
    store.update(rec.id, start)
    store.update(rec.id, cancel)  # running -> cancelled
    with pytest.raises(JobTransitionError):
        store.update(rec.id, cancel)  # cancelled -> cancelled is illegal


def test_events_are_monotonic_and_logged():
    store = _store()
    rec, _ = store.submit("t2i", Plane.GENERATION, {})
    store.append_event(rec.id, "running")
    store.append_event(rec.id, "progress", {"progress": 0.5})
    ids = [e.id for e in store.log(rec.id)]
    assert ids == [1, 2, 3]  # queued(1), running(2), progress(3) — monotonic


def test_fingerprint_is_order_independent_for_params():
    assert fingerprint("t2i", {"a": 1, "b": 2}) == fingerprint("t2i", {"b": 2, "a": 1})
    assert fingerprint("t2i", {"a": 1}) != fingerprint("t2v", {"a": 1})
