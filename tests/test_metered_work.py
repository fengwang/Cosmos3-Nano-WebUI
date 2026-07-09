"""S11: metered_work — job duration + terminal-outcome counting, re-raising on failure.

Spec: app-layer-instrumentation (job-work). The wrapper must be transparent: it passes the inner result
through on success and re-raises the inner exception on failure (so the frozen runner's handling is preserved).
"""
from __future__ import annotations

import pytest

from app.observability.instruments import metered_work
from app.observability.metrics import build_metrics


class _Rec:
    mode = "t2v"


def _dur_count(reg, outcome):
    return reg.get_sample_value("cosmos3_job_duration_seconds_count", {"mode": "t2v", "outcome": outcome})


def _terminal(reg, outcome):
    return reg.get_sample_value("cosmos3_job_terminal_total", {"mode": "t2v", "outcome": outcome})


def test_success_timed_counted_and_result_passed_through():
    metrics, reg = build_metrics()
    sentinel = object()
    work = metered_work(lambda rec, report: sentinel, metrics)
    assert work(_Rec(), lambda f: None) is sentinel
    assert _dur_count(reg, "succeeded") == 1.0
    assert _terminal(reg, "succeeded") == 1.0
    assert _terminal(reg, "failed") is None


def test_failure_counted_and_reraised():
    metrics, reg = build_metrics()

    def boom(rec, report):
        raise ValueError("engine boom")

    work = metered_work(boom, metrics)
    with pytest.raises(ValueError, match="engine boom"):
        work(_Rec(), lambda f: None)
    assert _terminal(reg, "failed") == 1.0
    assert _dur_count(reg, "failed") == 1.0
    assert _terminal(reg, "succeeded") is None
