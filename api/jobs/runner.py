"""The single serialized async job runner (Action shell; INV-5 + the RK-03/RK-15 serialization).

One asyncio task drains the queue **one job at a time**: acquire the orchestrator slot for the job's
plane (evict-before-load), run the **injected** ``work`` in a thread (a deterministic stub in S6; the
real engine call in S7), stream progress events, write the artifact, and reach a terminal state — or
fail with a typed error. Because exactly one job is processed at a time, two heavy jobs never co-grab
the GPU. Cancellation is race-safe: a `cancel` adds the id to a set BEFORE evicting the worker, so the
loop's success/fail branches (guarded by that set, with no `await` between the check and `start`) never
resurrect a cancelled job, and a running job's GPU slot is provably freed. Refs:
session_6/specs/async-job-model.md.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from app.schemas import ErrorModel, JobStatus
from jobs import artifacts
from jobs.events import PROGRESS
from jobs.model import JobRecord, JobTransitionError, cancel, fail, progress, start, succeed
from jobs.store import JobStore
from orchestrator.manager import Orchestrator
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId

ProgressCb = Callable[[float], None]


@dataclass(frozen=True)
class WorkResult:
    """What a job's ``work`` produced (inert Data): the artifact path + engine result metadata.

    ``meta`` carries the verified ``{engine, precision, vram_peak_bytes, trajectory_path}`` the worker
    reports (S7); the S6 stub returns an empty meta. Replaces the old bare ``str`` return — no compat shim.
    """

    artifact_path: str
    meta: dict = field(default_factory=dict)


Work = Callable[[JobRecord, ProgressCb], WorkResult]  # runs the job; returns the artifact + meta

_TERMINAL = frozenset({JobStatus.succeeded, JobStatus.failed, JobStatus.cancelled})
_log = logging.getLogger("cosmos3.jobs")


def default_stub_work(record: JobRecord, report: ProgressCb) -> WorkResult:
    """S6 default / host fallback: one progress tick + the deterministic stub artifact (no engine, empty meta)."""
    report(0.5)
    return WorkResult(artifacts.write_stub(record.id), {})


class JobRunner:
    """Drains the job queue serially, acquiring the single GPU slot per job."""

    def __init__(
        self, store: JobStore, orchestrator: Orchestrator, work: Work = default_stub_work,
        *, gpu_lease: asyncio.Lock | None = None,
    ) -> None:
        self._store = store
        self._orch = orchestrator
        self._work = work
        # The shared GPU lease (S7): held around each job's GPU phase so a reasoning stream cannot
        # evict the plane mid-job (and vice versa) — preserves "one heavy plane, serialized" (INV-4).
        # Injected from the app so the runner and the reasoning route share ONE lease; a private lock
        # (jobs already serialize via the single drain loop) when standalone.
        self._lease = gpu_lease or asyncio.Lock()
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._cancelled: set[str] = set()
        self._current: str | None = None
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        """Action: launch the drain loop (idempotent)."""
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Action: stop the drain loop (shutdown)."""
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def submit(self, record: JobRecord) -> None:
        """Action: enqueue a queued job for processing."""
        await self._queue.put(record.id)

    @staticmethod
    def _error_of(exc: Exception) -> ErrorModel:
        """Map a work failure to a typed ErrorModel: honor an exception-carried ``code`` (the worker's
        ``{ok:false, code}``), else ``internal_error``. Duck-typed so the runner stays engine-agnostic."""
        code = getattr(exc, "code", None)
        return ErrorModel(code=code if isinstance(code, str) else "internal_error", message=str(exc))

    def _fail(self, job_id: str, exc: Exception) -> None:
        """Transition a job to failed with a typed error + a failed event (the terminal-state guarantee)."""
        error = self._error_of(exc)
        self._store.update(job_id, lambda r: fail(r, error))
        self._store.append_event(job_id, JobStatus.failed.value, {"message": error.message})

    def _progress_cb(self, job_id: str) -> ProgressCb:
        def report(fraction: float) -> None:
            updated = self._store.update(
                job_id, lambda r: progress(r, fraction) if r.status is JobStatus.running else r
            )
            if updated.status is JobStatus.running:
                self._store.append_event(job_id, PROGRESS, {"progress": updated.progress})

        return report

    async def _loop(self) -> None:
        while True:
            job_id = await self._queue.get()
            try:
                await self._process(job_id)
            except Exception:  # noqa: BLE001 — one job's failure must never kill the runner loop
                _log.exception("runner crashed processing job %s", job_id)
            finally:
                self._queue.task_done()

    async def _process(self, job_id: str) -> None:
        if job_id in self._cancelled:  # cancelled before it was dequeued
            self._cancelled.discard(job_id)
            return
        record = self._store.try_get(job_id)
        if record is None or record.status is not JobStatus.queued:
            return  # unknown, or already cancelled-while-queued
        self._current = job_id
        try:
            async with self._lease:  # hold the GPU lease across acquire→work so no stream evicts mid-job
                try:
                    checkpoint = record.params.get("checkpoint") if record.plane is Plane.GENERATION else None
                    await self._orch.acquire(ResidencyId(record.plane, checkpoint))
                except Exception as exc:  # noqa: BLE001 — acquire failed (worker not ready / OOM): fail, never hang
                    if job_id not in self._cancelled:
                        self._fail(job_id, exc)  # INV-5: the job MUST reach a terminal state, not stay queued
                        await self._orch.evict_all()
                    return
                if job_id in self._cancelled:  # cancelled during acquire
                    return
                # No `await` between this check and `start` → atomic w.r.t. the cancel coroutine.
                self._store.update(job_id, start)
                self._store.append_event(job_id, JobStatus.running.value, {})
                try:
                    result = await asyncio.to_thread(
                        self._work, self._store.get(job_id), self._progress_cb(job_id)
                    )
                except Exception as exc:  # noqa: BLE001 — surface as a failed job (unless cancelled mid-flight)
                    if job_id not in self._cancelled:
                        self._fail(job_id, exc)
                        await self._orch.evict_all()  # a failed job may have left the plane dirty — release it
                else:
                    if job_id not in self._cancelled:
                        self._store.update(job_id, lambda r: succeed(r, result.artifact_path, result.meta))
                        self._store.append_event(job_id, JobStatus.succeeded.value, dict(result.meta))
        finally:
            self._cancelled.discard(job_id)
            self._current = None
            self._orch.notify_idle()

    async def cancel(self, job_id: str) -> JobRecord:
        """Cancel a queued (dequeue) or running (evict the slot) job. Terminal → `JobTransitionError` (409)."""
        record = self._store.get(job_id)  # JobNotFound → 404
        if record.status in _TERMINAL:
            raise JobTransitionError(record.status, JobStatus.cancelled)  # → 409
        self._cancelled.add(job_id)  # set BEFORE the await so the loop cannot resurrect this job
        if record.status is JobStatus.running and self._current == job_id:
            await self._orch.evict_all()  # kill the worker → GPU slot provably freed (EC-S4)
        updated = self._store.update(job_id, cancel)
        self._store.append_event(job_id, JobStatus.cancelled.value, {})
        return updated
