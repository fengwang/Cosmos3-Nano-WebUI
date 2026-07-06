"""Spec: health-readiness — pure warmup state machine (Calculations + Data, no I/O)."""
from app.readiness import (
    WarmupState,
    is_ready,
    liveness_payload,
    mark_warmed,
    readiness_payload,
)


def test_initial_state_is_not_ready():
    # specs/health-readiness.md :: readiness gate is deterministic under injection
    assert is_ready(WarmupState()) is False


def test_mark_warmed_makes_ready_and_is_immutable():
    s0 = WarmupState()
    s1 = mark_warmed(s0)
    assert is_ready(s1) is True
    assert s0.warmed_up is False  # original unchanged (frozen, copy-on-write)
    assert s1 is not s0


def test_readiness_payload_maps_state():
    assert readiness_payload(WarmupState()).status == "warming"
    assert readiness_payload(mark_warmed(WarmupState())).status == "ready"


def test_liveness_is_independent_of_warmup():
    assert liveness_payload().status == "live"
