# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from typing import Literal, get_args

from vllm.logger import init_logger
from vllm.model_executor.layers.quantization.base_config import QuantizationConfig
from vllm.platforms import current_platform

logger = init_logger(__name__)

QuantizationMethods = Literal[
    "awq",
    "auto_awq",
    "fp8",
    "fbgemm_fp8",
    "fp_quant",
    "modelopt",
    "modelopt_fp4",
    "modelopt_mxfp8",
    "modelopt_mixed",
    "auto_gptq",
    "gptq",
    "gptq_marlin",
    "awq_marlin",
    "humming",
    "compressed-tensors",
    "bitsandbytes",
    "experts_int8",
    "quark",
    "moe_wna16",
    "torchao",
    "inc",
    "mxfp4",
    "gpt_oss_mxfp4",
    "deepseek_v4_fp8",
    "online",
    # Below are online quant shorthand names (see vllm.config.quantization).
    # Listed here as strings to avoid a circular import; kept in sync with
    # _ONLINE_SHORTHANDS by the assertion in get_quantization_config().
    "fp8_per_tensor",
    "fp8_per_block",
    "fp8_per_channel",
    "int8_per_channel_weight_only",
    "mxfp8",
]
QUANTIZATION_METHODS: list[str] = list(get_args(QuantizationMethods))

DEPRECATED_QUANTIZATION_METHODS = [
    "fbgemm_fp8",
    "fp_quant",
]

# The customized quantization methods which will be added to this dict.
_CUSTOMIZED_METHOD_TO_QUANT_CONFIG = {}


def register_quantization_config(quantization: str):
    """Register a customized vllm quantization config.

    When a quantization method is not supported by vllm, you can register a customized
    quantization config to support it.

    Args:
        quantization (str): The quantization method name.

    Examples:
        >>> from vllm.model_executor.layers.quantization import (
        ...     register_quantization_config,
        ... )
        >>> from vllm.model_executor.layers.quantization import get_quantization_config
        >>> from vllm.model_executor.layers.quantization.base_config import (
        ...     QuantizationConfig,
        ... )
        >>>
        >>> @register_quantization_config("my_quant")
        ... class MyQuantConfig(QuantizationConfig):
        ...     pass
        >>>
        >>> get_quantization_config("my_quant")
        <class 'MyQuantConfig'>
    """  # noqa: E501

    def _wrapper(quant_config_cls):
        if quantization in QUANTIZATION_METHODS:
            logger.debug(
                "The quantization method '%s' already exists and will be "
                "overwritten by the quantization config %s.",
                quantization,
                quant_config_cls,
            )
        else:
            QUANTIZATION_METHODS.append(quantization)
            # Automatically assume the custom quantization config is supported
            if sq := current_platform.supported_quantization:
                sq.append(quantization)

        if not issubclass(quant_config_cls, QuantizationConfig):
            raise ValueError(
                "The quantization config must be a subclass of `QuantizationConfig`."
            )
        _CUSTOMIZED_METHOD_TO_QUANT_CONFIG[quantization] = quant_config_cls
        return quant_config_cls

    return _wrapper


def get_quantization_config(quantization: str) -> type[QuantizationConfig]:
    if quantization not in QUANTIZATION_METHODS:
        raise ValueError(f"Invalid quantization method: {quantization}")

    # lazy import to avoid triggering `torch.compile` too early
    from vllm.config.quantization import _ONLINE_SHORTHANDS
    from vllm.model_executor.layers.quantization.quark.quark import QuarkConfig
    from vllm.models.deepseek_v4 import DeepseekV4FP8Config

    from .auto_awq import AutoAWQConfig
    from .auto_gptq import AutoGPTQConfig
    from .bitsandbytes import BitsAndBytesConfig
    from .compressed_tensors.compressed_tensors import (
        CompressedTensorsConfig,
    )
    from .experts_int8 import ExpertsInt8Config
    from .fbgemm_fp8 import FBGEMMFp8Config
    from .fp8 import Fp8Config
    from .fp_quant import FPQuantConfig
    from .humming import HummingConfig
    from .inc import INCConfig
    from .modelopt import (
        ModelOptFp8Config,
        ModelOptMixedPrecisionConfig,
        ModelOptMxFp8Config,
        ModelOptNvFp4Config,
    )
    from .moe_wna16 import MoeWNA16Config
    from .mxfp4 import GptOssMxfp4Config, Mxfp4Config
    from .online.base import OnlineQuantizationConfig
    from .torchao import TorchAOConfig

    method_to_config: dict[str, type[QuantizationConfig]] = {
        "awq": AutoAWQConfig,
        "awq_marlin": AutoAWQConfig,
        "auto_awq": AutoAWQConfig,
        "fp8": Fp8Config,
        "fbgemm_fp8": FBGEMMFp8Config,
        "fp_quant": FPQuantConfig,
        "modelopt": ModelOptFp8Config,
        "modelopt_fp4": ModelOptNvFp4Config,
        "modelopt_mxfp8": ModelOptMxFp8Config,
        "modelopt_mixed": ModelOptMixedPrecisionConfig,
        "auto_gptq": AutoGPTQConfig,
        "gptq": AutoGPTQConfig,
        "gptq_marlin": AutoGPTQConfig,
        "compressed-tensors": CompressedTensorsConfig,
        "bitsandbytes": BitsAndBytesConfig,
        "experts_int8": ExpertsInt8Config,
        "quark": QuarkConfig,
        "moe_wna16": MoeWNA16Config,
        "torchao": TorchAOConfig,
        "inc": INCConfig,
        "mxfp4": Mxfp4Config,
        "gpt_oss_mxfp4": GptOssMxfp4Config,
        "deepseek_v4_fp8": DeepseekV4FP8Config,
        "humming": HummingConfig,
        "online": OnlineQuantizationConfig,
        # MiniMax-style checkpoints tag `quant_method: "mxfp8"`; load with the
        # ModelOpt MXFP8 config (same format). The "mxfp8" online shorthand
        # below only applies to the `--quantization mxfp8` CLI path.
        "mxfp8": ModelOptMxFp8Config,
    }

    # Register online shorthands (e.g. "fp8_per_tensor") as quant methods.
    # setdefault so a shorthand that is also a checkpoint method (e.g. "mxfp8")
    # keeps its checkpoint config; the shorthand still works via the
    # `--quantization` CLI path in `resolve_quantization_config`.
    for shorthand in _ONLINE_SHORTHANDS:
        method_to_config.setdefault(shorthand, OnlineQuantizationConfig)

    # Update the `method_to_config` with customized quantization methods.
    method_to_config.update(_CUSTOMIZED_METHOD_TO_QUANT_CONFIG)

    return method_to_config[quantization]


__all__ = [
    "QuantizationConfig",
    "QuantizationMethods",
    "get_quantization_config",
    "register_quantization_config",
    "QUANTIZATION_METHODS",
]

# --- AM-S2 spike: register the Cosmos3 FP8-blockwise W8A16 text-path method ---
# Registered inline (not via the decorator) to avoid a circular import during
# this package's own initialization. Enables `vllm serve <fp8-blockwise-ckpt>
# --quantization fp8_blockwise_w8a16` (no --omni) to serve TEXT off the
# quantized understanding tower. See docs/session_2 (AM-S2).
try:
    from vllm.model_executor.layers.quantization.fp8_blockwise_w8a16_vllm import (
        Fp8BlockwiseW8A16Config as _Fp8BwW8A16Config,
    )

    _CUSTOMIZED_METHOD_TO_QUANT_CONFIG["fp8_blockwise_w8a16"] = _Fp8BwW8A16Config
    if "fp8_blockwise_w8a16" not in QUANTIZATION_METHODS:
        QUANTIZATION_METHODS.append("fp8_blockwise_w8a16")
    logger.info("AM-S2: registered --quantization fp8_blockwise_w8a16")
except Exception as _e:  # pragma: no cover - spike safety net
    logger.warning("AM-S2: failed to register fp8_blockwise_w8a16: %s", _e)
