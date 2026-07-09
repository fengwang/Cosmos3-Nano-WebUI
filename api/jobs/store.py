"""In-memory job store + idempotency registry + event log (Action shell; the INV-5 edge state).

The one edge-mutable holder for jobs (like `ReadinessHolder` for warmup). A `threading.RLock` makes
read-modify-write atomic, because the work thread (progress) and the event loop (routes, cancel) touch
the store concurrently — so a progress update can never resurrect a cancelled job. Idempotency:
same key + same payload fingerprint replays the same job; a different payload is an `IdempotencyConflict`
(→ 409, never a silent overwrite). id/clock are injected for deterministic tests. The event log is
bounded (a deque) with monotonic per-job ids. Refs: session_6/specs/async-job-model.md.
"""
from __future__ import annotations

import hashlib
import json
import threading
import uuid
from collections import deque
from collections.abc import Callable
from datetime import datetime, timezone

from app.schemas import JobStatus
from jobs.events import JobEvent
from jobs.model import JobRecord
from orchestrator.planes import Plane

_EVENT_LOG_BOUND = 1024


class IdempotencyConflict(Exception):
    """An `Idempotency-Key` reused with a different payload (→ 409)."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Idempotency-Key {key!r} reused with a different payload")


class JobNotFound(Exception):
    """An unknown job id (→ 404)."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"job {job_id!r} not found")


def fingerprint(mode: str, params: dict) -> str:
    """Pure: a stable content hash of the canonical (mode, params) payload (the idempotency key)."""
    payload = json.dumps({"mode": mode, "params": params}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStore:
    """The process-local async-job store (single-node lab; jobs need not survive a restart)."""

    def __init__(
        self, *, id_factory: Callable[[], str] | None = None, clock: Callable[[], str] | None = None
    ) -> None:
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._clock = clock or _utcnow_iso
        self._lock = threading.RLock()
        self._jobs: dict[str, JobRecord] = {}
        self._events: dict[str, deque[JobEvent]] = {}
        self._seq: dict[str, int] = {}
        self._idem: dict[str, str] = {}

    def submit(
        self, mode: str, plane: Plane, params: dict, *, key: str | None = None
    ) -> tuple[JobRecord, bool]:
        """Create a queued job (+ a 'queued' event). Returns (record, replayed). Idempotency-aware."""
        fp = fingerprint(mode, params)
        with self._lock:
            if key is not None and key in self._idem:
                existing = self._jobs[self._idem[key]]
                if existing.idempotency_fingerprint == fp:
                    return existing, True
                raise IdempotencyConflict(key)
            job_id = self._id_factory()
            record = JobRecord(
                id=job_id, mode=mode, plane=plane, status=JobStatus.queued, created_at=self._clock(),
                params=dict(params),  # defensive copy: the record carries the params the worker consumes (S7)
                idempotency_fingerprint=fp if key is not None else None,
            )
            self._jobs[job_id] = record
            self._events[job_id] = deque(maxlen=_EVENT_LOG_BOUND)
            self._seq[job_id] = 0
            if key is not None:
                self._idem[key] = job_id
            self._append_event_locked(job_id, JobStatus.queued.value, {})
            return record, False

    def get(self, job_id: str) -> JobRecord:
        """Return the record or raise `JobNotFound` (→ 404)."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise JobNotFound(job_id)
            return record

    def try_get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def put(self, record: JobRecord) -> None:
        with self._lock:
            self._jobs[record.id] = record

    def update(self, job_id: str, fn: Callable[[JobRecord], JobRecord]) -> JobRecord:
        """Atomic read-modify-write under the lock (so concurrent transitions cannot race)."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise JobNotFound(job_id)
            updated = fn(record)
            self._jobs[job_id] = updated
            return updated

    def append_event(self, job_id: str, event_type: str, data: dict | None = None) -> JobEvent:
        with self._lock:
            return self._append_event_locked(job_id, event_type, data or {})

    def _append_event_locked(self, job_id: str, event_type: str, data: dict) -> JobEvent:
        seq = self._seq.get(job_id, 0) + 1
        self._seq[job_id] = seq
        event = JobEvent(id=seq, type=event_type, data=data)
        self._events.setdefault(job_id, deque(maxlen=_EVENT_LOG_BOUND)).append(event)
        return event

    def log(self, job_id: str) -> list[JobEvent]:
        with self._lock:
            if job_id not in self._jobs:
                raise JobNotFound(job_id)
            return list(self._events.get(job_id, ()))
