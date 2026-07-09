"""Unit tests for the pure mutation core (no I/O, no torch, kilobyte fixtures).

Derived from docs/session_5/specs/fp8-checkpoint-mutation.md. The FP8-dist transformer has 0 action
tensors + an FP8 lm_head (F8_E4M3 + 2 quantizer sidecars); the mutation appends the 5 BF16 action
tensors and swaps lm_head to BF16, both sourced from the BF16 model, preserving all else byte-identical.
"""
from __future__ import annotations

import pytest

from checkpoint_prep.mutation import (
    ACTION_TENSORS,
    DROPPED_LMHEAD,
    MutationError,
    build_layout,
    plan_mutation,
    updated_sidecars,
)

# Config values probed from /data/models/Cosmos3-Nano/transformer/config.json (BF16 source).
CFG = {"action_dim": 64, "hidden_size": 4096, "num_embodiment_domains": 32, "vocab_size": 151936}


def _entry(dtype, shape, start, end):
    return {"dtype": dtype, "shape": shape, "data_offsets": [start, end]}


def _fp8_header():
    """Minimal FP8-like header: one MLP target + FP8 lm_head + 2 quantizer sidecars + BF16 kept."""
    return {
        "layers.0.mlp.gate_proj.weight": _entry("F8_E4M3", [12288, 4096], 0, 100),
        "layers.0.mlp.gate_proj.weight_quantizer._scale": _entry("BF16", [96, 32], 100, 140),
        "self_attn.q_proj.weight": _entry("BF16", [4096, 4096], 140, 240),
        "embed_tokens.weight": _entry("BF16", [151936, 4096], 240, 340),
        "lm_head.weight": _entry("F8_E4M3", [151936, 4096], 340, 440),
        "lm_head.weight_quantizer._amax": _entry("BF16", [1187, 1, 32, 1], 440, 450),
        "lm_head.weight_quantizer._scale": _entry("BF16", [1187, 32], 450, 460),
    }


def _bf16_source():
    """BF16 source refs: the 5 action tensors + BF16 lm_head with config-matching shapes."""
    h, d, n, v = CFG["hidden_size"], CFG["action_dim"], CFG["num_embodiment_domains"], CFG["vocab_size"]
    return {
        "action_modality_embed": _entry("BF16", [h], 0, 8192),
        "action_proj_in.bias.weight": _entry("BF16", [n, h], 0, 262144),
        "action_proj_in.fc.weight": _entry("BF16", [n, d * h], 0, 16777216),
        "action_proj_out.bias.weight": _entry("BF16", [n, d], 0, 4096),
        "action_proj_out.fc.weight": _entry("BF16", [n, d * h], 0, 16777216),
        "lm_head.weight": _entry("BF16", [v, h], 0, 1244659712),
    }


def test_plan_add_drop_keep_sets():
    plan = plan_mutation(_fp8_header(), _bf16_source(), CFG)
    assert set(plan.add) == set(ACTION_TENSORS) | {"lm_head.weight"}
    assert set(plan.drop) == set(DROPPED_LMHEAD)
    # keeps everything except the 3 dropped FP8 lm_head tensors
    assert "layers.0.mlp.gate_proj.weight" in plan.keep
    assert "layers.0.mlp.gate_proj.weight_quantizer._scale" in plan.keep
    assert "embed_tokens.weight" in plan.keep
    assert "self_attn.q_proj.weight" in plan.keep
    for dropped in DROPPED_LMHEAD:
        assert dropped not in plan.keep


def test_plan_rejects_wrong_dtype():
    src = _bf16_source()
    src["action_proj_in.fc.weight"]["dtype"] = "F8_E4M3"
    with pytest.raises(MutationError):
        plan_mutation(_fp8_header(), src, CFG)


def test_plan_rejects_wrong_shape():
    src = _bf16_source()
    src["action_modality_embed"]["shape"] = [2048]  # != hidden_size
    with pytest.raises(MutationError):
        plan_mutation(_fp8_header(), src, CFG)


def test_plan_rejects_missing_source_tensor():
    src = _bf16_source()
    del src["action_proj_out.fc.weight"]
    with pytest.raises(MutationError):
        plan_mutation(_fp8_header(), src, CFG)


def test_plan_idempotent_refuse_when_already_mutated():
    src = _bf16_source()
    already = {k: _entry("BF16", src[k]["shape"], 0, 1) for k in ACTION_TENSORS}
    already["lm_head.weight"] = _entry("BF16", [CFG["vocab_size"], CFG["hidden_size"]], 0, 1)
    already["layers.0.mlp.gate_proj.weight"] = _entry("F8_E4M3", [12288, 4096], 0, 100)
    with pytest.raises(MutationError):
        plan_mutation(already, src, CFG)


def test_build_layout_contiguous_and_aligned():
    fp8, src = _fp8_header(), _bf16_source()
    layout = build_layout(plan_mutation(fp8, src, CFG), fp8, src)
    offs = sorted(v["data_offsets"] for v in layout.entries.values())
    assert offs[0][0] == 0
    for a, b in zip(offs, offs[1:]):
        assert a[1] == b[0]  # contiguous, no gaps / no overlaps
    assert offs[-1][1] == layout.data_len
    assert layout.header_len % 8 == 0  # 8-byte aligned header (safetensors convention)
    # the FP8 lm_head quantizer sidecars are gone; lm_head.weight is present as the restored BF16 tensor
    assert "lm_head.weight_quantizer._amax" not in layout.entries
    assert "lm_head.weight_quantizer._scale" not in layout.entries
    assert layout.entries["lm_head.weight"]["dtype"] == "BF16"
    assert layout.entries["action_proj_in.fc.weight"]["shape"] == [32, 64 * 4096]


def test_build_layout_keeps_original_bytes_size():
    """Kept tensor sizes are preserved (byte-length identity precondition)."""
    fp8, src = _fp8_header(), _bf16_source()
    layout = build_layout(plan_mutation(fp8, src, CFG), fp8, src)
    for name in ("layers.0.mlp.gate_proj.weight", "embed_tokens.weight", "self_attn.q_proj.weight"):
        s0, e0 = fp8[name]["data_offsets"]
        s1, e1 = layout.entries[name]["data_offsets"]
        assert (e1 - s1) == (e0 - s0)


def test_updated_sidecars_preserve_recipe_and_drop_lmhead():
    qc = {
        "recipe": "fp8_blockwise_mixed",
        "weight_only": True,
        "quant_lmhead": True,
        "mixed_precision": {"quantized": ["mlp.*", "mlp_moe_gen.*", "lm_head"],
                            "bf16_kept": ["self_attn.*"], "n_quantized": 217},
        "scale_layout": {"granularity": "blockwise-128x128", "n_quantized_weight": 217,
                         "n_scale": 434, "total_scale_elements": 701536,
                         "example_shapes": {"151936x4096": {"module_example": "lm_head"},
                                            "12288x4096": {"module_example": "layers.0.mlp.gate_proj"}}},
    }
    qmd = {"n_weight_quantized": 217, "expected_quantized_count": 217,
           "dropped_action_keys": list(ACTION_TENSORS)}
    new_qc, new_qmd = updated_sidecars(qc, qmd, dropped_scale_elements=75968)
    # load-bearing: recipe unchanged so fp8_w8a16_selected still selects
    assert new_qc["recipe"] == "fp8_blockwise_mixed"
    assert new_qc["quant_lmhead"] is False
    assert "lm_head" not in new_qc["mixed_precision"]["quantized"]
    assert new_qc["mixed_precision"]["n_quantized"] == 216
    assert new_qc["scale_layout"]["n_quantized_weight"] == 216
    assert new_qc["scale_layout"]["n_scale"] == 432
    assert new_qc["scale_layout"]["total_scale_elements"] == 701536 - 75968
    assert "151936x4096" not in new_qc["scale_layout"]["example_shapes"]  # lm_head example dropped
    assert new_qmd["n_weight_quantized"] == 216
    assert new_qmd["expected_quantized_count"] == 216
    assert not new_qmd["dropped_action_keys"]  # resolved
    assert set(new_qmd["appended_action_keys"]) == set(ACTION_TENSORS)
    assert new_qmd["lm_head_restored_bf16"] is True
    # original inputs not mutated in place
    assert qc["quant_lmhead"] is True and qmd["n_weight_quantized"] == 217
