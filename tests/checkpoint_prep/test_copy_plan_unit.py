"""Unit tests for the pure copy planner (spec: self-contained-checkpoint-copy, "The copy plan covers
the borrowed-file set and excludes the quantized transformer")."""
from __future__ import annotations

import pytest

from checkpoint_prep.copy_shared import CopyError, plan_copy, snapshot_transformer_hashes
from checkpoint_prep.safetensors_io import build_header_bytes


def test_snapshot_handles_model_safetensors_naming(tmp_path):
    """NVFP4-dist names its transformer `model.safetensors` (not diffusion_pytorch_model.safetensors);
    the INV-11 baseline must still hash it — regression for the vacuous-snapshot bug."""
    tdir = tmp_path / "transformer"
    tdir.mkdir(parents=True)
    entries = {"w": {"dtype": "BF16", "shape": [4], "data_offsets": [0, 8]}}
    (tdir / "model.safetensors").write_bytes(build_header_bytes(entries) + b"\x00" * 8)
    h = snapshot_transformer_hashes(tmp_path)
    assert len(h) == 1 and any(k.endswith("/w") for k in h)


def test_plan_covers_shared_reasoner_and_assets(sc_synth):
    plan = plan_copy(sc_synth.dist, sc_synth.source)
    rels = {it.rel for it in plan.items}
    # generation pipeline components + root configs + asset subset
    for d in ("vae", "text_tokenizer", "vision_encoder", "sound_tokenizer", "scheduler"):
        assert d in rels
    assert "model_index.json" in rels and "tokenizer.json" in rels and "config.json" in rels
    assert "assets/negative_prompt.json" in rels
    # reasoner bundle under reasoner/
    assert "reasoner/transformer" in rels and "reasoner/vision_encoder" in rels
    assert "reasoner/config.json" in rels and "reasoner/chat_template.json" in rels


def test_plan_never_targets_the_quantized_transformer(sc_synth):
    plan = plan_copy(sc_synth.dist, sc_synth.source)
    assert all(not it.rel.startswith("transformer/") and it.rel != "transformer" for it in plan.items)


def test_reasoner_items_source_from_bf16_root(sc_synth):
    plan = plan_copy(sc_synth.dist, sc_synth.source)
    by_rel = {it.rel: it for it in plan.items}
    # reasoner/transformer copies the BF16 <source>/transformer (not <dist>/transformer)
    assert by_rel["reasoner/transformer"].source.rstrip("/").endswith("/transformer")
    assert str(sc_synth.source) in by_rel["reasoner/transformer"].source
    assert by_rel["reasoner/config.json"].source.endswith("/config.json")


def test_plan_fails_closed_on_missing_source_file(sc_synth):
    (sc_synth.source / "merges.txt").unlink()
    with pytest.raises(CopyError) as exc:
        plan_copy(sc_synth.dist, sc_synth.source)
    assert "merges.txt" in str(exc.value)
