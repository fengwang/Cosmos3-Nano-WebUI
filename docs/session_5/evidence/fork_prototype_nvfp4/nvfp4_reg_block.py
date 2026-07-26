

# --- AM-S5 spike: register the Cosmos3 NVFP4-blockwise W4A16 text-path method ---
# Registered inline (mirrors the AM-S2 fp8_blockwise_w8a16 block) to avoid a circular
# import during this package's own initialization. Enables `vllm serve <nvfp4-blockwise-ckpt>
# --quantization nvfp4_blockwise_w4a16` (no --omni) to serve TEXT off the FP4-packed
# understanding tower via ModelOptNvFp4W4A16LinearMethod (Marlin FP4 W4A16). See docs/session_5.
try:
    from vllm.model_executor.layers.quantization.nvfp4_blockwise_w4a16_vllm import (
        Nvfp4BlockwiseW4A16Config as _Nvfp4BwW4A16Config,
    )

    _CUSTOMIZED_METHOD_TO_QUANT_CONFIG["nvfp4_blockwise_w4a16"] = _Nvfp4BwW4A16Config
    if "nvfp4_blockwise_w4a16" not in QUANTIZATION_METHODS:
        QUANTIZATION_METHODS.append("nvfp4_blockwise_w4a16")
    logger.info("AM-S5: registered --quantization nvfp4_blockwise_w4a16")
except Exception as _e:  # pragma: no cover - spike safety net
    logger.warning("AM-S5: failed to register nvfp4_blockwise_w4a16: %s", _e)
