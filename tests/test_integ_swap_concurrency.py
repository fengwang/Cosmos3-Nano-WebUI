"""EV-P5-INTEG-SWAP concurrency (host): the REAL JobRunner + a reasoning-style lease holder +
the REAL Orchestrator (fake workers) share ONE gpu_lease — proving the plane swap is
deadlock/starvation-free and RECOVERS (the second generation job succeeds after reasoning).

This closes the gap the live gate exposed: the earlier swap "failure" was a store-wipe from a
manual api restart (see failure_arbiter.md F2), not the orchestration logic. These tests model the
shared-lease contention the isolated `test_integ_swap_unit` fakes could not. A lease deadlock or
starvation would hang → `asyncio.wait_for` fails the test rather than hanging forever.
"""
from __future__ import annotations

import asyncio
import itertools
import threading

from app.schemas import JobStatus
from jobs.runner import JobRunner, WorkResult
from jobs.store import JobStore
from orchestrator.manager import Orchestrator
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId

REASON = ResidencyId(Plane.REASONING)


class _FakeWorker:
    def __init__(self, plane: Plane, log: list) -> None:
        self._plane, self._log, self._alive = plane, log, False

    def start(self) -> None:
        self._log.append(("start", self._plane))
        self._alive = True

    def wait_ready(self, timeout: float) -> bool:
        return True

    def evict(self) -> None:
        self._log.append(("evict", self._plane))
        self._alive = False

    def is_alive(self) -> bool:
        return self._alive


def _store() -> JobStore:
    counter = itertools.count(1)
    return JobStore(id_factory=lambda: f"job{next(counter)}", clock=lambda: "t0")


async def _await_status(store, job_id, predicate, timeout=5.0):
    for _ in range(int(timeout / 0.01)):
        if predicate(store.get(job_id)):
            return store.get(job_id)
        await asyncio.sleep(0.01)
    return store.get(job_id)


def _orch(log: list) -> Orchestrator:
    return Orchestrator(lambda t: _FakeWorker(t.plane, log), idle_timeout=0, post_evict_wait=lambda: True)


def test_swap_sequence_recovers_second_gen_job():
    """t2v(1) → reasoning → t2v(2): both jobs succeed, reasoning runs, ends resident on GENERATION."""
    log: list = []
    orch, store, lease = _orch(log), _store(), asyncio.Lock()
    runner = JobRunner(store, orch, work=lambda r, rep: (rep(0.5), WorkResult("/tmp/x.mp4", {"engine": "vllm_omni"}))[1],
                       gpu_lease=lease)

    async def reasoning_once():  # models the reasoning route: hold the shared lease around acquire + stream
        async with lease:
            await orch.acquire(REASON)
            await asyncio.sleep(0.02)
            orch.notify_idle()

    async def run():
        runner.start()
        rec1, _ = store.submit("t2v", Plane.GENERATION, {})
        await runner.submit(rec1)
        await _await_status(store, rec1.id, lambda r: r.status is JobStatus.succeeded)
        await reasoning_once()                                    # swap to reasoning (evicts the container)
        rec2, _ = store.submit("t2v", Plane.GENERATION, {})
        await runner.submit(rec2)
        await _await_status(store, rec2.id, lambda r: r.status is JobStatus.succeeded)  # <- must RECOVER
        await runner.stop()
        return store.get(rec1.id), store.get(rec2.id)

    j1, j2 = asyncio.run(asyncio.wait_for(run(), timeout=10))
    assert j1.status is JobStatus.succeeded
    assert j2.status is JobStatus.succeeded                       # recovers after the swap (no starvation)
    assert orch.resident is not None and orch.resident.plane is Plane.GENERATION  # ends on generation
    assert ("evict", Plane.GENERATION) in log                     # gen evicted for reasoning
    assert ("evict", Plane.REASONING) in log                      # reasoning evicted for gen job2


def test_reasoning_requested_during_running_job_blocks_then_swaps_no_deadlock():
    """Reasoning requested WHILE a gen job holds the lease → it correctly WAITS (mutual exclusion),
    then swaps once the job releases; a following gen job still recovers. No deadlock."""
    log: list = []
    orch, store, lease = _orch(log), _store(), asyncio.Lock()
    started, release = threading.Event(), threading.Event()

    def gen_work(rec, report):
        started.set()
        release.wait(5)  # hold the job 'running' (holding the lease) until the test releases it
        return WorkResult("/tmp/x.mp4", {"engine": "vllm_omni"})

    runner = JobRunner(store, orch, work=gen_work, gpu_lease=lease)

    async def reasoning_once():
        async with lease:
            await orch.acquire(REASON)
            await asyncio.sleep(0.01)
            orch.notify_idle()

    async def run():
        runner.start()
        rec1, _ = store.submit("t2v", Plane.GENERATION, {})
        await runner.submit(rec1)
        await asyncio.to_thread(started.wait, 5)                  # job1 running → holds the lease
        reason_task = asyncio.create_task(reasoning_once())       # request reasoning NOW
        await asyncio.sleep(0.05)
        assert not reason_task.done()                             # correctly blocked on the lease (not co-resident)
        release.set()                                            # job1 finishes → releases the lease
        await reason_task                                        # reasoning proceeds (swap) — no deadlock
        rec2, _ = store.submit("t2v", Plane.GENERATION, {})
        await runner.submit(rec2)
        await _await_status(store, rec2.id, lambda r: r.status is JobStatus.succeeded)
        await runner.stop()
        return store.get(rec1.id), store.get(rec2.id)

    j1, j2 = asyncio.run(asyncio.wait_for(run(), timeout=10))
    assert j1.status is JobStatus.succeeded and j2.status is JobStatus.succeeded
