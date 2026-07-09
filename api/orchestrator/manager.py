"""The single-GPU orchestrator (Action shell; the INV-4 owner).

One mutable slot (the resident `ResidencyId`) behind an `asyncio.Lock`, so concurrent `acquire`s
**serialize** — defeating "two heavy jobs both grab the GPU → OOM" (RK-03/RK-15). Every acquisition
runs the pure `plan_acquire` FSM, then: evict the resident worker by **process-group kill**, wait
until VRAM is released, and only then start the requested worker (evict-before-load). The worker
**factory** and the post-evict **VRAM wait** are injected, so the whole FSM + serialization are
host-testable with stub workers (no GPU); the gated-live path injects the real factory (vLLM server
+ `gen_worker`) and the real VRAM wait.

S2 extends the identity from bare `Plane` to `ResidencyId(plane, label)` — checkpoint switching
(INV-P3-2) is handled by the FSM. Adds idle-timeout eviction (INV-P3-3).
Refs: session_6/specs/single-gpu-orchestrator.md.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from orchestrator.residency import ResidencyId, plan_acquire
from orchestrator.worker import PlaneWorker, WorkerStartError, wait_vram_below

WorkerFactory = Callable[[ResidencyId], PlaneWorker]
VramWait = Callable[[], bool]

# A clean process-group kill returns the GPU to ~idle; loading the next plane on top of an unreleased
# KV cache is the RK-15 OOM. This absolute threshold gates the next load (the gated-live path passes a
# baseline-relative one). Generous: planes are out-of-process, so the api process itself holds ~0 VRAM.
DEFAULT_IDLE_BYTES = 2 * 1024**3

_log = logging.getLogger("cosmos3.orchestrator")


class Orchestrator:
    """At-most-one-heavy-plane-resident residency manager (the INV-4 owner)."""

    def __init__(
        self,
        factory: WorkerFactory,
        *,
        ready_timeout: float = 300.0,
        idle_bytes: int = DEFAULT_IDLE_BYTES,
        vram_timeout: float = 180.0,
        post_evict_wait: VramWait | None = None,
        idle_timeout: float = 600.0,
    ) -> None:
        self._factory = factory
        self._ready_timeout = ready_timeout
        self._post_evict_wait: VramWait = post_evict_wait or (
            lambda: wait_vram_below(idle_bytes, vram_timeout)
        )
        self._lock = asyncio.Lock()
        self._slot: ResidencyId | None = None
        self._worker: PlaneWorker | None = None
        self._idle_timeout = idle_timeout
        self._idle_handle: asyncio.TimerHandle | None = None
        self._idle_task: asyncio.Task | None = None

    @property
    def resident(self) -> ResidencyId | None:
        """The currently-resident identity (``None`` if the slot is cold)."""
        return self._slot

    async def acquire(self, target: ResidencyId) -> None:
        """Make ``target`` resident, evicting any other identity first (evict-before-load, serialized).

        Raises `WorkerStartError` if VRAM is not released after an eviction, or if the requested
        worker never becomes ready — never leaving a half-loaded plane recorded as resident.
        """
        async with self._lock:
            self._cancel_idle_timer()
            plan = plan_acquire(self._slot, target)
            if plan.evict is not None and self._worker is not None:
                _log.info("evicting %s before loading %s", plan.evict, target)
                await asyncio.to_thread(self._worker.evict)
                self._worker = None
                self._slot = None
                if not await asyncio.to_thread(self._post_evict_wait):
                    raise WorkerStartError(
                        f"VRAM not released after evicting for {target} (refusing to load — would OOM)"
                    )
            if plan.load is not None:
                worker = self._factory(target)
                await asyncio.to_thread(worker.start)
                ready = await asyncio.to_thread(worker.wait_ready, self._ready_timeout)
                if not ready:
                    await asyncio.to_thread(worker.evict)
                    raise WorkerStartError(f"{target} worker did not become ready")
                self._worker = worker
                self._slot = target

    async def evict_all(self) -> None:
        """Evict any resident worker and free the slot (shutdown / cancellation)."""
        async with self._lock:
            self._cancel_idle_handle()
            if self._worker is not None:
                await asyncio.to_thread(self._worker.evict)
            self._worker = None
            self._slot = None

    def notify_idle(self) -> None:
        """Start (or reset) the idle timer after a job finishes. 0 = disabled (INV-P3-3)."""
        self._cancel_idle_timer()
        if self._idle_timeout > 0 and self._slot is not None:
            loop = asyncio.get_running_loop()
            self._idle_handle = loop.call_later(self._idle_timeout, self._on_idle_timeout)

    def _cancel_idle_handle(self) -> None:
        if self._idle_handle is not None:
            self._idle_handle.cancel()
            self._idle_handle = None

    def _cancel_idle_timer(self) -> None:
        self._cancel_idle_handle()
        if self._idle_task is not None:
            self._idle_task.cancel()
            self._idle_task = None

    def _on_idle_timeout(self) -> None:
        self._idle_handle = None
        self._idle_task = asyncio.create_task(self._try_idle_evict())

    async def _try_idle_evict(self) -> None:
        try:
            if self._lock.locked():
                return
            _log.info("idle timeout — evicting resident %s", self._slot)
            await self.evict_all()
        except asyncio.CancelledError:
            raise
        except Exception:
            _log.exception("idle eviction failed")
        finally:
            self._idle_task = None
