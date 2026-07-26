# SPDX-License-Identifier: Apache-2.0
"""AM-S5 spike: a registerable ``--quantization nvfp4_blockwise_w4a16`` config for the
Cosmos3 TEXT/LLM serve path (plain ``vllm serve``, no --omni).

Weight-only NVFP4 (W4A16): the understanding-tower LM MLP projections
(``language_model.model.layers.N.mlp.{gate_up_proj,down_proj}``) load FP4-packed
(uint8, 2 nibbles/byte) + a per-16 FP8 block-scale grid + an FP32 per-tensor global
scale, and run vLLM's ``ModelOptNvFp4W4A16LinearMethod`` (Marlin FP4 W4A16 GEMM,
bf16 activations); every other Linear (attention, lm_head, norms) resolves to
``UnquantizedLinearMethod`` (BF16).

Mirrors the AM-S2 FP8 ``fp8_blockwise_w8a16`` patch, incl. its import discipline:
ONLY ``base_config`` is imported at module top (heavy imports — ``modelopt``,
``linear`` — are deferred into ``get_quant_method``) so registering this at
``quantization/__init__`` time cannot trigger a ``vllm.config`` circular import.

NOTE vs the fork's ``vllm_omni.quantization.nvfp4_blockwise`` (which targets the
UNFUSED ``.mlp.{gate,up,down}_proj`` of the omni/diffusion construction path): vLLM
FUSES gate_proj+up_proj -> gate_up_proj in the plain-text LM path, so we target the
FUSED name, anchored to the LM tower (never the visual/gen tower).
"""
from __future__ import annotations

import re
from typing import Any

import torch
from vllm.logger import init_logger
from vllm.model_executor.layers.quantization.base_config import (
    QuantizationConfig,
    QuantizeMethodBase,
)

logger = init_logger(__name__)

# The LM understanding-tower MLP projections that carry NVFP4-packed weights (fused
# gate_up_proj + standalone down_proj), anchored to language_model.model.layers.
_TARGET_RE = re.compile(
    r"language_model\.model\.layers\.\d+\.mlp\.(gate_up_proj|down_proj)$"
)


class Nvfp4BlockwiseW4A16Config(QuantizationConfig):
    """Registerable W4A16 NVFP4 config (weight-only, fused-MLP target-inclusion).

    Thin registry entry: it holds no ModelOpt state at construction (avoids the
    circular import) and lazily builds a real ``ModelOptNvFp4Config`` the first time
    a target layer asks for its quant method, delegating the actual load/compute to
    the pinned ``ModelOptNvFp4W4A16LinearMethod`` (Marlin FP4).
    """

    def __init__(self) -> None:
        super().__init__()
        self._modelopt_cfg: Any | None = None  # lazily built (deferred modelopt import)

    def get_name(self) -> str:
        return "nvfp4_blockwise_w4a16"

    def get_supported_act_dtypes(self) -> list[torch.dtype]:
        return [torch.bfloat16, torch.float16]

    @classmethod
    def get_min_capability(cls) -> int:
        return 80  # NVFP4 Marlin FP4 (weight-only) on sm_80+, incl. sm_120 Blackwell

    @staticmethod
    def get_config_filenames() -> list[str]:
        return []

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "Nvfp4BlockwiseW4A16Config":
        return cls()

    def _base_config(self) -> Any:
        """Lazily build the ModelOpt NVFP4 W4A16 config (deferred import, sm_120-safe)."""
        if self._modelopt_cfg is None:
            from vllm.model_executor.layers.quantization.modelopt import (
                ModelOptNvFp4Config,
            )

            cfg = ModelOptNvFp4Config(
                quant_method="W4A16_NVFP4",
                is_checkpoint_nvfp4_serialized=True,
                kv_cache_quant_algo=None,
                exclude_modules=[],
                group_size=16,
            )
            method_name = getattr(cfg.LinearMethodCls, "__name__", "")
            if method_name != "ModelOptNvFp4W4A16LinearMethod":
                raise RuntimeError(
                    "nvfp4_blockwise_w4a16 requires vLLM's ModelOptNvFp4W4A16LinearMethod "
                    f"but this build resolved {method_name!r}. Serve with the version-matched "
                    "vllm-omni image (vLLM 0.24.0 with W4A16_NVFP4 support)."
                )
            self._modelopt_cfg = cfg
            logger.info(
                "AM-S5: built nvfp4_blockwise_w4a16 config (fused text-path targeting "
                "'language_model.model.layers.*.mlp.{gate_up_proj,down_proj}', method=%s)",
                method_name,
            )
        return self._modelopt_cfg

    def get_quant_method(
        self, layer: torch.nn.Module, prefix: str
    ) -> QuantizeMethodBase | None:
        from vllm.model_executor.layers.linear import (
            LinearBase,
            UnquantizedLinearMethod,
        )

        if isinstance(layer, LinearBase):
            if _TARGET_RE.search(prefix):
                base = self._base_config()
                return base.LinearMethodCls(base)  # ModelOptNvFp4W4A16LinearMethod
            return UnquantizedLinearMethod()
        return None
