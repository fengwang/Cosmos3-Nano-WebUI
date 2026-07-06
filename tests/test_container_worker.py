"""Spec: container-plane-lifecycle — DockerCliController + ContainerPlaneWorker.

Host-testable via a fake controller + injected health probe + injected clock — no docker, no GPU.
"""
from __future__ import annotations

import inspect
import re

from orchestrator.container import ContainerPlaneWorker, DockerCliController
from orchestrator.planes import container_generation_spec

_SPEC = container_generation_spec(base_url="http://vllm-omni:8000")


class _FakeController:
    def __init__(self, *, running=False):
        self.running = running
        self.calls: list[str] = []

    def start(self):
        self.calls.append("start")
        self.running = True

    def stop(self):
        self.calls.append("stop")
        self.running = False

    def is_running(self):
        return self.running


class _FakeRun:
    """Records argv for DockerCliController; returns a scripted inspect result."""

    def __init__(self, *, running="true", returncode=0):
        self.argv: list[list[str]] = []
        self._running = running
        self._rc = returncode

    def __call__(self, argv, **kwargs):
        self.argv.append(argv)

        class _R:
            returncode = self._rc
            stdout = self._running + "\n"
        return _R()


# ── DockerCliController: fixed name + verbs, no request data (INV-8 control plane) ──

def test_docker_controller_uses_only_fixed_name_and_verbs():
    run = _FakeRun()
    c = DockerCliController("cosmos3-vllm-omni", run=run)
    c.start()
    c.stop()
    c.is_running()
    assert run.argv[0] == ["docker", "start", "cosmos3-vllm-omni"]
    assert run.argv[1] == ["docker", "stop", "cosmos3-vllm-omni"]
    assert run.argv[2][:3] == ["docker", "inspect", "-f"]
    # every argv token is a fixed verb/flag or the configured name — never request-derived
    flat = [tok for call in run.argv for tok in call]
    assert all(tok in {"docker", "start", "stop", "inspect", "-f", "{{.State.Running}}",
                       "cosmos3-vllm-omni"} for tok in flat)


def test_docker_controller_is_running_parses_true():
    assert DockerCliController("n", run=_FakeRun(running="true")).is_running() is True
    assert DockerCliController("n", run=_FakeRun(running="false")).is_running() is False
    assert DockerCliController("n", run=_FakeRun(running="", returncode=1)).is_running() is False


# ── ContainerPlaneWorker: PlaneWorker lifecycle ──

def _worker(controller, probe, *, clock=None):
    ticks = iter(clock or [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    return ContainerPlaneWorker(_SPEC, controller, probe=probe, poll_interval=0.0,
                                now=lambda: next(ticks), sleep=lambda _s: None)


def test_ready_when_health_200():
    ctrl = _FakeController(running=True)
    w = _worker(ctrl, probe=lambda _url: True)
    w.start()  # idempotent w/ already-running fake
    assert w.wait_ready(timeout=10.0) is True
    assert w.is_alive() is True


def test_flapping_health_still_becomes_ready():
    ctrl = _FakeController(running=True)
    probes = iter([False, False, True])  # 503, 503, 200
    w = _worker(ctrl, probe=lambda _url: next(probes))
    assert w.wait_ready(timeout=10.0) is True


def test_container_exit_fails_ready_fast():
    ctrl = _FakeController(running=False)  # never running
    w = _worker(ctrl, probe=lambda _url: True)
    assert w.wait_ready(timeout=10.0) is False


def test_evict_stops_container_and_is_idempotent():
    ctrl = _FakeController(running=True)
    w = _worker(ctrl, probe=lambda _url: True)
    w.evict()
    assert ctrl.running is False and "stop" in ctrl.calls
    w.evict()  # idempotent on an already-stopped container — must not raise
    assert w.is_alive() is False


def test_start_brings_container_up():
    ctrl = _FakeController(running=False)
    w = _worker(ctrl, probe=lambda _url: True)
    w.start()
    assert ctrl.running is True and "start" in ctrl.calls


def test_container_module_has_no_toplevel_torch_import():
    # host-loop guarantee: assert by source (robust in any venv — a bare import cannot prove
    # absence when torch is already resident from the oracle extra).
    import orchestrator.container as cmod
    src = inspect.getsource(cmod)
    assert not re.search(r"^\s*(import torch|from torch)", src, re.M)
