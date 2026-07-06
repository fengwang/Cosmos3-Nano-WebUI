"""Job SSE events + Last-Event-ID replay (ACD: Data + a pure Calculation; RK-09).

A `JobEvent` is inert Data with a monotonic per-job ``id``. `events_since` is a pure selection used
by the SSE endpoint to replay only the events a reconnecting client missed (its ``Last-Event-ID``).
State-change events carry the `JobStatus` value as the type; `PROGRESS`/`HEARTBEAT` are the two
non-status types. Refs: session_6/specs/async-job-model.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field

PROGRESS = "progress"
HEARTBEAT = "heartbeat"


@dataclass(frozen=True)
class JobEvent:
    """One SSE event (inert Data). ``id`` is monotonic within a job (the SSE ``id:`` field)."""

    id: int
    type: str
    data: dict = field(default_factory=dict)


def events_since(log: list[JobEvent], last_event_id: int | None) -> list[JobEvent]:
    """Pure: the events strictly after ``last_event_id`` (all events when it is ``None``)."""
    if last_event_id is None:
        return list(log)
    return [event for event in log if event.id > last_event_id]
