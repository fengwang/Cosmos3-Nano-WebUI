"""Integration tests for the effectful rewrite shell over tiny synthetic safetensors (real bytes).

Derived from docs/session_5/specs/fp8-checkpoint-mutation.md. Uses opaque byte payloads (the tool never
interprets tensor bytes), so no torch/dtype is needed to prove byte-identity, atomic replace, and
backup/restore. Synthetic-checkpoint builders live in conftest.py (the `synth` fixture).
"""
from __future__ import annotations

import json
import struct

import pytest

from checkpoint_prep.mutation import ACTION_TENSORS, MutationError
from checkpoint_prep.rewrite import apply_mutation, hash_all_tensors, restore_backup


def test_apply_mutation_byte_identity_and_swap(synth):
    pre = hash_all_tensors(synth.st)
    report = apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    post = hash_all_tensors(synth.st)

    for name in ("layers.0.mlp.gate_proj.weight", "layers.0.mlp.gate_proj.weight_quantizer._scale",
                 "self_attn.q_proj.weight", "embed_tokens.weight"):
        assert post[name] == pre[name], name  # kept tensors byte-identical
    assert "lm_head.weight_quantizer._amax" not in post  # FP8 lm_head sidecars gone
    assert "lm_head.weight_quantizer._scale" not in post
    assert "lm_head.weight" in post  # restored BF16 lm_head
    for a in ACTION_TENSORS:
        assert a in post
    assert report["action_count_before"] == 0 and report["action_count_after"] == 5
    assert report["lm_head_dtype_before"] == "F8_E4M3" and report["lm_head_dtype_after"] == "BF16"


def test_added_tensors_match_source_bytes(synth):
    src_hashes = {}
    for shard in sorted((synth.source / "transformer").glob("*.safetensors")):
        src_hashes.update(hash_all_tensors(shard))
    apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    post = hash_all_tensors(synth.st)
    for name in (*ACTION_TENSORS, "lm_head.weight"):
        assert post[name] == src_hashes[name], name


def test_config_and_sidecars_updated(synth):
    apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    cfg = json.loads((synth.ckpt / "transformer" / "config.json").read_text())
    qc = json.loads((synth.ckpt / "quantization_config.json").read_text())
    qmd = json.loads((synth.ckpt / "quantizer_map_diff.json").read_text())
    assert cfg["action_gen"] is True
    assert qc["recipe"] == "fp8_blockwise_mixed"  # load-bearing, unchanged
    assert qc["quant_lmhead"] is False and "lm_head" not in qc["mixed_precision"]["quantized"]
    assert qc["mixed_precision"]["n_quantized"] == 1  # toy: 2 quantized (mlp+lm_head) -> 1 (mlp only)
    assert qmd["n_weight_quantized"] == 1 and not qmd["dropped_action_keys"]
    assert set(qmd["appended_action_keys"]) == set(ACTION_TENSORS)


def test_output_is_structurally_valid(synth):
    apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    with open(synth.st, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        header = json.loads(f.read(n))
    entries = {k: v for k, v in header.items() if k != "__metadata__"}
    offs = sorted(v["data_offsets"] for v in entries.values())
    assert offs[0][0] == 0
    for a, b in zip(offs, offs[1:]):
        assert a[1] == b[0]  # contiguous
    assert 8 + n + offs[-1][1] == synth.st.stat().st_size


def test_backup_and_restore_roundtrip(synth):
    orig_bytes = synth.st.read_bytes()
    orig_cfg = (synth.ckpt / "transformer" / "config.json").read_text()
    apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    assert synth.st.read_bytes() != orig_bytes  # mutated
    restore_backup(str(synth.ckpt))
    assert synth.st.read_bytes() == orig_bytes  # byte-for-byte restored
    assert (synth.ckpt / "transformer" / "config.json").read_text() == orig_cfg


def test_verify_failure_leaves_original_intact(synth, monkeypatch):
    orig_bytes = synth.st.read_bytes()
    import checkpoint_prep.rewrite as rw
    monkeypatch.setattr(rw, "_verify_output",
                        lambda *a, **k: (_ for _ in ()).throw(MutationError("forced")))
    with pytest.raises(MutationError):
        apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    assert synth.st.read_bytes() == orig_bytes
    assert not list((synth.ckpt / "transformer").glob("*.s5-tmp"))  # no stray temp


def test_idempotent_refuse_on_already_mutated(synth):
    apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    with pytest.raises(MutationError):
        apply_mutation(str(synth.ckpt), str(synth.source), backup=False)  # second run refuses


def test_real_verify_output_catches_corrupt_write(synth, monkeypatch):
    """Exercise the REAL _verify_output (not a stub): a corrupted write must raise before the atomic
    replace, leaving the original intact. Guards the primary byte-identity safety mechanism."""
    import checkpoint_prep.rewrite as rw

    real_write = rw._write_rewrite

    def corrupt_write(*args):
        real_write(*args)  # produce the correct temp, then flip one byte of the first (kept) tensor
        out_path = args[-1]
        with open(out_path, "r+b") as f:
            n = struct.unpack("<Q", f.read(8))[0]
            f.seek(8 + n)
            b = f.read(1)
            f.seek(8 + n)
            f.write(bytes([b[0] ^ 0xFF]))

    monkeypatch.setattr(rw, "_write_rewrite", corrupt_write)
    orig = synth.st.read_bytes()
    with pytest.raises(MutationError):
        apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    assert synth.st.read_bytes() == orig  # original NOT replaced
    assert not list((synth.ckpt / "transformer").glob("*.s5-tmp"))  # temp cleaned up
