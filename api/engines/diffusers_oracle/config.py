"""Oracle configuration + precision detection (ACD: Data + a pure Calculation + one env Action).

Torch-free: only depends on `engines.base`. The *precision* is detected from the checkpoint's
`quantization_config.json` (not set by the caller) so the served precision is grounded in the
artifact. Refs: session_2/specs/diffusers-oracle-adapter.md; evidence_map D-DEFAULTMODEL.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from engines.base import Precision

# D-DEFAULTMODEL: NVFP4 is the default served checkpoint; FP8 is selectable via the env.
DEFAULT_MODEL_DIR = "/data/models/Cosmos3-Nano-NVFP4-Blockwise"


@dataclass(frozen=True)
class OracleConfig:
    """Where/how to load the oracle (inert Data). Precision is detected at load, not set here."""

    model_dir: str
    device: str = "cuda"

    @staticmethod
    def from_env() -> "OracleConfig":
        """Action: read ``COSMOS3_MODEL_DIR`` (default NVFP4-Blockwise) + device from the environment."""
        return OracleConfig(
            model_dir=os.environ.get("COSMOS3_MODEL_DIR", DEFAULT_MODEL_DIR),
            device=os.environ.get("COSMOS3_DEVICE", "cuda"),
        )


def precision_from_quant_config(cfg: dict) -> tuple[Precision, str]:
    """Pure: map a ``quantization_config.json`` dict to ``(Precision, granularity)``.

    ``recipe`` starting with ``nvfp4`` -> NVFP4; ``fp8`` -> FP8. Granularity is read from
    ``scale_layout`` (``per-block-16`` for NVFP4, ``per-tensor`` for FP8). Raises ``ValueError``
    on an unknown recipe (a precision we will not silently serve).
    """
    recipe = str(cfg.get("recipe", ""))
    granularity = str(cfg.get("scale_layout", {}).get("granularity", ""))
    if recipe.startswith("nvfp4"):
        return Precision.NVFP4, granularity
    if recipe == "fp8":
        return Precision.FP8, granularity
    raise ValueError(f"unknown quantization recipe: {recipe!r}")
