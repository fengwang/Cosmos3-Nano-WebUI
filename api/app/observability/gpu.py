"""Guarded GPU telemetry (Action: probe NVML → torch → omit; never fabricate).

Emits ``cosmos3_gpu_memory_used_bytes`` / ``cosmos3_gpu_memory_total_bytes`` /
``cosmos3_gpu_utilization_ratio`` only when a probe is available. On the torch-free host loop both probes
fail → the families are **omitted** (honest absence, not zeros) and ``/v1/metrics`` still returns 200. All
heavy imports are deferred into ``gpu_sample`` so this module stays import-light and torch-free.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector

_log = logging.getLogger("cosmos3.metrics.gpu")


@dataclass(frozen=True)
class GpuSample:
    """A single GPU telemetry reading. ``utilization_ratio`` is None when only memory is available (torch)."""

    used_bytes: int
    total_bytes: int
    utilization_ratio: float | None


def gpu_sample() -> GpuSample | None:
    """Probe the GPU: NVML (util + mem) → torch (mem only) → None (no probe). Never raises."""
    try:  # 1) NVML — utilization + memory
        import pynvml  # type: ignore[import-not-found]  # optional GPU dep; absent on the host loop

        pynvml.nvmlInit()
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            return GpuSample(int(mem.used), int(mem.total), float(util.gpu) / 100.0)
        finally:
            pynvml.nvmlShutdown()
    except Exception as exc:  # noqa: BLE001 — fall through to the next probe
        _log.debug("nvml probe unavailable: %s", exc)
    try:  # 2) torch — memory only (no utilization)
        import torch

        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info()
            return GpuSample(int(total - free), int(total), None)
    except Exception as exc:  # noqa: BLE001 — no GPU probe available
        _log.debug("torch mem probe unavailable: %s", exc)
    return None  # 3) omit (honest absence)


class GpuCollector(Collector):
    """A scrape-time collector that yields the GPU families only when a probe returns a sample."""

    def __init__(self, sampler: Callable[[], GpuSample | None] = gpu_sample) -> None:
        self._sampler = sampler

    def collect(self):
        try:
            sample = self._sampler()
        except Exception as exc:  # noqa: BLE001 — telemetry must never break a scrape
            _log.debug("gpu sample failed: %s", exc)
            sample = None
        if sample is None:
            return
        yield GaugeMetricFamily(
            "cosmos3_gpu_memory_used_bytes", "GPU memory used (bytes).", value=float(sample.used_bytes)
        )
        yield GaugeMetricFamily(
            "cosmos3_gpu_memory_total_bytes", "GPU memory total (bytes).", value=float(sample.total_bytes)
        )
        if sample.utilization_ratio is not None:
            yield GaugeMetricFamily(
                "cosmos3_gpu_utilization_ratio", "GPU utilization (0..1).",
                value=float(sample.utilization_ratio),
            )
