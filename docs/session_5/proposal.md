# Session 5 Proposal

## Motivation

`GPU-S4` produced an isolated, pushed branch with model-agnostic FP8/NVFP4 blockwise quant-loader support. `GPU-S5` is the outward-facing gate: it must run the fork's `precheck-pr` skill, satisfy DCO and CI requirements, and open an upstream PR only after an explicit owner go-ahead recorded immediately before submission.

The main risk is irreversible public action. A clean branch and passing checks are necessary but not enough; the PR must not be opened until the owner explicitly approves at the final gate.

## Agreed Changes

1. Freshen the external branch against current `vllm-project/vllm-omni` `main` if and only if the rebase is clean and does not change contribution scope.
2. Run `precheck-pr` quick and full from the fork checkout.
3. Evaluate and fix only blocking or High/Critical findings that fall inside the `GPU-S5` blast radius.
4. Run targeted quant tests, `compileall`, diff-scope guard sweeps, local `pre-commit`, and local wheel build where practical.
5. Confirm every PR commit carries a `Signed-off-by` trailer.
6. Determine and record the PR title prefix from upstream guidance.
7. Prepare PR title/body but stop for the explicit owner go-ahead immediately before opening.
8. If approved, open the PR against `vllm-project/vllm-omni` `main` and record the PR URL.
9. Use `gh pr checks <PR>` after opening to prove or classify upstream CI status.

## Capabilities

### New Capabilities

- **Submission Branch Freshness:** Rebase the `GPU-S4` branch onto current upstream `main` only when clean, preserving the model-agnostic contribution scope.
- **Precheck And Local CI Gate:** Run quick and full `precheck-pr`, targeted tests, local pre-commit, local wheel build, DCO checks, and guard sweeps before submission.
- **Owner-Gated PR Submission:** Prepare and open the upstream PR only after an explicit owner go-ahead immediately before `gh pr create`, then record GitHub CI status.

### Modified Capabilities

- **External Quant Contribution Branch:** The branch produced by `GPU-S4` may receive mechanical rebase commits or narrow precheck/CI fixes. It MUST remain free of Cosmos3-specific code and MUST remain DCO-signed.

## Impact

Affected external fork code may include only the existing `GPU-S4` branch files if precheck or CI finds concrete issues:

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

Affected documentation in this repository:

- `docs/session_5/**`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/eval_seed_cases.md`
- `docs/handoff.md`

No production dependency changes are planned. No WebUI runtime source, Dockerfile, schemas, checkpoints, generated media, or archived Phase-1 files are in scope.
