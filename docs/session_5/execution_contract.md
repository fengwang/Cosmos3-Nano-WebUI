# Session 5 Execution Contract

## Planned File Changes

This repository:

- `docs/session_5/**`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/eval_seed_cases.md`
- `docs/handoff.md`

External fork:

- Existing branch `gpu-s4-quant-loader-isolation` on `fengwang/vllm-omni`.
- Existing `GPU-S4` changed file set, only if `precheck-pr`, local CI, review, or rebase produces a concrete in-scope failure:
  - `tests/diffusion/model_loader/test_modelopt_native.py`
  - `tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py`
  - `tests/diffusion/model_loader/test_modelopt_native_nvfp4.py`
  - `tests/diffusion/quantization/test_fp8_blockwise_w8a16.py`
  - `tests/model_executor/quantization/test_nvfp4_blockwise_config.py`
  - `vllm_omni/config/omni_config.py`
  - `vllm_omni/diffusion/data.py`
  - `vllm_omni/diffusion/model_loader/checkpoint_adapters/__init__.py`
  - `vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native.py`
  - `vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native_fp8_w8a16.py`
  - `vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native_nvfp4.py`
  - `vllm_omni/quantization/fp8_blockwise_w8a16.py`
  - `vllm_omni/quantization/nvfp4_blockwise.py`
- The opened pull request against `vllm-project/vllm-omni`, if the final owner gate approves.

## Allowed Blast Radius

Allowed:

- External fork feature branch and pull request.
- External fork tests for touched quant-loader surfaces.
- `docs/session_5/**`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/eval_seed_cases.md`
- `docs/handoff.md`

Forbidden:

- This repository's runtime source: `api/**`, `webui/**`, `deploy/**`, `schemas/**`.
- This repository's checkpoints, generated media, or bulky artifacts.
- `docs/archive/phase-1/**`.
- Cosmos3-specific code anywhere in the fork or PR.
- Any external fork commit without DCO sign-off.
- Any `gh pr create` before explicit owner go-ahead immediately preceding it.

## First Test To Write Or Identify

Identify branch freshness as the first spec-derived failing check:

```bash
cd <external-vllm-omni-checkout>
test "$(git merge-base HEAD upstream/main)" = "$(git rev-parse upstream/main)"
```

At startup this is expected to fail because remote upstream `main` advanced beyond the `GPU-S4` base. The smallest implementation is a clean `git fetch upstream && git rebase upstream/main`. If the rebase conflicts, stop and route back to `GPU-S4`.

If a code change is needed later, the first code-level test MUST be the narrow targeted pytest that exercises the affected quant behavior before the fix.

## Checks After Each Task

- Task 1: `git fetch upstream`, branch freshness check, `git rebase upstream/main`, diff file-list, forbidden-residue sweep, `git diff --check`.
- Task 2: quick precheck report, full precheck report, targeted pytest, `python -m compileall vllm_omni`, local pre-commit, local wheel build or ENVIRONMENT classification.
- Task 3: DCO sweep, PR title/body validation, final branch push, recorded owner gate, `gh pr checks <PR>` if opened.
- Task 4: sharded review, High/Critical fix rechecks, adversarial verification, `make scan`, final git statuses.

## Review Axes

- Correctness: branch based on current upstream, adapter/config behavior still covered after rebase, precheck interpretation, PR body matches diff, GitHub checks status.
- Security/safety: no secrets, tokens, private paths, model weights, direct upstream pushes, or Cosmos3-specific code; owner gate before PR.
- Tests: quant method tests cover FP8/NVFP4 behavior; tests are not tautological and do not require Cosmos3 or GPU hardware.
- Architecture/maintainability: model-agnostic contribution remains narrow; ACD boundaries stay intact; no broad refactor or dependency addition.
- Performance: FP8 W8A16 remains opt-in; no new hot-path clones/deepcopy/event-loop blocking; local wheel/build changes do not introduce expensive import side effects.

## Adversarial Verifier Brief

Try to falsify this claim:

`GATE-GPU-S5-PR` passes because the branch is current, `precheck-pr` quick and full are clean, DCO is present on every commit, local CI equivalents and GitHub PR checks are green or properly classified, and the PR was opened only after an explicit owner go-ahead immediately before submission.

Verifier inputs:

- `docs/session_5_contract.yaml`
- `docs/project_contract.md`
- `docs/session_5/**`
- external branch diff against `upstream/main`
- PR URL and `gh pr checks` output if opened
- final command outputs summarized in evidence

Verifier focus:

- Was the branch rebased against current upstream, or was drift ignored?
- Was full `precheck-pr` run, not skipped after quick mode?
- Are all commits DCO-signed?
- Does any diff line contain Cosmos3-specific residue or private paths?
- Does the PR body claim anything unsupported?
- Is there a recorded owner go-ahead immediately before PR creation?
- Are GitHub checks green, or is a non-green state honestly classified?

## Concrete Done Condition

Done means `GATE-GPU-S5-PR` passes:

- The branch is current with upstream or a clean non-submission reason is recorded.
- `precheck-pr` quick and full are clean, or blockers are fixed and rechecked.
- DCO sign-off is present on every PR commit.
- Local targeted tests, `compileall`, guard sweeps, local pre-commit, and local wheel build have passed or any non-product failure is classified.
- The owner go-ahead is recorded immediately before PR creation.
- Either the PR is open with URL and GitHub checks green, or the session records why the PR did not proceed.
- Sharded review and adversarial verification are saved.
- `docs/handoff.md` names PR URL/review status or non-submission reason, checks run, checks not run, and next-session warnings.
