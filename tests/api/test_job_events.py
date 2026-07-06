"""Spec: async-job-model — SSE event log replay (RK-09 Last-Event-ID)."""
from __future__ import annotations

from jobs.events import HEARTBEAT, PROGRESS, JobEvent, events_since


def _log() -> list[JobEvent]:
    return [
        JobEvent(1, "queued"),
        JobEvent(2, "running"),
        JobEvent(3, PROGRESS, {"progress": 0.5}),
        JobEvent(4, HEARTBEAT),
        JobEvent(5, PROGRESS, {"progress": 0.9}),
        JobEvent(6, "succeeded"),
    ]


def test_events_since_replays_only_missed():
    got = events_since(_log(), last_event_id=3)
    assert [e.id for e in got] == [4, 5, 6]


def test_events_since_none_returns_whole_log():
    assert [e.id for e in events_since(_log(), None)] == [1, 2, 3, 4, 5, 6]


def test_events_since_at_tail_returns_empty():
    assert events_since(_log(), 6) == []
