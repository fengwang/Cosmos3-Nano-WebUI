"""The diffusers reference oracle (INV-2). Import-light by design.

`load_oracle` is the public Action facade; it defers the heavy `loader`/`adapter` imports
(torch/diffusers/modelopt) so this package — and `config` — import torch-free on the host loop.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # types only; no runtime torch import here
    from .adapter import DiffusersOracleAdapter
    from .config import OracleConfig


def load_oracle(config: "OracleConfig") -> "DiffusersOracleAdapter":
    """Build + verify the diffusers oracle from ``config`` (Action: GPU load). Heavy imports deferred."""
    from .loader import build_oracle

    return build_oracle(config)
