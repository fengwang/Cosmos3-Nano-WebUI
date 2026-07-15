## Summary

- Add ModelOpt-native FP8 blockwise sidecar loading for `fp8_blockwise_mixed` checkpoints.
- Add NVFP4 blockwise sidecar loading and W4A16 target-inclusion config for `nvfp4_blockwise_mixed_v1` checkpoints.
- Keep the FP8 resident W8A16 path opt-in while load-time dequant remains the default.

## Tests

- `.venv-mig-s2/bin/python -m pytest -q tests/diffusion/quantization/test_fp8_blockwise_w8a16.py tests/diffusion/model_loader/test_modelopt_native.py tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py tests/diffusion/model_loader/test_modelopt_native_nvfp4.py tests/model_executor/quantization/test_nvfp4_blockwise_config.py tests/model_executor/quantization/test_modelopt_nvfp4_nan_clamp.py`  
  `128 passed, 18 warnings`
- `.venv-mig-s2/bin/python -m compileall -q vllm_omni`
- `.venv-mig-s2/bin/python -m pre_commit run --files $(git diff --name-only "$BASE"...HEAD)`
- `bash scripts/build_wheel.sh --python .venv-mig-s2/bin/python`

## Notes

- DCO signed on all commits.
- No downstream model-specific code or model weights included.
- No GPU benchmark claim in this PR.
