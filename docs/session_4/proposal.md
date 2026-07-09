# Session 4 Proposal

## Motivation

`GPU-S4` must answer whether upstream already has the FP8/NVFP4 blockwise and ModelOpt-native support before any contribution code exists. If upstream does not have it, the session must produce a clean, model-agnostic branch on the `fengwang/vllm-omni` fork that `GPU-S5` can run through PR hygiene.

The core risk is scope bleed. The fork's current pin contains useful quant-loader code, but it also contains Cosmos3 integration. The contribution branch must isolate the quant loader and prove it does not depend on Cosmos3-specific code.

## Agreed Changes

1. Inspect current `vllm-project/vllm-omni` `main` before any isolation commit.
2. Record an evidenced upstream-state finding in this repository.
3. If upstream is missing the feature, create an isolated branch from upstream `main`.
4. Import only the model-agnostic quant-loader slice and narrow tests from fork pin `697035018b70cef76b974a909d23371a9984c3f2`.
5. Resolve only conflicts inside the quant-loader blast radius.
6. Run targeted tests, no-Cosmos3 sweeps, and `compileall`.
7. Push the verified feature branch to `fengwang/vllm-omni`.
8. Record the branch name, commit SHA, conflict notes, semantic drift, checks, and remaining risks.

## Capabilities

### New Capabilities

- **Upstream State Finding:** Determine and record whether current upstream `main` already implements equivalent FP8/NVFP4 blockwise quant or ModelOpt-native detection.
- **Quant Loader Isolation:** Build a branch whose diff contains only model-agnostic quant-loader code, registration hooks, NVFP4 NaN-clamp support, and narrow tests.
- **Rebased Branch Verification:** Verify and publish the isolated branch with evidence that it compiles and does not depend on Cosmos3-specific code.

### Modified Capabilities

- None in this repository's runtime source.
- In the external fork branch only, quantization and checkpoint-loader behavior changes by adding the isolated FP8/NVFP4 loader support.

## Impact

Affected external fork code:

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
- Narrow tests under `tests/**` for the touched quant-loader surfaces.

Affected documentation in this repository:

- `docs/session_4/**`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/eval_seed_cases.md`
- `docs/handoff.md`

No production dependency changes are planned. No WebUI, API, Dockerfile, schema, checkpoint, or archived Phase-1 file changes are in scope.

