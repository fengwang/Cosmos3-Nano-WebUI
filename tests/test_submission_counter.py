"""S11: submission counter — cosmos3_job_submitted_total{mode} counts NEW jobs, not idempotent replays.

Spec: app-layer-instrumentation (submission counter). Tested at the shared choke point ``submit_and_enqueue``
(generation/action/jobs all route through it), so one assertion covers every submission path.
"""
from __future__ import annotations

import asyncio

from app.jobs_router import submit_and_enqueue
from app.observability.metrics import build_metrics
from app.schemas import JobSubmit
from jobs.runner import JobRunner
from jobs.store import JobStore
from orchestrator.manager import Orchestrator


def _runner(store: JobStore) -> JobRunner:
    # Not started: submit() only enqueues; the factory is never called (we never acquire).
    return JobRunner(store, Orchestrator(lambda plane: None))


def test_submission_counts_new_job_by_mode():
    metrics, reg = build_metrics()
    store = JobStore()
    asyncio.run(
        submit_and_enqueue(JobSubmit(mode="t2v", params={"prompt": "x"}), store, _runner(store), metrics=metrics)
    )
    assert reg.get_sample_value("cosmos3_job_submitted_total", {"mode": "t2v"}) == 1.0


def test_idempotent_replay_does_not_double_count():
    metrics, reg = build_metrics()
    store = JobStore()
    runner = _runner(store)
    submit = JobSubmit(mode="t2v", params={"prompt": "x"})
    asyncio.run(submit_and_enqueue(submit, store, runner, metrics=metrics, idempotency_key="k1"))
    asyncio.run(submit_and_enqueue(submit, store, runner, metrics=metrics, idempotency_key="k1"))
    assert reg.get_sample_value("cosmos3_job_submitted_total", {"mode": "t2v"}) == 1.0  # replay not counted
