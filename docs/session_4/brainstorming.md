# Session 4 Brainstorming

## Startup Snapshot

- Main repository branch: `GPU-S4`.
- Main repository state: clean at startup by `git status --short`.
- Recent main commit: `c348efa` (`feat(gpu-s3): joint validation on RTX 5090 -- GATE-GPU-S3-VALIDATION passes`).
- External fork checkout: `<external-vllm-omni-checkout>`.
- External fork branch: `mig-s2-cosmos3-quant-pin`.
- External fork HEAD: `697035018b70cef76b974a909d23371a9984c3f2`.
- External fork state: clean at startup.
- External fork remote: `origin` points to `git@github.com:fengwang/vllm-omni.git`.
- Upstream current main ref from read-only `git ls-remote`: `a5db2d839a0a20ddb0090faa5bb233280601e5eb`.
- `docs/session_4/` did not exist before this session.

## Baseline Checks

Read-only checks run before editing:

```bash
rtk git status --short
rtk git log --oneline -8 --decorate
rtk git status --short --branch  # in <external-vllm-omni-checkout>
rtk git remote -v                # in <external-vllm-omni-checkout>
rtk git rev-parse HEAD           # in <external-vllm-omni-checkout>
rtk git ls-remote https://github.com/vllm-project/vllm-omni.git refs/heads/main
rtk rg -n "fp8_blockwise|nvfp4_blockwise|modelopt_native" vllm_omni
rtk rg --files tests | rg 'modelopt|fp8|nvfp4|quantization'
```

Known failing checks: none at startup.

Deferred until after design approval because they mutate the fork checkout or local environment:

```bash
git remote add upstream https://github.com/vllm-project/vllm-omni.git
git fetch upstream
git rebase upstream/main <isolated feature branch>
python -m compileall vllm_omni
make scan
```

## Clarifications

### Narrow External Fork Tests

Decision: narrow tests in the external fork are allowed for touched quant-loader surfaces.

Rejected alternative: no new tests at all. This was rejected because the session lifecycle asks for spec-derived tests after each task, and a pure documentation or grep-only approach would make isolation regressions too easy to miss.

Boundary: broad CI hygiene, `precheck-pr`, and GPU tests stay in `GPU-S5`.

### Branch Publication

Decision: after local isolation and checks pass, push the isolated feature branch to `fengwang/vllm-omni`.

Rejected alternative: local branch only. This was rejected because `GPU-S5` needs a stable remote branch and must not depend on this local workspace.

Boundary: no upstream pull request is opened in this session.

## Approaches Considered

### Approach A: Patch Synthesis Onto Upstream Main

Create a new branch from current upstream `main`. Inspect upstream state first. If upstream does not already cover the feature, import only the model-agnostic quant-loader files, registration hooks, NVFP4 NaN-clamp hunk, and narrow tests from the fork pin.

Pros:

- Produces the cleanest PR-shaped branch.
- Makes Cosmos3 leakage easy to detect.
- Keeps the final diff close to the session contract.

Cons:

- Loses some historical context from the original fork commits.
- Requires careful manual mapping of candidate files and hunks.

### Approach B: Cherry-Pick And Prune

Cherry-pick the relevant fork commits and remove Cosmos3-specific changes after conflicts.

Pros:

- Preserves commit history better.
- Can be faster if the historical commits are already well-scoped.

Cons:

- The local history appears mixed with Cosmos3 integration.
- More likely to drag in unrelated runtime changes.
- More conflict noise during rebase.

### Approach C: Stop If Upstream Already Covers It

If current upstream `main` already implements equivalent FP8/NVFP4 blockwise or ModelOpt-native detection, stop after recording evidence.

Pros:

- Avoids unnecessary contribution work.
- Satisfies `GATE-GPU-S4-UPSTREAM-SCOPE` if evidence is strong.

Cons:

- Only valid if the upstream check is precise enough to prove coverage.

## Chosen Design

Use Approach A, with Approach C as the early-exit path.

Execution order:

1. Verify upstream state with evidence before any contribution code exists.
2. If upstream already covers the contribution, document the no-PR-needed finding and stop code work.
3. If missing, branch from upstream `main`.
4. Import only the quant-loader slice:
   - `vllm_omni/quantization/fp8_blockwise_w8a16.py`
   - `vllm_omni/quantization/nvfp4_blockwise.py`
   - registration hooks in `vllm_omni/quantization/{__init__.py,factory.py,component_config.py}`
   - `vllm_omni/diffusion/model_loader/checkpoint_adapters/{modelopt.py,modelopt_native.py,modelopt_native_fp8_w8a16.py,modelopt_native_nvfp4.py}`
   - the isolated NVFP4 W4A4 `weight_scale` NaN-clamp hunk in `vllm_omni/patch.py`
   - narrow CPU tests for the touched surfaces.
5. Run no-Cosmos3 sweeps, targeted pytest, and `python -m compileall vllm_omni`.
6. Push the clean feature branch to `fengwang/vllm-omni`.
7. Record branch name, commit SHA, upstream-state finding, conflicts, and semantic drift in this repository.

## Architecture

The external fork is the code workspace. This repository is the control and evidence workspace. The isolated branch starts from upstream `main`; the fork pin is used only as the source for candidate files and tests.

The branch is not built from Cosmos3 commits. It is synthesized from a purpose-bound quant-loader slice, then tested for independence.

## Components

- Upstream-state probe: `git log`, `rg`, and targeted file inspection against `vllm-project/vllm-omni/main`.
- Isolation slice: quantization configs, checkpoint adapters, registration hooks, and NVFP4 NaN-clamp hunk.
- Guardrails: sweeps for `cosmos3`, Cosmos3 imports, model-specific hooks, and unrelated runtime surfaces.
- Tests: narrow CPU tests for touched quant-loader, adapter, and clamp behavior.

## Data Flow

```text
upstream/main + fork pin candidates
  -> isolated branch
  -> targeted checks
  -> pushed fork branch
  -> evidence and handoff for GPU-S5
```

## Error Handling

- Upstream already has equivalent support: stop code work and document a no-PR-needed finding.
- Rebase conflict inside the quant-loader surface: resolve and record the reasoning.
- Conflict requiring Cosmos3-specific judgment: stop and escalate.
- Any check failure: classify with the Failure Arbiter before fixing.

## Testing

- Pre-isolation: upstream-state evidence before code exists.
- Per task: targeted pytest, grep, or compile checks tied to the task.
- Final: no-Cosmos3 sweep, `python -m compileall vllm_omni`, targeted quant pytest, sharded review, adversarial verification.
- Push only after the local branch is clean and the checks pass or any failures are classified and documented.

## Validated Design

The approved design is patch synthesis onto upstream `main`, with a documented early exit if upstream already covers the feature. Narrow external-fork tests are in scope. The isolated branch will be pushed to `fengwang/vllm-omni` after local verification, but no upstream PR will be opened.
