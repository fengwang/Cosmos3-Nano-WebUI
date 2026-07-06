"""Out-of-process plane workers + process-group-kill eviction (Action shell; the INV-4 mechanism).

A plane worker is a subprocess **group** (`start_new_session=True`), so eviction can reap the whole
group — including vLLM's separate EngineCore child (a parent-only kill would orphan it holding the KV
cache, RK-15). This is the only mechanism S5 *proved* frees VRAM (FA-2). Readiness is probed per the
spec (HTTP /health for vLLM; a touched ready-file for the generation worker). `wait_vram_below`
reuses the frozen S5 GPU-wide sampler so the manager never loads a plane on top of an unreleased KV
cache. Refs: session_6/specs/single-gpu-orchestrator.md; tests/equivalence/test_coresidency_handoff_gpu.py.
"""
from __future__ import annotations

import os
import signal
import subprocess
import time
import urllib.request
from typing import Protocol

from engines.vllm.coresidency import gpu_memory_used_bytes
from orchestrator.planes import PlaneSpec, ProbeKind

# Parent-venv vars stripped when a worker runs in its OWN venv (vLLM) so its torch/libs win.
_PARENT_ENV_LEAK = ("PYTHONPATH", "VIRTUAL_ENV", "LD_LIBRARY_PATH")


class WorkerStartError(RuntimeError):
    """Raised when a worker process dies or never becomes ready (the acquisition must fail)."""


class PlaneWorker(Protocol):
    """The minimal lifecycle the manager drives (the real impl is `SubprocessPlaneWorker`; tests inject a stub)."""

    def start(self) -> None: ...
    def wait_ready(self, timeout: float) -> bool: ...
    def evict(self) -> None: ...
    def is_alive(self) -> bool: ...


def _http_ok(url: str, timeout: float = 5.0) -> bool:
    """Action: True iff ``url`` answers HTTP 200 (the vLLM readiness probe)."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 — fixed localhost health URL
            return resp.status == 200
    except Exception:  # noqa: BLE001 — any error == not ready yet
        return False


class SubprocessPlaneWorker:
    """Drives one plane as a killable subprocess group (Action shell)."""

    def __init__(self, spec: PlaneSpec, *, log_path: str | None = None, poll_interval: float = 2.0) -> None:
        self._spec = spec
        self._log_path = log_path or f"/tmp/cosmos3_worker_{spec.plane.value}.log"
        self._poll = poll_interval
        self._proc: subprocess.Popen | None = None

    def _env(self) -> dict[str, str] | None:
        overrides = dict(self._spec.env_overrides) if self._spec.env_overrides else None
        if not self._spec.strip_parent_env and not overrides:
            return None  # inherit (the generation worker needs PYTHONPATH to import engines/orchestrator)
        env = dict(os.environ)
        if self._spec.strip_parent_env:
            for var in _PARENT_ENV_LEAK:
                env.pop(var, None)
        if overrides:
            env.update(overrides)
        return env

    def start(self) -> None:
        """Action: launch the worker as a new process group, logging to a per-plane file."""
        if self._spec.probe_kind is ProbeKind.READY_FILE:
            try:
                os.unlink(self._spec.probe_target)
            except FileNotFoundError:
                pass
        log = open(self._log_path, "w")  # noqa: SIM115 — handed to the child; closed on evict
        self._log = log
        self._proc = subprocess.Popen(
            list(self._spec.argv), start_new_session=True, stdout=log, stderr=subprocess.STDOUT, env=self._env()
        )

    def wait_ready(self, timeout: float) -> bool:
        """Action: block until the probe passes, the process dies, or ``timeout`` elapses."""
        proc = self._proc
        if proc is None:
            return False
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if proc.poll() is not None:  # died early — don't poll for the full timeout
                return False
            if self._probe():
                return True
            time.sleep(self._poll)
        return self._probe()

    def _probe(self) -> bool:
        if self._spec.probe_kind is ProbeKind.HTTP:
            return _http_ok(self._spec.probe_target)
        return os.path.exists(self._spec.probe_target)

    def is_alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def evict(self) -> None:
        """Action: kill the whole process GROUP (SIGTERM→SIGKILL) — reaps the EngineCore child (RK-15).

        Signals the group id directly (== the child pid; ``start_new_session`` makes it the leader), and
        does NOT short-circuit on ``poll()`` — so a still-alive group member (e.g. an EngineCore
        grandchild) is signalled even if the launcher parent already exited.
        """
        proc = self._proc
        if proc is None:
            self._close_log()
            return
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                break  # the group is already gone
            try:
                proc.wait(timeout=30)
                break
            except subprocess.TimeoutExpired:
                continue
        self._close_log()

    def _close_log(self) -> None:
        log = getattr(self, "_log", None)
        if log is not None and not log.closed:
            log.close()


def wait_vram_below(threshold_bytes: int, timeout: float, *, device_index: int = 0, poll: float = 2.0) -> bool:
    """Action: poll GPU-wide VRAM (nvidia-smi) until it drops to/below ``threshold`` or ``timeout`` elapses."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if gpu_memory_used_bytes(device_index) <= threshold_bytes:
            return True
        time.sleep(poll)
    return gpu_memory_used_bytes(device_index) <= threshold_bytes
