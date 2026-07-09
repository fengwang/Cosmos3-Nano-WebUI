"""Host (torch-free) tests for the action graft loader's pure parts.

`merge_state_dicts` is a pure Calculation (disjoint union; raises on key collision). The module must
import torch-free (heavy imports deferred into functions), like the diffusers oracle loader.
Refs: session_4/specs/action-enablement.md.
"""
from __future__ import annotations

import pytest

from engines.diffusers_action.loader import ActionEngineConfig, merge_state_dicts


def test_merge_disjoint_union():
    gen = {"blocks.0.weight": 1, "blocks.0.weight_quantizer._amax": 2}
    adapters = {"action_proj_in.fc.weight": 3, "action_modality_embed": 4}
    merged = merge_state_dicts(gen, adapters)
    assert merged == {**gen, **adapters}
    # inputs are not mutated (Calculation discipline)
    assert "action_proj_in.fc.weight" not in gen


def test_merge_raises_on_collision():
    gen = {"shared.key": 1}
    adapters = {"shared.key": 2}
    with pytest.raises(ValueError, match="collision"):
        merge_state_dicts(gen, adapters)


def test_config_defaults_to_trusted_base_action_mount():
    cfg = ActionEngineConfig(quant_dir="/data/models/Cosmos3-Nano-NVFP4-Blockwise")
    assert cfg.base_action_dir == "/data/models/Cosmos3-Nano/transformer"
    assert cfg.device == "cuda"


def test_module_imports_torch_free():
    # Importing the loader on the host (no torch) must succeed — heavy imports are deferred.
    import importlib

    mod = importlib.import_module("engines.diffusers_action.loader")
    assert hasattr(mod, "load_action_transformer")
