"""Spec: async-job-model — the serialized runner (EC-S1 lifecycle, EC-S4 cancellation, failure).

A stub orchestrator records acquire/evict_all; injected `work` functions drive each path. Cancellation
of a running job uses a blocking work + threading events to exercise the race-safe path: the slot is
evicted and the job ends `cancelled`, never resurrected to `succeeded` by the work's return.
"""
from __future__ import annotations

import asyncio
import itertools
import threading

import pytest

from app.schemas import JobStatus
from jobs.model import JobRecord, JobTransitionError, start, succeed
from jobs.runner import JobRunner, WorkResult
from jobs.store import JobStore
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId

_TERMINAL = {JobStatus.succeeded, JobStatus.failed, JobStatus.cancelled}


class StubOrch:
    def __init__(self) -> None:
        self.acquired: list = []
        self.evict_all_calls = 0

    async def acquire(self, target) -> None:
        self.acquired.append(target)

    async def evict_all(self) -> None:
        self.evict_all_calls += 1

    def notify_idle(self) -> None: ...


def _store() -> JobStore:
    counter = itertools.count(1)
    return JobStore(id_factory=lambda: f"job{next(counter)}", clock=lambda: "t0")


async def _await_status(store: JobStore, job_id: str, predicate, timeout: float = 5.0) -> JobRecord:
    for _ in range(int(timeout / 0.01)):
        rec = store.get(job_id)
        if predicate(rec):
            return rec
        await asyncio.sleep(0.01)
    return store.get(job_id)


def test_runner_runs_job_to_succeeded(tmp_path):
    store, orch = _store(), StubOrch()

    def work(rec: JobRecord, report) -> WorkResult:
        report(0.5)
        path = tmp_path / "a.png"
        path.write_bytes(b"\x89PNG\r\n\x1a\n")
        return WorkResult(str(path), {"engine": "stub", "precision": "nvfp4"})

    runner = JobRunner(store, orch, work=work)
    rec, _ = store.submit("t2i", Plane.GENERATION, {})

    async def run():
        runner.start()
        await runner.submit(rec)
        await _await_status(store, rec.id, lambda r: r.status in _TERMINAL)
        await runner.stop()

    asyncio.run(run())
    final = store.get(rec.id)
    assert final.status is JobStatus.succeeded and final.artifact_path.endswith("a.png")
    assert final.result_meta == {"engine": "stub", "precision": "nvfp4"}  # meta carried to the record (S7)
    assert orch.acquired == [ResidencyId(Plane.GENERATION)]  # the slot was acquired for the job's plane
    types = [e.type for e in store.log(rec.id)]
    assert "running" in types and "progress" in types and "succeeded" in types


def test_runner_failure_marks_failed_and_releases_slot():
    store, orch = _store(), StubOrch()

    def work(rec, report):
        raise RuntimeError("boom")

    runner = JobRunner(store, orch, work=work)
    rec, _ = store.submit("t2i", Plane.GENERATION, {})

    async def run():
        runner.start()
        await runner.submit(rec)
        await _await_status(store, rec.id, lambda r: r.status in _TERMINAL)
        await runner.stop()

    asyncio.run(run())
    final = store.get(rec.id)
    assert final.status is JobStatus.failed and final.error is not None
    assert orch.evict_all_calls >= 1  # the slot was released after the failure (no leaked residency)


def test_cancel_running_job_evicts_slot_and_marks_cancelled():
    store, orch = _store(), StubOrch()
    started, release = threading.Event(), threading.Event()

    def work(rec, report):
        started.set()
        release.wait(5)  # hold the job 'running' until the test cancels it
        return WorkResult("/tmp/should_not_be_used.png")

    runner = JobRunner(store, orch, work=work)
    rec, _ = store.submit("t2v", Plane.GENERATION, {})

    async def run():
        runner.start()
        await runner.submit(rec)
        await asyncio.to_thread(started.wait, 5)
        await _await_status(store, rec.id, lambda r: r.status is JobStatus.running)
        result = await runner.cancel(rec.id)
        release.set()
        await asyncio.sleep(0.05)
        await runner.stop()
        return result

    result = asyncio.run(run())
    assert result.status is JobStatus.cancelled
    assert orch.evict_all_calls >= 1  # the GPU slot was freed (EC-S4 — provably stopped)
    assert store.get(rec.id).status is JobStatus.cancelled  # not resurrected by work's return


def test_cancel_queued_job_is_not_executed():
    store, orch = _store(), StubOrch()
    ran: list[str] = []

    def work(rec, report):
        ran.append(rec.id)
        return WorkResult("/x.png")

    runner = JobRunner(store, orch, work=work)
    rec, _ = store.submit("t2i", Plane.GENERATION, {})

    async def run():
        result = await runner.cancel(rec.id)  # cancel while queued (runner not draining yet)
        runner.start()
        await runner.submit(rec)
        await asyncio.sleep(0.05)
        await runner.stop()
        return result

    result = asyncio.run(run())
    assert result.status is JobStatus.cancelled
    assert ran == []  # the cancelled job never executed
    assert orch.acquired == []  # and never acquired the slot


def test_acquire_failure_fails_job_not_stuck_queued():
    # INV-5: if orchestrator.acquire raises (worker never ready / OOM), the job MUST reach a terminal
    # state (failed) + the slot released — never linger in `queued` forever (sharded-review H3).
    store = _store()

    class _FailAcquire:
        def __init__(self) -> None:
            self.evict_all_calls = 0

        async def acquire(self, target) -> None:
            raise RuntimeError("generation worker did not become ready")

        async def evict_all(self) -> None:
            self.evict_all_calls += 1

        def notify_idle(self) -> None: ...

    orch = _FailAcquire()
    runner = JobRunner(store, orch, work=lambda r, report: WorkResult("/x.png"))
    rec, _ = store.submit("t2v", Plane.GENERATION, {})

    async def run():
        runner.start()
        await runner.submit(rec)
        await _await_status(store, rec.id, lambda r: r.status in _TERMINAL)
        await runner.stop()

    asyncio.run(run())
    final = store.get(rec.id)
    assert final.status is JobStatus.failed and final.error is not None  # terminal, not stuck queued
    assert final.error.code == "internal_error"
    assert orch.evict_all_calls >= 1  # the slot was released
    assert "failed" in [e.type for e in store.log(rec.id)]


def test_cancel_terminal_job_raises_409_semantics():
    store, orch = _store(), StubOrch()
    runner = JobRunner(store, orch)
    rec, _ = store.submit("t2i", Plane.GENERATION, {})
    store.update(rec.id, start)
    store.update(rec.id, lambda r: succeed(r, "/x.png"))

    with pytest.raises(JobTransitionError):
        asyncio.run(runner.cancel(rec.id))
