"""Spec: single-gpu-orchestrator — the pure residency FSM (the INV-4 decision core).

`plan_acquire` decides what the single-slot manager must DO (evict/load), never does it — so the
evict-before-load invariant is a host-testable Calculation with no I/O.

Extended in S2 with `ResidencyId(plane, label)` — checkpoint switching (INV-P3-2) is a natural
consequence of the identity comparison, not a special case.
"""
from __future__ import annotations

from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId, ResidencyPlan, plan_acquire


# ---- existing plane-level tests (wrapped in ResidencyId) -------------------------

def test_acquire_different_plane_evicts_first():
    assert plan_acquire(ResidencyId(Plane.REASONING), ResidencyId(Plane.GENERATION)) == ResidencyPlan(
        evict=ResidencyId(Plane.REASONING), load=ResidencyId(Plane.GENERATION)
    )


def test_acquire_resident_plane_is_noop():
    assert plan_acquire(ResidencyId(Plane.GENERATION), ResidencyId(Plane.GENERATION)) == ResidencyPlan(
        evict=None, load=None
    )


def test_acquire_on_cold_slot_loads_without_evicting():
    assert plan_acquire(None, ResidencyId(Plane.REASONING)) == ResidencyPlan(
        evict=None, load=ResidencyId(Plane.REASONING)
    )


def test_plan_never_loads_two_planes():
    plan = plan_acquire(ResidencyId(Plane.GENERATION), ResidencyId(Plane.REASONING))
    assert plan.load == ResidencyId(Plane.REASONING) and plan.evict == ResidencyId(Plane.GENERATION)


# ---- S2: checkpoint-label tests (INV-P3-2) --------------------------------------

def test_same_plane_different_label_evicts():
    """The core S2 scenario: NVFP4 → FP8 on the same plane triggers evict-then-load."""
    assert plan_acquire(
        ResidencyId(Plane.GENERATION, "nvfp4"), ResidencyId(Plane.GENERATION, "fp8")
    ) == ResidencyPlan(
        evict=ResidencyId(Plane.GENERATION, "nvfp4"), load=ResidencyId(Plane.GENERATION, "fp8")
    )


def test_same_plane_same_label_is_noop():
    assert plan_acquire(
        ResidencyId(Plane.GENERATION, "fp8"), ResidencyId(Plane.GENERATION, "fp8")
    ) == ResidencyPlan(evict=None, load=None)


def test_cold_slot_with_label_loads():
    assert plan_acquire(None, ResidencyId(Plane.GENERATION, "fp8")) == ResidencyPlan(
        evict=None, load=ResidencyId(Plane.GENERATION, "fp8")
    )


def test_reasoning_nolabel_reacquire_noop():
    assert plan_acquire(
        ResidencyId(Plane.REASONING, None), ResidencyId(Plane.REASONING, None)
    ) == ResidencyPlan(evict=None, load=None)


def test_reverse_checkpoint_switch_evicts():
    """FP8 → NVFP4 is symmetric — both directions evict."""
    assert plan_acquire(
        ResidencyId(Plane.GENERATION, "fp8"), ResidencyId(Plane.GENERATION, "nvfp4")
    ) == ResidencyPlan(
        evict=ResidencyId(Plane.GENERATION, "fp8"), load=ResidencyId(Plane.GENERATION, "nvfp4")
    )
