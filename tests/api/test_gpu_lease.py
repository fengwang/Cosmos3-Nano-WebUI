"""GPU lease serializes the runner vs. an external holder (the reasoning-stream stand-in) — INV-4.

Spec: session_7/specs/reasoning-endpoint.md — while a reasoning stream holds the GPU lease, a job
waits (no mid-stream eviction). Here an external coroutine holds the lease and the runner's job must
stay queued (and not acquire the plane) until it is released.
"""
from __future__ import annotations

import asyncio
import itertools

from app.schemas import JobStatus
from jobs.runner import JobRunner, WorkResult
from jobs.store import JobStore
from orchestrator.planes import Plane


class _StubOrch:
    def __init__(self) -> None:
        self.acquired: list = []

    async def acquire(self, target) -> None:
        self.acquired.append(target)

    async def evict_all(self) -> None: ...

    def notify_idle(self) -> None: ...


def _store() -> JobStore:
    counter = itertools.count(1)
    return JobStore(id_factory=lambda: f"job{next(counter)}", clock=lambda: "t0")


async def _await(store: JobStore, job_id: str, predicate, timeout: float = 5.0) -> None:
    for _ in range(int(timeout / 0.01)):
        if predicate(store.get(job_id)):
            return
        await asyncio.sleep(0.01)


def test_runner_waits_for_the_gpu_lease():
    store, orch = _store(), _StubOrch()
    lease = asyncio.Lock()
    runner = JobRunner(store, orch, work=lambda rec, report: WorkResult("/x.png"), gpu_lease=lease)
    rec, _ = store.submit("t2i", Plane.GENERATION, {})

    async def run():
        await lease.acquire()  # an external holder stands in for a live reasoning stream
        runner.start()
        await runner.submit(rec)
        await asyncio.sleep(0.1)
        assert store.get(rec.id).status is JobStatus.queued  # blocked on the lease (not started)
        assert orch.acquired == []  # the plane is NOT acquired while the lease is held
        lease.release()
        await _await(store, rec.id, lambda r: r.status is JobStatus.succeeded)
        await runner.stop()

    asyncio.run(run())
    assert store.get(rec.id).status is JobStatus.succeeded
    from orchestrator.residency import ResidencyId
    assert orch.acquired == [ResidencyId(Plane.GENERATION)]  # acquired only after the lease freed


def test_lease_is_mutually_exclusive():
    async def run():
        lease = asyncio.Lock()
        await lease.acquire()
        waiter = asyncio.create_task(lease.acquire())
        await asyncio.sleep(0.05)
        assert not waiter.done()  # a second acquirer cannot proceed while held
        lease.release()
        await waiter  # now it proceeds
        assert lease.locked()
        lease.release()

    asyncio.run(run())
