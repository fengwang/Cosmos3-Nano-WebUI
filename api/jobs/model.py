"""Immutable job record + pure lifecycle transitions (ACD: Data + Calculations; INV-5).

A `JobRecord` is inert, immutable Data; the lifecycle is pure copy-on-write transitions that validate
the source state — an illegal transition raises `JobTransitionError` (→ 409) rather than silently
mutating. This is the whole INV-5 state machine, host-testable with zero I/O. The wire `Job`
(app.schemas) is a *view* the router derives from a record. Refs: session_6/specs/async-job-model.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from app.schemas import ErrorModel, JobStatus
from orchestrator.planes import Plane

_TERMINAL = frozenset({JobStatus.succeeded, JobStatus.failed, JobStatus.cancelled})


class JobTransitionError(Exception):
    """An illegal lifecycle transition (→ 409). Carries the offending from/to states."""

    def __init__(self, frm: JobStatus, to: JobStatus) -> None:
        self.frm = frm
        self.to = to
        super().__init__(f"illegal job transition {frm.value} -> {to.value}")


@dataclass(frozen=True)
class JobRecord:
    """One async job (immutable Data). ``plane`` tells the runner which GPU plane to acquire."""

    id: str
    mode: str
    plane: Plane
    status: JobStatus
    created_at: str
    params: dict = field(default_factory=dict)  # the submitted mode params the worker needs (S7)
    progress: float = 0.0
    artifact_path: str | None = None
    error: ErrorModel | None = None
    idempotency_fingerprint: str | None = None
    result_meta: dict | None = None  # engine/precision/vram_peak/trajectory_path from the worker (S7)


def _clamp01(value: float) -> float:
    return 0.0 if value < 0 else 1.0 if value > 1 else float(value)


def start(job: JobRecord) -> JobRecord:
    """queued → running (else illegal)."""
    if job.status is not JobStatus.queued:
        raise JobTransitionError(job.status, JobStatus.running)
    return replace(job, status=JobStatus.running)


def progress(job: JobRecord, fraction: float) -> JobRecord:
    """running → running with updated progress in [0, 1] (else illegal)."""
    if job.status is not JobStatus.running:
        raise JobTransitionError(job.status, JobStatus.running)
    return replace(job, progress=_clamp01(fraction))


def succeed(job: JobRecord, artifact_path: str, meta: dict | None = None) -> JobRecord:
    """running → succeeded with the artifact + optional engine result metadata (else illegal)."""
    if job.status is not JobStatus.running:
        raise JobTransitionError(job.status, JobStatus.succeeded)
    return replace(
        job, status=JobStatus.succeeded, artifact_path=artifact_path, progress=1.0, result_meta=meta
    )


def fail(job: JobRecord, error: ErrorModel) -> JobRecord:
    """queued|running → failed with a typed error (terminal jobs cannot fail again)."""
    if job.status in _TERMINAL:
        raise JobTransitionError(job.status, JobStatus.failed)
    return replace(job, status=JobStatus.failed, error=error)


def cancel(job: JobRecord) -> JobRecord:
    """queued|running → cancelled (terminal jobs cannot be cancelled — EC-S4)."""
    if job.status in _TERMINAL:
        raise JobTransitionError(job.status, JobStatus.cancelled)
    return replace(job, status=JobStatus.cancelled)
