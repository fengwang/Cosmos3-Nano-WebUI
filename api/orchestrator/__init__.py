"""Single-GPU orchestrator (S6) — the INV-4 owner.

A single-slot residency manager that drives the generation + reasoning engine planes as
**out-of-process workers** and evicts by **process-group kill** (the only mechanism S5 proved
frees VRAM — FA-2/RK-15). Pure residency FSM (`residency`) + Action worker lifecycle (`worker`,
`gen_worker`) + a serialized async manager (`manager`). Reuses the frozen S5 co-residency
contract + verdicts. Refs: session_6/specs/single-gpu-orchestrator.md.
"""
