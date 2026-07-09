"""Readiness — the pure warmup state machine (Calculations over immutable Data).

The readiness *decision* (what RK-07/EC-S5 care about) is a pure function of an
immutable ``WarmupState``: unit-testable with zero I/O and deterministically drivable
in tests. The warmup *effect* (flipping the state) is an Action confined to the app
shell (``main.py``); it never lives here. Refs: evidence_map G3, risk_register RK-07.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from app.schemas import HealthStatus


@dataclass(frozen=True)
class WarmupState:
    """Immutable readiness state (Data)."""

    warmed_up: bool = False


def mark_warmed(state: WarmupState) -> WarmupState:
    """Pure transition: warmup completed -> a new warmed state (copy-on-write)."""
    return replace(state, warmed_up=True)


def is_ready(state: WarmupState) -> bool:
    """Pure readiness predicate: True only after warmup has completed."""
    return state.warmed_up


def readiness_payload(state: WarmupState) -> HealthStatus:
    """Pure: map readiness state to the ``/v1/health/ready`` body."""
    if state.warmed_up:
        return HealthStatus(status="ready")
    return HealthStatus(status="warming", detail="model/route warmup in progress")


def liveness_payload() -> HealthStatus:
    """Pure: the ``/v1/health/live`` body — independent of warmup."""
    return HealthStatus(status="live")
