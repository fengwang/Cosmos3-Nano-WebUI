# Evidence, Risk, And Handoff Specification

## ADDED Requirements

### Requirement: Evidence Drift Handling

The session SHALL update `docs/evidence_map.md` only when the observed public baseline changes, sharpens, or contradicts existing evidence.

#### Scenario: Baseline Matches Existing Evidence

WHEN Session 1 baseline commands match existing evidence rows
THEN the session MUST avoid unrelated evidence rewrites and MAY add a narrowly scoped Session 1 row if it improves future handoff.

#### Scenario: Baseline Contradicts Existing Evidence

WHEN Session 1 baseline commands contradict existing evidence rows
THEN the session MUST update `docs/evidence_map.md` with the new command evidence and classify any resulting risk change.

### Requirement: Risk And Eval Updates

The session SHALL update `docs/risk_register.md` or `docs/eval_seed_cases.md` only when a new risk, missed check, noisy check, or reusable eval seed is found.

#### Scenario: Check Command Bug Found

WHEN a deterministic check command is found to be noisy or malformed
THEN the session MUST record the failure classification in `docs/session_1/failure_arbiter.md` and MUST consider whether an eval seed or checklist update is needed.

### Requirement: Session Handoff

The session SHALL write `docs/handoff.md` from the repo template because the user explicitly allowed it for this session.

#### Scenario: Session Completes

WHEN final checks have run and `GATE-MIG-S1-SCOPE` is evaluated
THEN `docs/handoff.md` MUST list changed files, checks run, checks not run, current status, decisions, next priorities, warnings, and eval seed notes.

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
