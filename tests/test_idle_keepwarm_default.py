"""Spec: idle-keep-warm-default (LX-S1).

The shipped idle keep-warm default is **1800 s (30 min)** at BOTH sources of truth — the app's
env-wiring (`api/app/main.py`) and the `Orchestrator` constructor default
(`api/orchestrator/manager.py`) — it stays operator-overridable via
`COSMOS3_IDLE_TIMEOUT_SECONDS`, and `0` disables idle eviction (INV-2, FR-1/FR-2, E-06/R-02).

These assert the **app-wired** value — built through `create_app()`'s real env→construct path,
read off the resident orchestrator — not a module literal, so a `main.py` wiring regression fails
here (the contract's "asserts the constant, not the wiring" adversarial case). No GPU:
`create_app()` only *constructs* the worker factory (never calls it), and the reasoning tokenizer
degrades to `None` on the torch-free host.
"""
from __future__ import annotations

from app.main import create_app
from orchestrator.manager import Orchestrator
from orchestrator.planes import Plane
from orchestrator.residency import ResidencyId

_IDLE_ENV = "COSMOS3_IDLE_TIMEOUT_SECONDS"


def _wired_idle_timeout(app) -> float:
    """The idle keep-warm actually wired into the resident orchestrator (through the metered wrapper)."""
    return app.state.orchestrator._inner._idle_timeout


def test_app_wires_idle_keepwarm_default_1800(monkeypatch):
    # No env set → the shipped default. This is the headline gate: it proves the *wired* value,
    # so a regression of the main.py fallback (600 vs 1800) cannot pass unnoticed.
    monkeypatch.delenv(_IDLE_ENV, raising=False)
    app = create_app()
    assert _wired_idle_timeout(app) == 1800.0


def test_app_honors_idle_keepwarm_override(monkeypatch):
    # INV-2: still an overridable operator setting, not a hard-coded lock.
    monkeypatch.setenv(_IDLE_ENV, "900")
    app = create_app()
    assert _wired_idle_timeout(app) == 900.0


def test_app_wires_idle_keepwarm_zero(monkeypatch):
    # INV-2: 0 stays a valid, wired value ("never evict").
    monkeypatch.setenv(_IDLE_ENV, "0")
    app = create_app()
    assert _wired_idle_timeout(app) == 0.0


def test_orchestrator_constructor_default_is_1800():
    # A directly-constructed orchestrator (tests, future callers) must not drift from the wired
    # default (E-06/R-02). The factory is never invoked at construction, so a stub is sufficient.
    orch = Orchestrator(lambda target: None)
    assert orch._idle_timeout == 1800.0


def test_idle_timeout_zero_schedules_no_timer():
    # INV-2 / failure-mode watch: notify_idle only schedules when idle_timeout > 0. The slot is
    # forced resident so the *only* reason no timer is scheduled is the 0 guard (not the empty
    # slot). idle_timeout=0 short-circuits before touching the event loop, so no loop is needed.
    orch = Orchestrator(lambda target: None, idle_timeout=0.0)
    orch._slot = ResidencyId(Plane.GENERATION)
    orch.notify_idle()
    assert orch._idle_handle is None
