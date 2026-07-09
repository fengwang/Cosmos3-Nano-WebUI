"""Spec: single-gpu-orchestrator — the manager FSM + serialization (stub workers, no GPU) +
the real process-group-kill eviction (a host subprocess, no GPU).

Stub workers let the full residency FSM, evict-before-load, serialization, and failure handling be
host-tested deterministically; one test drives a real `SubprocessPlaneWorker` against an idle
subprocess to prove the `os.killpg` eviction mechanism (the INV-4/RK-15 crux) without the 5090.

S2 extends with checkpoint-label switching (INV-P3-2) and idle-timeout eviction (INV-P3-3).
"""
from __future__ import annotations

import asyncio
import os
import sys
import threading
import time

import pytest

from engines.vllm.loader import ReasonerConfig
from orchestrator.manager import Orchestrator
from orchestrator.planes import Plane, PlaneSpec, ProbeKind, generation_spec, reasoning_spec
from orchestrator.residency import ResidencyId
from orchestrator.worker import SubprocessPlaneWorker, WorkerStartError


# ---- helpers: ResidencyId construction shortcuts --------------------------------
GEN = ResidencyId(Plane.GENERATION)
REASON = ResidencyId(Plane.REASONING)
GEN_FP8 = ResidencyId(Plane.GENERATION, "fp8")
GEN_NVFP4 = ResidencyId(Plane.GENERATION, "nvfp4")


# ---- a recording stub worker + a shared concurrency trace ------------------------------------
class _Trace:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.alive = 0
        self.max_alive = 0
        self.events: list[tuple[str, ResidencyId]] = []

    def record(self, kind: str, target: ResidencyId, delta: int) -> None:
        with self._lock:
            self.alive += delta
            self.max_alive = max(self.max_alive, self.alive)
            self.events.append((kind, target))


class RecordingStubWorker:
    def __init__(self, target: ResidencyId, trace: _Trace, *, ready: bool = True) -> None:
        self._target = target
        self._trace = trace
        self._ready = ready
        self._alive = False

    def start(self) -> None:
        self._alive = True
        self._trace.record("start", self._target, +1)
        time.sleep(0.02)  # widen the window so a serialization bug would surface as max_alive == 2

    def wait_ready(self, timeout: float) -> bool:
        return self._ready

    def is_alive(self) -> bool:
        return self._alive

    def evict(self) -> None:
        if self._alive:
            self._alive = False
            self._trace.record("evict", self._target, -1)


def _orch(trace: _Trace, *, ready: bool = True, idle_timeout: float = 0.0) -> Orchestrator:
    return Orchestrator(
        lambda target: RecordingStubWorker(target, trace, ready=ready),
        post_evict_wait=lambda: True,
        idle_timeout=idle_timeout,
    )


# ---- FSM / serialization (stub) — plane-level -----------------------------------
def test_acquire_evicts_before_loading_a_different_plane():
    trace = _Trace()
    orch = _orch(trace)

    async def run():
        await orch.acquire(REASON)
        await orch.acquire(GEN)
        return orch.resident

    assert asyncio.run(run()) == GEN
    assert trace.events == [
        ("start", REASON),
        ("evict", REASON),
        ("start", GEN),
    ]
    assert trace.max_alive == 1


def test_reacquire_same_plane_is_noop():
    trace = _Trace()
    orch = _orch(trace)

    async def run():
        await orch.acquire(GEN)
        await orch.acquire(GEN)
        return orch.resident

    assert asyncio.run(run()) == GEN
    assert trace.events == [("start", GEN)]


def test_concurrent_acquisitions_never_coreside():
    trace = _Trace()
    orch = _orch(trace)

    async def run():
        await asyncio.gather(orch.acquire(GEN), orch.acquire(REASON))
        return orch.resident

    resident = asyncio.run(run())
    assert trace.max_alive == 1
    assert resident in (GEN, REASON)


def test_ready_failure_raises_and_leaves_no_phantom_residency():
    trace = _Trace()
    orch = _orch(trace, ready=False)

    async def run():
        await orch.acquire(REASON)

    with pytest.raises(WorkerStartError):
        asyncio.run(run())
    assert orch.resident is None
    assert ("evict", REASON) in trace.events


def test_evict_all_frees_the_slot():
    trace = _Trace()
    orch = _orch(trace)

    async def run():
        await orch.acquire(GEN)
        await orch.evict_all()
        return orch.resident

    assert asyncio.run(run()) is None


def test_acquire_aborts_when_vram_not_released():
    trace = _Trace()
    orch = Orchestrator(lambda t: RecordingStubWorker(t, trace), post_evict_wait=lambda: False)

    async def run():
        await orch.acquire(REASON)
        await orch.acquire(GEN)

    with pytest.raises(WorkerStartError):
        asyncio.run(run())
    assert orch.resident is None


# ---- S2: checkpoint-label switching (INV-P3-2) -----------------------------------
def test_checkpoint_switch_evicts_and_reloads():
    trace = _Trace()
    orch = _orch(trace)

    async def run():
        await orch.acquire(GEN_NVFP4)
        await orch.acquire(GEN_FP8)
        return orch.resident

    assert asyncio.run(run()) == GEN_FP8
    assert trace.events == [
        ("start", GEN_NVFP4),
        ("evict", GEN_NVFP4),
        ("start", GEN_FP8),
    ]
    assert trace.max_alive == 1


def test_same_checkpoint_reacquire_is_noop():
    trace = _Trace()
    orch = _orch(trace)

    async def run():
        await orch.acquire(GEN_FP8)
        await orch.acquire(GEN_FP8)
        return orch.resident

    assert asyncio.run(run()) == GEN_FP8
    assert trace.events == [("start", GEN_FP8)]


def test_rapid_triple_checkpoint_switch():
    """NVFP4 → FP8 → NVFP4: three starts, two evictions."""
    trace = _Trace()
    orch = _orch(trace)

    async def run():
        await orch.acquire(GEN_NVFP4)
        await orch.acquire(GEN_FP8)
        await orch.acquire(GEN_NVFP4)
        return orch.resident

    assert asyncio.run(run()) == GEN_NVFP4
    assert trace.events == [
        ("start", GEN_NVFP4),
        ("evict", GEN_NVFP4),
        ("start", GEN_FP8),
        ("evict", GEN_FP8),
        ("start", GEN_NVFP4),
    ]
    assert trace.max_alive == 1


# ---- S2: idle-timeout eviction (INV-P3-3) ----------------------------------------
def test_idle_timer_fires_and_evicts():
    trace = _Trace()
    orch = _orch(trace, idle_timeout=0.1)

    async def run():
        await orch.acquire(GEN_FP8)
        orch.notify_idle()
        await asyncio.sleep(0.3)
        return orch.resident

    assert asyncio.run(run()) is None


def test_idle_timer_cancelled_by_acquire():
    trace = _Trace()
    orch = _orch(trace, idle_timeout=0.2)

    async def run():
        await orch.acquire(GEN_FP8)
        orch.notify_idle()
        await asyncio.sleep(0.05)
        await orch.acquire(GEN_FP8)  # same identity — no-op but cancels timer
        await asyncio.sleep(0.3)
        return orch.resident

    assert asyncio.run(run()) == GEN_FP8


def test_idle_timeout_zero_disables():
    trace = _Trace()
    orch = _orch(trace, idle_timeout=0.0)

    async def run():
        await orch.acquire(GEN_FP8)
        orch.notify_idle()
        await asyncio.sleep(0.2)
        return orch.resident

    assert asyncio.run(run()) == GEN_FP8


def test_idle_timer_skipped_when_lock_held():
    trace = _Trace()
    orch = _orch(trace, idle_timeout=0.05)

    async def run():
        await orch.acquire(GEN_FP8)
        orch.notify_idle()
        async with orch._lock:  # simulate in-flight job holding the lock
            await asyncio.sleep(0.2)  # timer fires while lock held → skipped
        return orch.resident

    assert asyncio.run(run()) == GEN_FP8


def test_evict_all_cancels_idle_timer():
    trace = _Trace()
    orch = _orch(trace, idle_timeout=0.2)

    async def run():
        await orch.acquire(GEN_FP8)
        orch.notify_idle()
        await orch.evict_all()
        await asyncio.sleep(0.4)
        # No error from a stale callback firing after slot is already None
        return orch.resident

    assert asyncio.run(run()) is None


# ---- plane specs -----------------------------------------------------------------
def test_reasoning_spec_uses_vllm_bin_and_health_probe():
    spec = reasoning_spec(
        ReasonerConfig(model_dir="/data/models/Cosmos3-Nano"), vllm_bin="/opt/vllm/bin/vllm", port=8765
    )
    assert spec.argv[0] == "/opt/vllm/bin/vllm" and "serve" in spec.argv
    assert "--port" in spec.argv and "8765" in spec.argv
    assert spec.probe_kind is ProbeKind.HTTP and spec.probe_target.endswith(":8765/health")
    assert spec.strip_parent_env is True
    assert "/data/models/Cosmos3-Nano" in spec.argv


def test_generation_spec_runs_gen_worker_module():
    spec = generation_spec(ready_file="/tmp/ready", python_bin="/usr/bin/python3")
    assert spec.argv == ("/usr/bin/python3", "-m", "orchestrator.gen_worker", "/tmp/ready")
    assert spec.probe_kind is ProbeKind.READY_FILE and spec.probe_target == "/tmp/ready"
    assert spec.env_overrides is None


def test_generation_spec_with_model_dir_sets_env_override():
    spec = generation_spec(ready_file="/tmp/ready", model_dir="/data/models/FP8")
    assert spec.env_overrides == (("COSMOS3_MODEL_DIR", "/data/models/FP8"),)


# ---- the REAL process-group-kill eviction (host subprocess; no GPU) --------------------------
def test_subprocess_worker_ready_file_then_killpg_evicts(tmp_path):
    ready = tmp_path / "ready"
    script = "import sys, time; open(sys.argv[1], 'w').close(); time.sleep(120)"
    spec = PlaneSpec(
        plane=Plane.GENERATION,
        argv=(sys.executable, "-c", script, str(ready)),
        probe_kind=ProbeKind.READY_FILE,
        probe_target=str(ready),
    )
    worker = SubprocessPlaneWorker(spec, log_path=str(tmp_path / "w.log"), poll_interval=0.05)
    worker.start()
    try:
        assert worker.wait_ready(timeout=10) is True
        assert worker.is_alive()
        pgid = os.getpgid(worker._proc.pid)  # type: ignore[union-attr]
    finally:
        worker.evict()
    assert not worker.is_alive()
    with pytest.raises(ProcessLookupError):
        os.killpg(pgid, 0)


def test_stale_ready_file_cleared_on_restart(tmp_path):
    """FA-S2-01 regression: start() must remove a stale ready file so the probe waits for the new one."""
    ready = tmp_path / "ready"
    ready.write_text("ready")

    script = "import sys, time; time.sleep(1); open(sys.argv[1], 'w').close(); time.sleep(120)"
    spec = PlaneSpec(
        plane=Plane.GENERATION,
        argv=(sys.executable, "-c", script, str(ready)),
        probe_kind=ProbeKind.READY_FILE,
        probe_target=str(ready),
    )
    worker = SubprocessPlaneWorker(spec, log_path=str(tmp_path / "w.log"), poll_interval=0.05)
    assert ready.exists()
    worker.start()
    try:
        t0 = time.monotonic()
        assert worker.wait_ready(timeout=10) is True
        elapsed = time.monotonic() - t0
        assert elapsed >= 0.5, f"Probe passed too fast ({elapsed:.2f}s) — stale ready file not cleared"
    finally:
        worker.evict()
