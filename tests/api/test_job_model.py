"""Spec: async-job-model — immutable record + pure lifecycle transitions (INV-5)."""
from __future__ import annotations

import pytest

from app.schemas import ErrorModel, JobStatus
from jobs.model import JobRecord, JobTransitionError, cancel, fail, progress, start, succeed
from orchestrator.planes import Plane


def _queued() -> JobRecord:
    return JobRecord(id="j1", mode="t2i", plane=Plane.GENERATION, status=JobStatus.queued, created_at="t0")


def test_queued_starts_then_succeeds_copy_on_write():
    q = _queued()
    running = start(q)
    done = succeed(running, "/srv/artifacts/j1.png")
    assert running.status is JobStatus.running
    assert done.status is JobStatus.succeeded and done.artifact_path == "/srv/artifacts/j1.png"
    assert done.progress == 1.0
    assert q.status is JobStatus.queued  # input unchanged (immutable)


def test_progress_is_clamped_and_requires_running():
    running = start(_queued())
    assert progress(running, 1.5).progress == 1.0
    assert progress(running, -0.2).progress == 0.0
    with pytest.raises(JobTransitionError):
        progress(_queued(), 0.5)  # cannot progress a queued job


def test_cancel_from_queued_and_running_ok_but_terminal_rejected():
    assert cancel(_queued()).status is JobStatus.cancelled
    assert cancel(start(_queued())).status is JobStatus.cancelled
    done = succeed(start(_queued()), "/x.png")
    with pytest.raises(JobTransitionError):
        cancel(done)


def test_fail_from_queued_or_running_but_not_terminal():
    err = ErrorModel(code="internal_error", message="boom")
    assert fail(_queued(), err).status is JobStatus.failed
    assert fail(start(_queued()), err).status is JobStatus.failed
    with pytest.raises(JobTransitionError):
        fail(succeed(start(_queued()), "/x.png"), err)


def test_succeed_requires_running_not_queued():
    with pytest.raises(JobTransitionError):
        succeed(_queued(), "/x.png")


def test_succeed_carries_result_meta_without_mutating_input():
    running = start(_queued())
    meta = {"engine": "diffusers_oracle", "precision": "nvfp4", "vram_peak_bytes": 13_000_000_000}
    done = succeed(running, "/srv/artifacts/j1.mp4", meta)
    assert done.result_meta == meta and done.artifact_path.endswith("j1.mp4")
    assert running.result_meta is None  # input unchanged (copy-on-write)
    assert succeed(start(_queued()), "/x.png").result_meta is None  # default: no meta
