"""The single-slot residency FSM (ACD: Data + a pure Calculation; the INV-4 decision core).

`plan_acquire` decides what the manager must DO to make a requested identity resident — it never does
it (no I/O). The invariant it encodes: at most one heavy plane resident, so a swap is always
**evict-then-load** (never load a second plane while one is resident). Pure → host-testable with
synthetic state.

S2 extends the identity from bare `Plane` to `ResidencyId(plane, label)` — checkpoint switching
(INV-P3-2) is a natural consequence of the dataclass equality, not a special case.
Refs: session_6/specs/single-gpu-orchestrator.md.
"""
from __future__ import annotations

from dataclasses import dataclass

from orchestrator.planes import Plane


@dataclass(frozen=True)
class ResidencyId:
    """The full identity of a resident plane — plane type + optional checkpoint label."""

    plane: Plane
    label: str | None = None


@dataclass(frozen=True)
class ResidencyPlan:
    """The orchestrator's marching orders for one acquisition (inert Data)."""

    evict: ResidencyId | None
    load: ResidencyId | None


def plan_acquire(current: ResidencyId | None, requested: ResidencyId) -> ResidencyPlan:
    """Pure: decide the eviction/load for making ``requested`` resident given ``current``.

    - already resident → no-op ``(None, None)``
    - cold slot → load-only ``(None, requested)``
    - different identity resident → **evict-before-load** ``(current, requested)`` (INV-4)
    """
    if current == requested:
        return ResidencyPlan(evict=None, load=None)
    if current is None:
        return ResidencyPlan(evict=None, load=requested)
    return ResidencyPlan(evict=current, load=requested)
