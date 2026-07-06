"""EV-P5-INTEG-SWAP (host, stubbed docker): INV-P5-2 coarse mutual exclusion via the real FSM.

Drives the real Orchestrator with logging fake workers + an injected post-evict VRAM gate, proving
the generation container and the reasoning worker are never co-resident: each load is preceded by the
other plane's eviction AND a confirmed VRAM release (evict-before-load, INV-4/INV-P5-2). No docker/GPU.
Spec: integration-gates-and-smokes; design.md data flow (SWAP).
"""
from __future__ import annotations

import asyncio

import pytest

from orchestrator.manager import Orchestrator
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId
from orchestrator.worker import WorkerStartError

GEN = ResidencyId(Plane.GENERATION, "fp8-blockwise")
REASON = ResidencyId(Plane.REASONING)


class _LogWorker:
    """A fake PlaneWorker that records lifecycle calls into a shared log (models a container or subprocess)."""

    def __init__(self, plane: Plane, log: list) -> None:
        self._plane = plane
        self._log = log
        self._alive = False

    def start(self) -> None:
        self._log.append(("start", self._plane))
        self._alive = True

    def wait_ready(self, timeout: float) -> bool:
        self._log.append(("ready", self._plane))
        return True

    def evict(self) -> None:
        self._log.append(("evict", self._plane))
        self._alive = False

    def is_alive(self) -> bool:
        return self._alive


def _orch(log: list, *, vram_ok: bool = True) -> Orchestrator:
    return Orchestrator(
        lambda target: _LogWorker(target.plane, log),
        idle_timeout=0,
        post_evict_wait=lambda: (log.append(("vram_released",)) or vram_ok),
    )


def test_swap_sequence_is_evict_before_load_never_coresident():
    log: list = []
    orch = _orch(log)

    async def scenario():
        await orch.acquire(GEN)     # cold load
        await orch.acquire(REASON)  # swap: evict GEN → vram → load REASON
        await orch.acquire(GEN)     # swap back: evict REASON → vram → load GEN

    asyncio.run(scenario())
    assert log == [
        ("start", Plane.GENERATION), ("ready", Plane.GENERATION),
        ("evict", Plane.GENERATION), ("vram_released",),
        ("start", Plane.REASONING), ("ready", Plane.REASONING),
        ("evict", Plane.REASONING), ("vram_released",),
        ("start", Plane.GENERATION), ("ready", Plane.GENERATION),
    ]


def test_reasoning_starts_only_after_gen_evict_and_vram_release():
    log: list = []
    orch = _orch(log)

    async def scenario():
        await orch.acquire(GEN)
        await orch.acquire(REASON)

    asyncio.run(scenario())
    # the INV-P5-2 window: gen evicted → VRAM confirmed released → ONLY THEN reasoning starts
    assert log.index(("evict", Plane.GENERATION)) < log.index(("vram_released",)) < log.index(("start", Plane.REASONING))


def test_vram_not_released_refuses_load_no_coresidency():
    log: list = []
    orch = _orch(log, vram_ok=False)  # eviction did not free VRAM

    async def scenario():
        await orch.acquire(GEN)
        await orch.acquire(REASON)  # must refuse to load on top of unreleased VRAM (would OOM)

    with pytest.raises(WorkerStartError):
        asyncio.run(scenario())
    assert ("start", Plane.REASONING) not in log  # reasoning never started → never co-resident
    assert orch.resident is None                  # slot left clean, not half-loaded
