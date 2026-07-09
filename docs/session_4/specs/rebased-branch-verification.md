# Specification: Rebased Branch Verification

## ADDED Requirements

### Requirement: Isolated Branch Is Based On Current Upstream Main

If isolation proceeds, the feature branch MUST be based on current `upstream/main` and rebase or synthesis conflicts MUST be recorded.

#### Scenario: Branch Base Is Current

WHEN the branch is ready for final checks
THEN `git merge-base HEAD upstream/main` SHALL equal the current upstream `main` commit, unless a recorded fast-forward or rebase note explains a newer fetched ref.

#### Scenario: Conflicts Are Classified

WHEN a conflict occurs
THEN the session SHALL classify whether it is inside the quant-loader surface, outside the allowed surface, or requires Cosmos3-specific judgment before resolving it.

### Requirement: Final Checks Prove Compile And Scope

The final branch MUST compile and pass the targeted checks chosen for the touched quant-loader surfaces.

#### Scenario: Compileall Passes

WHEN `python -m compileall vllm_omni` runs on the isolated branch
THEN it SHALL exit with status 0, or the failure SHALL be classified before any fix.

#### Scenario: Cosmos3 Sweep Passes

WHEN the final branch diff and touched files are searched for Cosmos3-specific dependencies
THEN no forbidden dependency SHALL remain in the isolated quant-loader branch.

### Requirement: Verified Branch Is Published To The Fork

After local checks pass, the isolated branch MUST be pushed to `fengwang/vllm-omni` for `GPU-S5`.

#### Scenario: Handoff Names Remote Branch And Commit

WHEN the session ends after a successful push
THEN the handoff SHALL record the remote branch name, final commit SHA, checks run, checks not run, and remaining risks.

