# Session 4 Execution Contract

## Planned File Changes

This repository:

- `docs/session_4/**`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/eval_seed_cases.md`
- `docs/handoff.md`

External fork:

- Branch from `vllm-project/vllm-omni` `main`, pushed to `fengwang/vllm-omni`.
- Candidate paths:
  - `vllm_omni/quantization/fp8_blockwise_w8a16.py`
  - `vllm_omni/quantization/nvfp4_blockwise.py`
  - `vllm_omni/quantization/__init__.py`
  - `vllm_omni/quantization/factory.py`
  - `vllm_omni/quantization/component_config.py`
  - `vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt.py`
  - `vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native.py`
  - `vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native_fp8_w8a16.py`
  - `vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native_nvfp4.py`
  - `vllm_omni/diffusion/model_loader/checkpoint_adapters/__init__.py`
  - `vllm_omni/patch.py`
  - narrow tests under `tests/**` for these surfaces.

## Allowed Blast Radius

Allowed:

- External `fengwang/vllm-omni` fork feature branch.
- External fork tests for touched quant-loader surfaces.
- `docs/session_4/**`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/eval_seed_cases.md`
- `docs/handoff.md`

Forbidden:

- This repository's runtime source: `api/**`, `webui/**`, `deploy/**`, `schemas/**`.
- This repository's checkpoints or generated artifacts.
- `docs/archive/phase-1/**`.
- Cosmos3-specific model, adapter, pipeline, or guard code in the external branch.
- Upstream `vllm-project/vllm-omni` direct writes.

## First Test To Write Or Identify

Identify the upstream-state finding check before any code change:

```bash
cd <external-vllm-omni-checkout>
rtk git log --oneline upstream/main -- vllm_omni/quantization
rtk rg -n "fp8_blockwise|nvfp4_blockwise|modelopt_native|ModelOptNative|NvFp4|FP8" vllm_omni
```

If isolation proceeds, the first code-level test is the narrow FP8 W8A16 target-selection/config test:

```bash
cd <external-vllm-omni-checkout>
rtk python -m pytest -q tests/diffusion/quantization/test_fp8_blockwise_w8a16.py
```

## Checks After Each Task

- Task 1: upstream fetch, exact search, semantic search, `docs/session_4/upstream_state.md` present.
- Task 2: branch diff file list, no-Cosmos3 sweep, targeted imported test collection.
- Task 3: targeted pytest set, `python -m compileall vllm_omni`, no-secret and no-private-path sweep.
- Task 4: external branch push, main repo `make scan`, sharded review, adversarial verification.

## Review Axes

- Correctness: upstream coverage conclusion, loader registration, adapter selection, shape and dtype checks, conflict resolutions.
- Security/safety: no secrets, private paths, tokens, model weights, unsafe shell behavior, or direct upstream writes.
- Tests: narrow tests fail on missing loader behavior and avoid Cosmos3 fixtures.
- Architecture/maintainability: model-agnostic boundaries, ACD separation, no Cosmos3 coupling, minimal patch hunk.
- Performance: no avoidable hot-path dequant, no added heavy import side effects, clamp scans only intended tensors.

## Adversarial Verifier Brief

Try to falsify this claim:

`GATE-GPU-S4-UPSTREAM-SCOPE` passes because upstream state was checked before contribution code, and either upstream already covers the feature or a pushed, isolated, rebased, compiling branch exists with no Cosmos3-specific code.

Verifier inputs:

- `docs/session_4_contract.yaml`
- `docs/project_contract.md`
- `docs/session_4/upstream_state.md`
- `docs/session_4/branch_notes.md`
- `docs/session_4/checks.md`
- External branch diff against `upstream/main`
- Final command outputs summarized in evidence

Verifier focus:

- Was upstream state checked first?
- Does the branch contain Cosmos3-specific code?
- Did tests and `compileall` actually run on the isolated branch?
- Is the pushed branch and commit recorded?
- Are any done claims unsupported by evidence?

## Concrete Done Condition

Done means `GATE-GPU-S4-UPSTREAM-SCOPE` passes:

- Upstream-state finding exists with upstream SHA and deterministic command evidence.
- If upstream already covers the feature, no contribution code is created and the finding is recorded as the done condition.
- If upstream does not cover it, a branch based on current upstream `main` exists on `fengwang/vllm-omni`, compiles with `python -m compileall vllm_omni`, passes targeted quant-loader tests, and contains no Cosmos3-specific code.
- Conflict and semantic-drift notes are recorded.
- Sharded review and adversarial verification are saved.
- `docs/handoff.md` names the branch, commit, checks run, checks not run, and next-session warnings.

