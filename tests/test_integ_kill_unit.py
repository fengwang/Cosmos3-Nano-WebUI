"""EV-P5-INTEG-KILL (host, stubbed docker): killing the gen container mid-job fails cleanly.

Drives the real JobRunner with vllm_omni_work bound to a transport that dies mid-poll (the container
was killed). Asserts: the job reaches `failed` with an error surfaced, the GPU slot is released
(evict_all), no hang, and NO artifact is written for the job id (no artifact-dir contamination).
Spec: integration-gates-and-smokes; contract adversarial_cases (kill mid-job).
"""
from __future__ import annotations

import asyncio
import itertools
import os

from app.schemas import JobStatus
from engines.vllm_omni import work as vw
from jobs.runner import JobRunner
from jobs.store import JobStore
from orchestrator.planes import Plane

_TERMINAL = {JobStatus.succeeded, JobStatus.failed, JobStatus.cancelled}


class _StubOrch:
    def __init__(self) -> None:
        self.evict_all_calls = 0

    async def acquire(self, target) -> None: ...

    async def evict_all(self) -> None:
        self.evict_all_calls += 1

    def notify_idle(self) -> None: ...


class _KilledTransport:
    """Container killed mid-job: submit ok, one poll ok, then the connection dies (never downloads)."""

    def __init__(self) -> None:
        self._polls = 0

    def post_form(self, path, form):
        return {"id": "vid-1", "status": "queued"}

    def get_json(self, path):
        self._polls += 1
        if self._polls == 1:
            return 200, {"status": "in_progress", "progress": 10}
        raise ConnectionError("container gone")  # killed mid-job

    def get_bytes(self, path):
        raise AssertionError("must not download content after the container is killed")

    def delete(self, path): ...


async def _await(store, job_id, predicate, timeout=5.0):
    for _ in range(int(timeout / 0.01)):
        if predicate(store.get(job_id)):
            return store.get(job_id)
        await asyncio.sleep(0.01)
    return store.get(job_id)


def test_kill_mid_job_fails_cleanly_and_writes_no_artifact(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    counter = itertools.count(1)
    store = JobStore(id_factory=lambda: f"job{next(counter)}", clock=lambda: "t0")
    orch = _StubOrch()
    killed = _KilledTransport()

    def work(rec, report):
        return vw.vllm_omni_work(rec, report, transport=killed)

    runner = JobRunner(store, orch, work=work)
    rec, _ = store.submit("t2v", Plane.GENERATION,
                          {"prompt": "x", "width": 640, "height": 480, "num_frames": 57})

    async def run():
        runner.start()
        await runner.submit(rec)
        await _await(store, rec.id, lambda r: r.status in _TERMINAL)
        await runner.stop()

    asyncio.run(run())
    final = store.get(rec.id)
    assert final.status is JobStatus.failed and final.error is not None  # error surfaced to the UI
    assert orch.evict_all_calls >= 1                                     # GPU slot released (no leak)
    assert os.listdir(str(tmp_path)) == []                              # no artifact-dir contamination
    assert "failed" in [e.type for e in store.log(rec.id)]
