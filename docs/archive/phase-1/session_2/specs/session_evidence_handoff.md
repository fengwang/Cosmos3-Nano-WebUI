# Specification - Session Evidence And Handoff

Session: MIG-S2
Capability: Session Evidence And Handoff

## ADDED Requirements

### Requirement: Deterministic checks are recorded with classifications

Session 2 SHALL record every required deterministic check, its command, result,
and failure classification if it does not pass.

#### Scenario: Check failure is classified before fix

WHEN a compile, pytest, push, or remote-verification command fails
THEN `docs/session_2/failure_arbiter.md` SHALL record its category, evidence,
why other categories do not fit, allowed next action, and forbidden next action
before source changes are expanded.

### Requirement: Evidence map and risk register reflect the final pin

The WebUI repo SHALL update public evidence and risk status for the vLLM-Omni
fork pin.

#### Scenario: Evidence documents the public pin

WHEN Session 2 exits successfully
THEN `docs/evidence_map.md` SHALL contain a row for the final public branch/tag
or commit
AND `docs/risk_register.md` SHALL update `R-02` and `R-13` with the Session 2
disposition.

### Requirement: Review and adversarial verification are saved

Because Session 2 is high risk, sharded review and adversarial verification MUST
be run and saved.

#### Scenario: Review artifacts exist before handoff

WHEN Session 2 finalization starts
THEN `docs/session_2/sharded_review.md` SHALL contain actionable findings or an
explicit no-finding result
AND `docs/session_2/adversarial_verification.md` SHALL contain a PASS/FAIL
verdict against the Session 2 done condition.

## MODIFIED Requirements

### Requirement: Deterministic checks run in the external fork checkout

The Session 2 deterministic checks are scoped to the external vLLM-Omni fork
checkout when they reference `vllm_omni` or fork tests. WebUI seed-repo failures
for those commands are environment/scope evidence, not product failures.

#### Scenario: WebUI seed repo lacks fork source

WHEN `rtk python -m compileall vllm_omni` is run from the WebUI repo and
`vllm_omni` does not exist
THEN the failure SHALL be classified as ENVIRONMENT/scope
AND the same check SHALL be run from `vllm-omni`.

