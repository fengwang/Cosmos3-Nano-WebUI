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


def test_config_no_bf16_base_action_default(monkeypatch):
    # AM-S3/INV-4: the action config MUST NOT default to a BF16 base dir. The quantized checkpoint now
    # self-contains the bf16 action_* adapters (E-06 refuted); action is served by the resident vllm-omni
    # model, so the dormant graft never points at a separate BF16 base by default.
    monkeypatch.delenv("COSMOS3_BASE_ACTION_DIR", raising=False)
    monkeypatch.setenv("COSMOS3_MODEL_DIR", "/data/models/Cosmos3-Nano-FP8-Blockwise")
    cfg = ActionEngineConfig.from_env()
    assert cfg.base_action_dir != "/data/models/Cosmos3-Nano/transformer"  # the retired BF16 base
    assert cfg.base_action_dir is None  # unset → no separate base; adapters live in the quantized checkpoint
    assert cfg.device == "cuda"


def test_config_base_action_dir_env_override_still_honored(monkeypatch):
    # An operator may still point the (dormant) graft at an explicit dir; only the BF16 default is retired.
    monkeypatch.setenv("COSMOS3_BASE_ACTION_DIR", "/some/explicit/dir")
    assert ActionEngineConfig.from_env().base_action_dir == "/some/explicit/dir"


def test_module_imports_torch_free():
    # Importing the loader on the host (no torch) must succeed — heavy imports are deferred.
    import importlib

    mod = importlib.import_module("engines.diffusers_action.loader")
    assert hasattr(mod, "load_action_transformer")
