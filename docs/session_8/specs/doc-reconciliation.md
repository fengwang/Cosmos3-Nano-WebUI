# Specification - Doc Reconciliation

Session: MIG-S8
Capability: doc-reconciliation

## ADDED Requirements

### Requirement: No release-blocking risk is left unowned

`docs/risk_register.md` MUST, at session close, have no release-blocking risk that is open
without an owner-visible disposition. Every release-blocking risk MUST be Closed, Mitigated,
or explicitly routed with the owner's decision recorded.

#### Scenario: Every release blocker is dispositioned

WHEN the risk register is read at close
THEN each release-blocking risk SHALL be Closed, Mitigated, or routed to a named
owner/session with the owner's decision recorded (e.g. the GPU deferral).

#### Scenario: The GPU-deferral decision is recorded

WHEN R-05 / R-08 / R-13 (GPU / surface-breadth / fork-image) are read
THEN each SHALL record the owner's beta-limited disposition and the session that owns the
follow-up.

### Requirement: Tracking docs are consistent with each other and with the repo

`docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`, and
`docs/release_checklist.md` MUST be updated to a final state that does not contradict the
README, the Docker/Compose setup, or `docs/model_setup.md`.

#### Scenario: Evidence map records the S8 gate

WHEN `docs/evidence_map.md` is read
THEN it SHALL contain an `MIG-S8` row recording the release-gate review, the checks run, and
the manual-gate deferral, using public evidence only.

#### Scenario: Eval seed cases reflect final state

WHEN `docs/eval_seed_cases.md` is read
THEN deterministic cases satisfied through `MIG-S7` SHALL be marked satisfied, and each
`EV-MIG-GPU-*` case SHALL be marked as the `MIG-S8` manual gate.

#### Scenario: Release checklist separates verified from manual gates

WHEN `docs/release_checklist.md` is read
THEN CPU/scan/license/hygiene items verified this session SHALL be tickable with evidence,
and GPU + at-publish items SHALL remain explicit manual/at-publish gates.

#### Scenario: No cross-doc contradiction

WHEN the reconciled docs are compared with the README claim matrix and `docs/model_setup.md`
THEN no reconciled doc SHALL contradict the README's claims, the Compose wiring, or the
checkpoint setup.
