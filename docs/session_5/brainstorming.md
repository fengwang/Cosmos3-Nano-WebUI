# Session 5 Brainstorming

## Startup Snapshot

- Main repository branch: `GPU-S5`.
- Main repository state: clean at startup by `git status --short`.
- Recent main commit: `4035f02` (`Codex implements S4`).
- `docs/session_5/` did not exist before this session.
- External fork checkout: `<external-vllm-omni-checkout>`.
- External fork branch: `gpu-s4-quant-loader-isolation`.
- External fork HEAD: `f7e024ddc9965622ebcfdb919e8ccb46b4232074`.
- External fork state: clean at startup.
- External fork remote branch: `origin/gpu-s4-quant-loader-isolation` also points to `f7e024ddc9965622ebcfdb919e8ccb46b4232074`.
- Local upstream tracking ref at handoff: `a5db2d839a0a20ddb0090faa5bb233280601e5eb`.
- Fresh read-only remote check during startup: `vllm-project/vllm-omni` `main` has advanced to `ca0ae7269ca3e9487645cf66088fdfc338951da9`.
- No PR exists for `fengwang:gpu-s4-quant-loader-isolation` against `vllm-project/vllm-omni` at startup.

## Baseline Checks

Read-only checks run before editing:

```bash
rtk git status --short
rtk git branch --show-current
rtk git log --oneline --decorate -n 10
rtk git status --short --branch  # in <external-vllm-omni-checkout>
rtk git log --oneline --decorate -n 8  # in <external-vllm-omni-checkout>
rtk git remote -v  # in <external-vllm-omni-checkout>
rtk git log --format='%h %s%n%b' -n 4  # in <external-vllm-omni-checkout>
rtk ls -la <external-vllm-omni-checkout>/.claude/skills/precheck-pr
rtk cat <external-vllm-omni-checkout>/.claude/skills/precheck-pr/SKILL.md
rtk cat <external-vllm-omni-checkout>/.claude/skills/precheck-pr/references/checklists.md
rtk cat <external-vllm-omni-checkout>/.claude/skills/precheck-pr/references/code-quality.md
rtk sed -n '1,220p' <external-vllm-omni-checkout>/CONTRIBUTING.md
rtk sed -n '1,220p' <external-vllm-omni-checkout>/.github/workflows/pre-commit.yml
rtk sed -n '1,260p' <external-vllm-omni-checkout>/.github/workflows/build_wheel.yml
rtk sed -n '1,220p' <external-vllm-omni-checkout>/.pre-commit-config.yaml
rtk git ls-remote upstream refs/heads/main  # in <external-vllm-omni-checkout>
rtk gh pr list --repo vllm-project/vllm-omni --head fengwang:gpu-s4-quant-loader-isolation --state all --json number,state,title,url,headRefName,headRepositoryOwner
```

Known failing or not-yet-satisfied checks at startup:

- Branch freshness is stale against current remote upstream `main`: branch base `a5db2d839a0a20ddb0090faa5bb233280601e5eb`, remote `main` `ca0ae7269ca3e9487645cf66088fdfc338951da9`.
- `precheck-pr` quick and full have not run yet; they are the session's core task.
- `gh pr checks <PR>` is not applicable because no PR exists.
- Diff-scoped precheck probes found warning candidates to evaluate:
  - a test-only `except Exception` availability guard in `tests/model_executor/quantization/test_nvfp4_blockwise_config.py`;
  - several `SimpleNamespace` test fakes;
  - no added `Any`, no hot-path copy, no event-loop blocking hits.

## Clarifications

### Upstream Drift

Decision: allow a clean rebase in `GPU-S5`.

If the rebase is conflict-free and the diff remains model-agnostic, continue in this session. If conflicts or semantic overlap appear, stop and route back to `GPU-S4`.

Rejected alternatives:

- Strictly route back to `GPU-S4` for any upstream movement. This is safer but would turn a likely mechanical branch-freshness issue into a full stop.
- Open the PR from the stale branch. Rejected because branch freshness is part of `precheck-pr`.

### Owner Go-Ahead

Decision: prepare everything, then stop for an explicit owner go-ahead immediately before opening the PR.

This current brainstorming approval is not the PR-opening approval.

### CI Evidence Before PR

Decision: run local equivalents before PR, then use GitHub CI after PR.

Run local `pre-commit` and local wheel build where practical before asking for the PR-opening go-ahead. After PR creation, wait on `gh pr checks` to prove upstream CI and DCO state.

## Approaches Considered

### Approach A: Freshen, Precheck, Then PR Gate

Cleanly rebase onto current upstream `main`; run quick and full `precheck-pr`; fix only blockers or contract-relevant warnings; run targeted tests, `pre-commit`, and local wheel build where practical; prepare the PR title/body; stop for the owner gate; open the PR; then wait for `gh pr checks`.

Pros:

- Satisfies the branch-freshness concern before PR.
- Keeps PR creation behind the explicit human gate.
- Produces the strongest evidence for `GATE-GPU-S5-PR`.

Cons:

- A clean rebase is a narrow expansion of the `GPU-S5` execution work.
- Local wheel build can be expensive or environment-sensitive.

### Approach B: Strict No-Rebase Session

Stop now and route back to `GPU-S4` because upstream moved.

Pros:

- Most literal reading of the original `GPU-S5` out-of-scope line.

Cons:

- Likely wastes a session on mechanical branch freshness.
- Does not advance the PR gate if the rebase is conflict-free.

### Approach C: Submit Current Branch As-Is

Run precheck and open from the current `f7e024dd` branch if GitHub reports it mergeable.

Pros:

- Fastest.

Cons:

- Weak branch-freshness evidence.
- Likely to fail or warn in `precheck-pr`.

## Chosen Design

Use Approach A.

Execution order:

1. Create session 5 artifacts in this repository.
2. Fetch upstream in the external fork and attempt a clean rebase onto current `upstream/main`.
3. If the rebase conflicts or changes the semantic contribution scope, classify and stop.
4. Run `precheck-pr` quick, then full, recording each result.
5. Treat the diff as a General PR unless current upstream guidance or `precheck-pr` classifies it differently.
6. Fix only concrete blockers or High/Critical review findings.
7. Run targeted quant tests, `compileall`, no-Cosmos3/no-private-reference sweeps, local `pre-commit`, and local wheel build where practical.
8. Verify DCO sign-off on every branch commit.
9. Prepare PR title/body with a valid upstream prefix. Initial title candidate: `[Kernel] Add FP8/NVFP4 blockwise quant loaders`.
10. Ask for the owner go-ahead immediately before `gh pr create`.
11. If approved, open the PR and monitor `gh pr checks`.
12. Record final evidence, sharded review, adversarial verification, handoff, and eval seeds.

## Architecture

This repository remains the control and evidence workspace. The external fork remains the code workspace. GitHub PR creation is an outward-facing Action with a hard human synchronization point immediately before it.

Functional-thinking boundary:

- Pure calculations in the fork remain target selection, sidecar parsing, remapping, shape checks, and dequant math.
- Actions are git operations, filesystem reads, CI commands, GitHub API calls, and PR submission.
- Any new code fix must be test-first. If no code fix is needed, existing `GPU-S4` tests become the identified spec-derived tests.

Concept-design boundary:

- No new concept decomposition is needed. `GPU-S4` already established the purpose-bound contribution surface: model-agnostic quant-loader support. `GPU-S5` only synchronizes verification, owner approval, and upstream submission.

## Risks

- Current upstream `main` may now overlap the branch. Mitigation: rebase first and inspect the post-rebase diff before precheck.
- `precheck-pr` may classify the PR as Diffusion Model because files under `vllm_omni/diffusion/` changed. Mitigation: run the skill's classification and record the chosen checklist.
- Local wheel build may fail for environment reasons. Mitigation: classify as ENVIRONMENT if the failure is missing service/toolchain rather than product regression; do not rewrite product code for environment-only failures.
- The PR can be opened before the owner gate by accident. Mitigation: keep `gh pr create` out of scripts and stop for explicit owner go-ahead.
- GitHub CI can fail after PR creation. Mitigation: classify failures before fixing; do not patch unrelated upstream flakes as product bugs.

## Validated Design

The approved design is a gated submission path: clean rebase allowed only if conflict-free, quick and full `precheck-pr`, local CI equivalents before PR, explicit owner gate immediately before `gh pr create`, and GitHub checks after PR creation. Any conflict, Cosmos3 leakage, missing DCO sign-off, or scope expansion stops the session or routes back to `GPU-S4`.
