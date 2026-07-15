# Session 5 Design

## Context

`GPU-S4` handed off external branch `gpu-s4-quant-loader-isolation` at `f7e024ddc9965622ebcfdb919e8ccb46b4232074`. The branch contains model-agnostic quant-loader/config wiring and narrow tests. `GPU-S5` must turn that branch into an upstream PR only after it passes contribution hygiene and the owner gives an immediate final approval.

Fresh startup evidence shows remote upstream `main` has advanced beyond the `GPU-S4` base. The owner approved a narrow `GPU-S5` rebase allowance: rebase if clean; stop and route back to `GPU-S4` if conflicts or semantic drift appear.

## Goals

- Bring the external branch up to current upstream `main` without scope drift.
- Run `precheck-pr` quick and full.
- Confirm local equivalents for upstream CI where practical.
- Verify DCO sign-off on every PR commit.
- Prepare valid PR metadata.
- Record the owner go-ahead immediately before opening the PR.
- Open the PR and record its URL and checks status, or record why submission did not proceed.

## Non-Goals

- Further quant isolation or semantic rebase work if conflicts appear.
- Responding to maintainer review after the PR is open.
- Adding production dependencies.
- Changing this repository's runtime source.
- Changing Cosmos3-specific code anywhere in the upstream-facing branch.
- GPU validation or benchmark expansion.

## Decisions

### D1: Treat Clean Rebase As Submission Hygiene

Fetch current upstream and attempt `git rebase upstream/main` before precheck. If conflict-free and the diff remains inside the existing quant-loader scope, continue. If not, stop and record a route-back to `GPU-S4`.

Why: branch freshness is part of the upstream precheck, and the owner explicitly approved the clean-rebase path for this session.

### D2: Run Both `precheck-pr` Modes

Run quick mode first to catch showstoppers, then full mode before PR submission readiness. Record both outputs.

Why: the session contract requires quick and full. A clean quick run is not a substitute for full.

### D3: Use Local Equivalents Before The PR, GitHub CI After The PR

Before asking for owner go-ahead, run targeted pytest, `compileall`, guard sweeps, DCO checks, `pre-commit`, and local wheel build where practical. After PR creation, run `gh pr checks <PR>`.

Why: GitHub CI only exists after PR creation, but the outward action must be as evidence-backed as possible before the owner gate.

### D4: Fix Only Concrete Blockers Or High/Critical Findings

Warnings that do not violate the session contract are recorded. High/Critical review findings, precheck blockers, DCO failures, and CI failures are fixed if they fall inside blast radius.

Why: `GPU-S5` is a gate/submission session, not a broad refactor session.

### D5: Keep PR Creation Manual-Gated

Do not script or batch `gh pr create` with earlier checks. Stop and ask the owner immediately before the command.

Why: project contract `INV-7` and PRD owner decision 7 require a recorded, immediate owner go-ahead.

## ACD Design Notes

| Concern | ACD Class | Boundary |
|---|---|---|
| Git fetch/rebase/push | Action | external shell commands |
| `precheck-pr`, pytest, pre-commit, wheel build | Action | verification shell commands |
| PR title/body selection | Calculation over upstream guidance plus diff metadata | recorded before GitHub action |
| DCO trailer verification | Calculation over git log text, driven by Action command output | evidence artifact |
| PR creation | Action | hard owner gate immediately before command |
| Quant target parsing/remapping tests | Calculation | existing fork tests exercise pure helpers |

## Risks And Mitigations

- Upstream drift creates conflicts -> Mitigation: stop and record route-back to `GPU-S4`.
- `precheck-pr` guidance differs from current docs -> Mitigation: read both the local skill and `docs/contributing/README.md`, record the interpretation.
- Local wheel build fails due to environment -> Mitigation: classify before fixing; only product-code failures justify code changes.
- A DCO trailer is missing after rebase/fix commit -> Mitigation: use `git commit -s` and verify `Signed-off-by` on every branch commit before push.
- `gh pr create` happens before owner gate -> Mitigation: no automated PR creation; require explicit user response immediately before command.
- GitHub CI fails after PR creation -> Mitigation: classify with Failure Arbiter; fix only in-scope product/test issues.

## Migration Plan

1. Create session 5 planning/spec/task/plan artifacts.
2. Fetch upstream and rebase the external branch if clean.
3. Re-run targeted tests and guard sweeps after rebase.
4. Run quick `precheck-pr`; classify and fix blockers.
5. Run full `precheck-pr`; classify and fix blockers.
6. Run local pre-commit and wheel build where practical.
7. Verify DCO and PR metadata.
8. Run sharded review and fix High/Critical only.
9. Run adversarial verification.
10. Ask owner for immediate go-ahead.
11. If approved, open PR, push final branch as needed, and wait on `gh pr checks`.
12. Update evidence, risk register, handoff, and eval seeds.

Rollback strategy: before PR creation, the fork branch can be force-pushed or replaced if only local/fork state changed. After PR creation, rollback is closing or superseding the PR, which is why owner approval is mandatory.

## Open Questions

- Whether the rebase is conflict-free is unknown until upstream is fetched.
- Whether local wheel build completes in this environment is unknown until run.
- Whether upstream CI includes checks beyond `pre-commit` and `build_wheel` is unknown until the PR exists.
