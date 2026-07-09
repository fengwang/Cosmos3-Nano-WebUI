"""S11 observability — Prometheus metrics for the api (instrument the frozen core from the app edge).

All families are namespaced ``cosmos3_*`` (distinct from the model-quality ``*_metrics``). Metrics are built
per-app into a private ``CollectorRegistry`` (injected, never a module global), mirroring the codebase's
``ReadinessHolder``/``JobStore`` edge-state discipline so each ``create_app()`` gets isolated metrics. This
package imports torch-free; the GPU probe defers its heavy import.
"""
from __future__ import annotations

from app.observability.collectors import StateCollector, register_collectors
from app.observability.gpu import GpuCollector, GpuSample, gpu_sample
from app.observability.metrics import Metrics, build_metrics, render

__all__ = [
    "Metrics",
    "build_metrics",
    "render",
    "StateCollector",
    "register_collectors",
    "GpuCollector",
    "GpuSample",
    "gpu_sample",
]
