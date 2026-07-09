"""The vllm-omni container generation plane — a `PlaneWorker` backed by a docker container (S4).

The container plugs into the existing single-slot Orchestrator FSM unchanged: `start` brings the
container up, `wait_ready` polls the server readiness endpoint, **`evict` stops the container (frees
its VRAM)**, and `is_alive` reports whether it is running. Because the orchestrator runs
evict-before-load, coarse mutual exclusion (INV-P5-2 — gen container XOR reasoning worker) is a
consequence of `evict`=stop, with no change to `manager.py`/`residency.py`.

All docker access is confined to `DockerCliController`, which acts only on a fixed operator-configured
container name using fixed verbs via an argv list (no shell, no request-derived input) — the accepted
docker-socket privilege (R-15) with INV-8 discipline extended to the control plane. The controller,
health probe, and clock are injected, so the whole lifecycle is host-testable without docker or a GPU.
Refs: session_4/specs/container-plane-lifecycle.md; design.md D-1/D-6/D-8.
"""
from __future__ import annotations

import logging
import subprocess
import time
from collections.abc import Callable
from typing import Protocol

from orchestrator.planes import PlaneSpec
from orchestrator.worker import _http_ok

_log = logging.getLogger("cosmos3.orchestrator")


class ContainerController(Protocol):
    """The minimal container lifecycle the worker drives (real impl: `DockerCliController`; tests fake it)."""

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def is_running(self) -> bool: ...


class DockerCliController:
    """Controls one container by a FIXED operator-configured name (R-15 confinement; INV-8 control plane).

    All docker access in the api is confined here: fixed verbs (start / stop / inspect) invoked as an
    argv list (no shell), acting ONLY on ``name`` — never any request-derived value. `stop` is
    idempotent (``check=False``) so stopping an already-stopped/absent container never raises.
    """

    def __init__(self, name: str, *, run: Callable[..., object] = subprocess.run) -> None:
        self._name = name
        self._run = run

    def start(self) -> None:
        self._run(["docker", "start", self._name], check=True, capture_output=True)  # noqa: S603,S607 — fixed argv

    def stop(self) -> None:
        self._run(["docker", "stop", self._name], check=False, capture_output=True)  # noqa: S603,S607 — idempotent

    def is_running(self) -> bool:
        result = self._run(  # noqa: S603,S607 — fixed argv; name is operator config, never request data
            ["docker", "inspect", "-f", "{{.State.Running}}", self._name],
            capture_output=True, text=True,
        )
        return getattr(result, "returncode", 1) == 0 and (getattr(result, "stdout", "") or "").strip() == "true"


class ContainerPlaneWorker:
    """Drives the vllm-omni container as an orchestrator `PlaneWorker` (start/wait_ready/evict/is_alive)."""

    def __init__(
        self, spec: PlaneSpec, controller: ContainerController, *,
        probe: Callable[[str], bool] | None = None, poll_interval: float = 2.0,
        now: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._spec = spec
        self._controller = controller
        self._probe = probe or _http_ok
        self._poll = poll_interval
        self._now = now
        self._sleep = sleep

    def start(self) -> None:
        """Action: bring the container up (a failure raises → the acquisition fails, never a half-load)."""
        self._controller.start()

    def wait_ready(self, timeout: float) -> bool:
        """Action: poll the server readiness endpoint until a stable 200, the container exits, or timeout.

        A transient non-200 during cold start (PTX JIT / model load) is treated as "not ready yet"
        (flap-tolerant, R-07); the wait fails fast only if the container is no longer running.
        """
        deadline = self._now() + timeout
        while self._now() < deadline:
            if not self._controller.is_running():
                return False  # container exited — don't wait out the full (generous) timeout
            if self._probe(self._spec.probe_target):
                return True
            self._sleep(self._poll)
        return self._controller.is_running() and self._probe(self._spec.probe_target)

    def evict(self) -> None:
        """Action: STOP the container to release VRAM (INV-P5-2). Never raises (idempotent).

        The manager's post-evict `wait_vram_below` is the real VRAM guarantee; a stop error here must
        not break acquisition, so it is logged, not propagated.
        """
        try:
            self._controller.stop()
        except Exception:  # noqa: BLE001 — best-effort stop; the VRAM gate is the real guarantee
            _log.exception("container stop failed during evict")

    def is_alive(self) -> bool:
        return self._controller.is_running()
