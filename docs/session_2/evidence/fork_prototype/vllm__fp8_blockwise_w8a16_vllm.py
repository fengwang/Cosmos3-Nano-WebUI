# SPDX-License-Identifier: Apache-2.0
"""AM-S2 spike: a registerable `--quantization fp8_blockwise_w8a16` config for the
Cosmos3 TEXT/LLM serve path (plain `vllm serve`, no --omni).

Weight-only FP8 blockwise (W8A16): the understanding-tower LM MLP projections
(`language_model.model.layers.N.mlp.{gate_up_proj,down_proj}`) stay resident FP8
(e4m3) + a 128x128 block-scale grid and are dequantized per-op to BF16; every
other Linear (attention, lm_head) resolves to UnquantizedLinearMethod (BF16).

Reuses the tested linear method from vllm_omni. NOTE vs the omni target regex:
vLLM FUSES gate_proj+up_proj -> gate_up_proj, so we target the FUSED name here.
"""
from __future__ import annotations

import re
from typing import Any

import torch

from vllm.model_executor.layers.quantization.base_config import (
    QuantizationConfig,
    QuantizeMethodBase,
)

# The LM understanding-tower MLP projections that carry blockwise-FP8 weights.
# vLLM fuses gate/up into gate_up_proj (MergedColumnParallelLinear); down_proj is
# standalone (RowParallelLinear). Anchored to the LM tower to avoid matching the
# BF16 visual tower's MLP.
_TARGET_RE = re.compile(
    r"language_model\.model\.layers\.\d+\.mlp\.(gate_up_proj|down_proj)$"
)


class Fp8BlockwiseW8A16Config(QuantizationConfig):
    """Registerable W8A16 FP8-blockwise config (weight-only, MLP-target-inclusion)."""

    def __init__(self, weight_block_size: tuple[int, int] = (128, 128)) -> None:
        super().__init__()
        self.weight_block_size = list(weight_block_size)

    def get_name(self) -> str:
        return "fp8_blockwise_w8a16"

    def get_supported_act_dtypes(self) -> list[torch.dtype]:
        return [torch.bfloat16, torch.float16]

    @classmethod
    def get_min_capability(cls) -> int:
        return 89  # FP8 e4m3 (sm_89+, incl. sm_120 Blackwell)

    @staticmethod
    def get_config_filenames() -> list[str]:
        return []

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "Fp8BlockwiseW8A16Config":
        return cls()

    def get_quant_method(
        self, layer: torch.nn.Module, prefix: str
    ) -> QuantizeMethodBase | None:
        from vllm.model_executor.layers.linear import (
            LinearBase,
            UnquantizedLinearMethod,
        )

        if isinstance(layer, LinearBase):
            if _TARGET_RE.search(prefix):
                # Reuse the tested weight-only blockwise-FP8 linear method.
                from vllm_omni.quantization.fp8_blockwise_w8a16 import (
                    Fp8BlockwiseW8A16LinearMethod,
                )

                return Fp8BlockwiseW8A16LinearMethod(self)
            return UnquantizedLinearMethod()
        return None
