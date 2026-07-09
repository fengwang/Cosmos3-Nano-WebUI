# Session 4 Design

## Context

The PRD requires `GPU-S4` to answer whether upstream already has the contribution before any isolation work begins. If the answer is no, the session must create an isolated, rebased, compiling feature branch on the `fengwang/vllm-omni` fork.

The external checkout exists at `<external-vllm-omni-checkout>` and starts clean at fork pin `697035018b70cef76b974a909d23371a9984c3f2`. Current upstream `main`, checked read-only by `git ls-remote`, is `a5db2d839a0a20ddb0090faa5bb233280601e5eb`.

## Goals

- Record an evidenced answer to the upstream-state question.
- If needed, create a branch from upstream `main` with only model-agnostic FP8/NVFP4 quant-loader support.
- Add or preserve narrow CPU tests for touched quant-loader surfaces.
- Rebase or synthesize cleanly onto upstream `main`.
- Push the verified branch to `fengwang/vllm-omni`.
- Hand off exact branch, commit, checks, conflict notes, and semantic drift to `GPU-S5`.

## Non-Goals

- Open an upstream pull request.
- Run `precheck-pr`.
- Add broad PR hygiene or GPU tests.
- Touch this repository's runtime source, Dockerfiles, schemas, checkpoints, or archived Phase-1 files.
- Carry Cosmos3-specific model, adapter, or guard code into the upstream-facing branch.

## Decisions

### D1: Branch From Upstream Main, Then Import The Slice

Create the feature branch from `upstream/main`, not from the Cosmos3 fork branch. Import only the candidate files and hunks required by the contract.

Why: this makes the branch PR-shaped from the start and prevents hidden Cosmos3 commits from becoming the base of the contribution.

Alternative considered: cherry-pick historical fork commits and prune. Rejected because the local history mixes quant-loader work with Cosmos3 integration.

### D2: Treat Upstream Coverage As An Early Exit

Run upstream state checks before any contribution commit. If upstream already has equivalent support, write the finding and do not create an isolation branch.

Why: the PRD requires this check first, and unnecessary upstream-facing code would increase review risk.

### D3: Keep Tests Narrow And CPU-Only

Add or preserve tests only for the touched quant-loader surfaces. Avoid GPU tests, e2e serving tests, and `precheck-pr`.

Why: the user clarified that narrow external-fork tests are in scope, but the session plan leaves full PR hygiene to `GPU-S5`.

### D4: Use ACD Boundaries Inside The Quant Slice

Keep file reads, git operations, and test execution in shell scripts or command steps. In code, keep parsing, shape checks, remapping, target matching, and dequant math as pure calculations over explicit inputs where the existing upstream style allows it.

Why: the quant-loader code is easier to test and review when I/O is isolated at adapter detection and checkpoint loading boundaries.

### D5: Escalate Cosmos3-Required Conflicts

If a conflict cannot be resolved without importing Cosmos3-specific model, pipeline, guard, or adapter code, stop and record the conflict rather than copying that code.

Why: project invariant `INV-6` and the session contract forbid Cosmos3-specific dependencies in the upstream-facing branch.

## Risks And Mitigations

- Upstream has overlapping support with different names -> Mitigation: inspect both name matches and semantic equivalents such as ModelOpt FP8/NVFP4 detection, not only exact filenames.
- Candidate code imports Cosmos3-specific modules -> Mitigation: run import and text sweeps for `cosmos3`, `Cosmos3`, and model-specific paths before final checks.
- Tests rely on local Cosmos3 docs or fixtures -> Mitigation: keep tests self-contained and remove references to this repository's old session paths from upstream-facing test docstrings where practical.
- The NVFP4 NaN-clamp hunk conflicts with upstream's `patch.py` -> Mitigation: first check whether upstream already clamps, then either self-extinguish or add the smallest guarded hunk.
- Branch push succeeds but docs record the wrong commit -> Mitigation: capture `git rev-parse HEAD` after push and record it in evidence and handoff.

## Migration Plan

1. Add `upstream` remote if absent and fetch current `main`.
2. Record upstream-state checks in `docs/session_4/upstream_state.md`.
3. If upstream covers the feature, update evidence, risk, handoff, and stop.
4. If missing, create `gpu-s4-quant-loader-isolation` from `upstream/main`.
5. Import candidate files and tests from fork pin `697035018b70cef76b974a909d23371a9984c3f2`.
6. Resolve quant-surface conflicts only.
7. Run targeted checks after each task.
8. Push to `origin/gpu-s4-quant-loader-isolation` after final local verification.
9. Update this repository's evidence, review, adversarial verification, handoff, and eval seeds.

Rollback strategy: the external branch can be deleted or superseded before `GPU-S5` opens a PR. This repository records the branch and evidence by reference only.

## Open Questions

- Exact upstream semantic overlap is unknown until `git fetch upstream` and source inspection run.
- The minimum viable test set depends on upstream's current test layout after fetch.
- The final branch name is planned as `gpu-s4-quant-loader-isolation`; if it already exists remotely, create a date-suffixed branch and record it.

