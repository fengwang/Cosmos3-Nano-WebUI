"""S11: /v1/metrics exposition — content type, parseable, minimum set present, GPU omitted on the host loop.

Spec: metrics-endpoint (endpoint, minimum dashboard set). Deterministic-check #1 (the minimum set).
"""
from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client.parser import text_string_to_metric_families

from app.observability.collectors import register_collectors
from app.observability.metrics import build_metrics, render
from jobs.store import JobStore

_MINIMUM_FAMILIES = (
    "cosmos3_http_requests",  # request rate + errors (status label)
    "cosmos3_http_request_duration_seconds",  # latency by route
    "cosmos3_job_submitted",  # job rate
    "cosmos3_job_terminal",  # cancel/error rate (outcome label)
    "cosmos3_job_duration_seconds",  # job latency
    "cosmos3_plane_acquire_duration_seconds",  # model-load + swap duration
    "cosmos3_jobs",  # queue depth + state
    "cosmos3_plane_resident",  # which plane is hot
)


class _StubOrch:
    resident = None


def _exercise(metrics) -> None:
    metrics.http_requests.labels("GET", "/v1/health/live", "200").inc()
    metrics.http_duration.labels("GET", "/v1/health/live").observe(0.01)
    metrics.job_submitted.labels("t2v").inc()
    metrics.job_terminal.labels("t2v", "succeeded").inc()
    metrics.job_duration.labels("t2v", "succeeded").observe(1.0)
    metrics.plane_acquire.labels("generation", "cold_load").observe(5.0)


def test_exposition_content_type_and_minimum_set():
    metrics, reg = build_metrics()
    register_collectors(reg, JobStore(), _StubOrch(), gpu_sampler=lambda: None)
    _exercise(metrics)

    body, ctype = render(reg)
    assert ctype == CONTENT_TYPE_LATEST
    assert ctype.startswith("text/plain")

    families = {fam.name for fam in text_string_to_metric_families(body.decode())}
    for fam in _MINIMUM_FAMILIES:
        assert fam in families, f"missing minimum family {fam}; have {sorted(families)}"


def test_gpu_families_absent_on_host_loop():
    _, reg = build_metrics()
    register_collectors(reg, JobStore(), _StubOrch(), gpu_sampler=lambda: None)
    body, _ = render(reg)
    families = {fam.name for fam in text_string_to_metric_families(body.decode())}
    assert not any(fam.startswith("cosmos3_gpu_") for fam in families)
