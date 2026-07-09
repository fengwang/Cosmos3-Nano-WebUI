"""Metric family definitions + the render Calculation (Data + a pure exposition function).

The event-driven families (Counters/Histograms updated by the middleware + the metered wrappers) are built
into an injected ``CollectorRegistry``. Scrape-time *gauges* (queue depth, resident plane, GPU) are added by
``collectors.register_collectors``. Namespaced ``cosmos3_*``. Torch-free.
"""
from __future__ import annotations

from dataclasses import dataclass

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

# Bucket families (seconds). HTTP: ms..10s (202-accept + artifact fetch + the reasoning stream open).
# Jobs: 0.5s..10min (generation is minutes). Plane acquire: 1s..5min (a cold vLLM/oracle load is tens of
# seconds). Chosen conservatively; the report records the final buckets after the first warm live numbers.
_HTTP_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
_JOB_BUCKETS = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0, 300.0, 600.0)
_ACQUIRE_BUCKETS = (1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0, 180.0, 300.0)


@dataclass(frozen=True)
class Metrics:
    """The event-driven metric handles updated by the middleware + the metered wrappers (the Action edges)."""

    http_requests: Counter  # cosmos3_http_requests_total{method,route,status}
    http_duration: Histogram  # cosmos3_http_request_duration_seconds{method,route}
    job_submitted: Counter  # cosmos3_job_submitted_total{mode}
    job_terminal: Counter  # cosmos3_job_terminal_total{mode,outcome}
    job_duration: Histogram  # cosmos3_job_duration_seconds{mode,outcome}
    plane_acquire: Histogram  # cosmos3_plane_acquire_duration_seconds{plane,transition}


def build_metrics(registry: CollectorRegistry | None = None) -> tuple[Metrics, CollectorRegistry]:
    """Build the metric families into a fresh (or given) private registry. Returns (handles, registry)."""
    reg = registry if registry is not None else CollectorRegistry()
    metrics = Metrics(
        http_requests=Counter(
            "cosmos3_http_requests", "HTTP requests by method, matched route, and status.",
            ["method", "route", "status"], registry=reg,
        ),
        http_duration=Histogram(
            "cosmos3_http_request_duration_seconds", "HTTP request duration (seconds).",
            ["method", "route"], buckets=_HTTP_BUCKETS, registry=reg,
        ),
        job_submitted=Counter(
            "cosmos3_job_submitted", "Async jobs accepted (202) by mode.", ["mode"], registry=reg,
        ),
        job_terminal=Counter(
            "cosmos3_job_terminal", "Async jobs reaching a terminal state by mode and outcome.",
            ["mode", "outcome"], registry=reg,
        ),
        job_duration=Histogram(
            "cosmos3_job_duration_seconds", "Server-side job-work duration (seconds).",
            ["mode", "outcome"], buckets=_JOB_BUCKETS, registry=reg,
        ),
        plane_acquire=Histogram(
            "cosmos3_plane_acquire_duration_seconds",
            "Orchestrator plane acquisition — model-load + swap — duration (seconds).",
            ["plane", "transition"], buckets=_ACQUIRE_BUCKETS, registry=reg,
        ),
    )
    return metrics, reg


def render(registry: CollectorRegistry) -> tuple[bytes, str]:
    """Calculation: the Prometheus exposition bytes + content type for the registry's current state."""
    return generate_latest(registry), CONTENT_TYPE_LATEST
