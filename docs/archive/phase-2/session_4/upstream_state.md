# Upstream State Finding

## Refs

- Fork checkout: `<external-vllm-omni-checkout>`
- Fork branch at startup: `mig-s2-cosmos3-quant-pin`
- Fork pin: `697035018b70cef76b974a909d23371a9984c3f2`
- Upstream remote: `https://github.com/vllm-project/vllm-omni.git`
- Upstream main: `a5db2d839a0a20ddb0090faa5bb233280601e5eb`

## Commands

```bash
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git remote -v
rtk git fetch upstream
rtk git rev-parse upstream/main
rtk git log --oneline upstream/main -- vllm_omni/quantization
rtk git ls-tree -r --name-only upstream/main -- vllm_omni/diffusion/model_loader/checkpoint_adapters
rtk git ls-tree -r --name-only upstream/main -- vllm_omni/quantization
rtk git grep -n -E "fp8_blockwise|nvfp4_blockwise|modelopt_native|ModelOptNative|nvfp4_blockwise_mixed_v1|fp8_blockwise_mixed" upstream/main -- vllm_omni || true
rtk git show upstream/main:vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt.py
rtk git show upstream/main:vllm_omni/patch.py | rg -n "nvfp4|weight_scale|NaN|clamp|_clamp"
rtk git diff --name-status upstream/main 697035018b70cef76b974a909d23371a9984c3f2 -- vllm_omni/quantization vllm_omni/diffusion/model_loader/checkpoint_adapters vllm_omni/patch.py tests/diffusion/model_loader tests/diffusion/quantization tests/model_executor/quantization
```

## Findings

### Exact Filename Matches

Current upstream `main` does not contain these fork candidate files:

- `vllm_omni/quantization/fp8_blockwise_w8a16.py`
- `vllm_omni/quantization/nvfp4_blockwise.py`
- `vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native.py`
- `vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native_fp8_w8a16.py`
- `vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native_nvfp4.py`

The upstream checkpoint-adapter tree at `a5db2d839a0a20ddb0090faa5bb233280601e5eb` contains only:

```text
vllm_omni/diffusion/model_loader/checkpoint_adapters/__init__.py
vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt.py
```

The upstream quantization tree does not contain `fp8_blockwise_w8a16.py` or `nvfp4_blockwise.py`.

### Semantic ModelOpt Matches

Upstream does contain generic ModelOpt adapter and factory support:

- `ModelOptFp8CheckpointAdapter`
- `ModelOptNvFp4CheckpointAdapter`
- `ModelOptMixedPrecisionCheckpointAdapter`
- `factory._detect_modelopt_method` for `FP8`, `NVFP4`, and `MIXED_PRECISION`

This support depends on an active `quant_config` with methods such as `modelopt`, `modelopt_fp4`, or `modelopt_mixed`. It does not implement the fork's native sidecar paths:

- root `quantization_config.json` recipe `fp8_blockwise_mixed`
- transformer sidecar `nvfp4_blockwise_mixed_v1.json`
- FP8 W8A16 resident MLP target selection
- NVFP4 W4A16 packed triplet remapping from `weight_packed`, `weight_block_scale`, and `weight_global_scale`

### NVFP4 NaN-Clamp Hunk

Upstream already contains the NVFP4 W4A4 `weight_scale` NaN-clamp logic in `vllm_omni/patch.py`. It includes `_clamp_nvfp4_weight_scale_nans`, `_clamp_installed`, upstream self-extinguish detection, and `VLLM_OMNI_SKIP_NVFP4_NAN_CLAMP`.

This means the isolated branch does not need to import the `patch.py` clamp hunk unless later checks show a missing test-only adjustment.

## Conclusion

- Result: `missing`
- Rationale: upstream already has generic ModelOpt FP8/NVFP4 config detection and the NVFP4 NaN-clamp hunk, but it does not contain the native blockwise sidecar adapters or the FP8/NVFP4 blockwise quant config files required by `GPU-S4`.
- Next action: proceed with isolated branch construction from `upstream/main`, importing only the missing model-agnostic native loader slice and narrow tests. Treat `vllm_omni/patch.py` as already covered upstream unless a targeted test proves a gap.

