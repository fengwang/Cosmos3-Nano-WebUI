# Specification: Submission Branch Freshness

## ADDED Requirements

### Requirement: Branch Rebase Is Clean Or Session Stops

The external `gpu-s4-quant-loader-isolation` branch MUST be brought current with `vllm-project/vllm-omni` `main` before PR submission readiness is claimed. `GPU-S5` MAY perform a clean rebase. If the rebase conflicts or changes semantic contribution scope, the session MUST stop and record route-back to `GPU-S4`.

#### Scenario: Clean Rebase Continues

WHEN upstream `main` has advanced and `git rebase upstream/main` completes without conflicts
THEN the session SHALL continue after recording the new upstream base and branch head.

#### Scenario: Conflict Routes Back

WHEN `git rebase upstream/main` reports a conflict
THEN the session SHALL classify the failure before any fix and SHALL NOT resolve semantic conflicts inside `GPU-S5`.

### Requirement: Post-Rebase Diff Remains In Scope

After any clean rebase, the branch diff MUST remain limited to model-agnostic quant-loader code, config wiring, checkpoint adapters, and narrow tests inherited from `GPU-S4` plus any `GPU-S5` blocker fixes.

#### Scenario: Cosmos3 Residue Is Rejected

WHEN the post-rebase diff is swept for Cosmos3-specific names, private paths, tokens, and session residue
THEN the sweep SHALL return zero forbidden matches before PR submission readiness is claimed.

#### Scenario: File List Matches Blast Radius

WHEN the post-rebase diff file list is compared to the session blast radius
THEN every changed production or test file SHALL be part of the upstream-facing quant-loader contribution.
