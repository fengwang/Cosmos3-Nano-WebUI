# Branch Notes

## Branch

- External checkout: `<external-vllm-omni-checkout>`
- Branch: `gpu-s4-quant-loader-isolation`
- Base upstream main: `a5db2d839a0a20ddb0090faa5bb233280601e5eb`
- Local head commit: `f7e024ddc9965622ebcfdb919e8ccb46b4232074`
- Remote branch: `origin/gpu-s4-quant-loader-isolation`
- Remote head commit: `f7e024ddc9965622ebcfdb919e8ccb46b4232074`
- GitHub branch URL: `https://github.com/fengwang/vllm-omni/tree/gpu-s4-quant-loader-isolation`
- Commits:
  - `bb4e170c5ac40fdac630c8c2030216521b9cc297` — `feat: add model-agnostic FP8/NVFP4 quant loaders`
  - `f7e024ddc9965622ebcfdb919e8ccb46b4232074` — `fix: wire blockwise quant config selection`
- Sign-off: present on both commits
- PR status: not opened; `GPU-S5` owns PR creation and precheck.

## Conflict Notes

- No git rebase conflicts occurred. The branch was synthesized from `upstream/main`.
- `vllm_omni/patch.py` was not changed because upstream already contains the NVFP4 W4A4 `weight_scale` NaN-clamp hunk.
- `vllm_omni/quantization/factory.py`, `component_config.py`, and `__init__.py` were not changed because upstream already has the generic ModelOpt method detection used by this slice.

## Semantic Drift

- Upstream already has generic `ModelOptFp8CheckpointAdapter`, `ModelOptNvFp4CheckpointAdapter`, `ModelOptMixedPrecisionCheckpointAdapter`, and factory detection for `FP8`, `NVFP4`, and `MIXED_PRECISION`.
- The missing surface is native sidecar handling for `fp8_blockwise_mixed` and `nvfp4_blockwise_mixed_v1`, plus FP8 W8A16 resident routing.
- The imported slice was scrubbed of Cosmos3-specific names and old session references.
- Sharded review found that resident adapter routing must be wired to model-construction quant config routing. The final branch adds model-agnostic wiring in `TransformerConfig.from_dict`, `OmniDiffusionConfig`, and its structured config mirror.
- Sharded performance review found the FP8 W8A16 resident path dequantized full weights on every forward while being selected by default. The final branch makes that path explicit opt-in with `VLLM_OMNI_FP8_BLOCKWISE_W8A16=1`; load-time dequant remains default.
- Sharded correctness review found NVFP4 config target selection excluded `mlp_moe_gen` even though the adapter accepts that family. The final branch includes `mlp_moe_gen` in NVFP4 target-inclusion selection and tests it.

## Scope Proof

Changed external files:

```text
tests/diffusion/model_loader/test_modelopt_native.py
tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py
tests/diffusion/model_loader/test_modelopt_native_nvfp4.py
tests/diffusion/quantization/test_fp8_blockwise_w8a16.py
tests/model_executor/quantization/test_nvfp4_blockwise_config.py
vllm_omni/config/omni_config.py
vllm_omni/diffusion/data.py
vllm_omni/diffusion/model_loader/checkpoint_adapters/__init__.py
vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native.py
vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native_fp8_w8a16.py
vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native_nvfp4.py
vllm_omni/quantization/fp8_blockwise_w8a16.py
vllm_omni/quantization/nvfp4_blockwise.py
```

Pre-commit scope sweep:

```bash
rtk bash -lc 'set -o pipefail; diff=$(git diff upstream/main...HEAD) || exit 2; printf "%s" "$diff" | rg -n "cosmos3|Cosmos3|COSMOS3|docs/session_[0-9]|/data/|/workspace/|HF_TOKEN|private"; rc=$?; if [ "$rc" -eq 1 ]; then echo "PASS: zero forbidden matches"; exit 0; elif [ "$rc" -eq 0 ]; then echo "FAIL: forbidden matches"; exit 1; else echo "ERROR: rg failed with exit $rc"; exit "$rc"; fi'
```

Result: `PASS: zero forbidden matches`.

Post-push status:

```text
## gpu-s4-quant-loader-isolation...origin/gpu-s4-quant-loader-isolation
f7e024ddc9965622ebcfdb919e8ccb46b4232074
```
