# Specification - Gate Record

Session: MIG-S8
Capability: gate-record

## ADDED Requirements

### Requirement: Every migration gate is recorded with status and evidence

`docs/session_8/outputs/gate_record.md` MUST record each gate `GATE-MIG-S1-SCOPE` through
`GATE-MIG-S8-BETA` with a status and a public evidence pointer (the closing session's
deterministic checks, tracked artifacts, or public remotes/model pages).

#### Scenario: All eight gates are present

WHEN the gate record is read
THEN it SHALL contain a row for each of `GATE-MIG-S1..S8`, each with a status and a public
evidence pointer.

#### Scenario: Manual GPU gate status is recorded

WHEN the record covers the GPU surface
THEN it SHALL record the manual GPU gate as NOT-YET-RUN / beta-limited and SHALL record the
pin and revisions any later run must match (vLLM-Omni `697035018b70…`, FP8 `4e181f99…`,
NVFP4 `b5c9332e…`).

### Requirement: The recommended verdict is advisory and evidence-based

The gate record MUST state a recommended `GATE-MIG-S8-BETA` verdict, the rule that produced
it, and that it is advisory pending owner ratification. The recommendation MUST rest only on
verified evidence and MUST name any condition that is deferred to at-publish.

#### Scenario: Verdict is marked recommended, owner ratifies

WHEN the `GATE-MIG-S8-BETA` row is read
THEN it SHALL be labelled "recommended (owner ratifies)" and SHALL list the exact conditions
the recommendation depends on.

#### Scenario: Recommendation rule is explicit

WHEN the rationale is read
THEN it SHALL state the GO rule (scrub clean ∧ CPU checks green ∧ compose renders ∧
license/hygiene present ∧ claims evidence-qualified ∧ no unowned release-blocking risk ∧ GPU
marked beta-limited ∧ every PRD MUST covered) and distinguish blockers from at-publish
conditions.

#### Scenario: Drift D1 is an owner-visible beta limitation

WHEN the record covers checkpoint loading
THEN drift D1 SHALL be recorded as an open, owner-visible beta limitation routed to the GPU
session, not silently marked resolved or PASS.
