"""Tests for the integrity probe — pure predicates + an end-to-end probe over a synthetic mutation.

Derived from docs/session_5/specs/checkpoint-integrity-probe.md.
"""
from __future__ import annotations

import json
import struct

from checkpoint_prep.integrity_probe import (
    check_action_set,
    check_inv7_structure,
    check_quantized_count,
    check_scoped_byte_identity,
    check_sidecars,
    check_source_identity,
    probe_checkpoint,
)
from checkpoint_prep.mutation import ADDED_TENSORS
from checkpoint_prep.rewrite import apply_mutation

CFG = {"action_dim": 64, "hidden_size": 4096, "num_embodiment_domains": 32, "vocab_size": 151936}


def _entry(dtype, shape):
    return {"dtype": dtype, "shape": shape, "data_offsets": [0, 1]}


def _mutated_header():
    """A correctly-mutated header: 1 mlp F8 target + BF16 lm_head + 5 BF16 action + BF16 kept."""
    h, d, n, v = CFG["hidden_size"], CFG["action_dim"], CFG["num_embodiment_domains"], CFG["vocab_size"]
    hdr = {
        "layers.0.mlp.gate_proj.weight": _entry("F8_E4M3", [12288, 4096]),
        "layers.0.mlp.gate_proj.weight_quantizer._scale": _entry("BF16", [96, 32]),
        "self_attn.q_proj.weight": _entry("BF16", [4096, 4096]),
        "embed_tokens.weight": _entry("BF16", [v, h]),
        "lm_head.weight": _entry("BF16", [v, h]),
        "action_modality_embed": _entry("BF16", [h]),
        "action_proj_in.bias.weight": _entry("BF16", [n, h]),
        "action_proj_in.fc.weight": _entry("BF16", [n, d * h]),
        "action_proj_out.bias.weight": _entry("BF16", [n, d]),
        "action_proj_out.fc.weight": _entry("BF16", [n, d * h]),
    }
    return hdr


# ---- pure predicates ----

def test_check_action_set_ok():
    assert check_action_set(_mutated_header(), CFG) == []


def test_check_action_set_missing_and_mistyped():
    hdr = _mutated_header()
    hdr["action_proj_in.fc.weight"]["dtype"] = "F8_E4M3"  # mis-typed
    del hdr["action_modality_embed"]  # missing
    problems = check_action_set(hdr, CFG)
    assert any("action_modality_embed" in p for p in problems)
    assert any("action_proj_in.fc.weight" in p and "BF16" in p for p in problems)


def test_check_inv7_ok():
    assert check_inv7_structure(_mutated_header()) == []


def test_check_inv7_rejects_quantized_lmhead():
    hdr = _mutated_header()
    hdr["lm_head.weight"] = _entry("F8_E4M3", [151936, 4096])
    hdr["lm_head.weight_quantizer._amax"] = _entry("BF16", [1187, 1, 32, 1])
    problems = check_inv7_structure(hdr)
    assert any("lm_head" in p for p in problems)


def test_check_inv7_rejects_quantized_non_mlp():
    hdr = _mutated_header()
    hdr["self_attn.q_proj.weight"] = _entry("F8_E4M3", [4096, 4096])  # forbidden quantization
    problems = check_inv7_structure(hdr)
    assert any("self_attn" in p for p in problems)


def test_check_quantized_count_consistency():
    hdr = _mutated_header()
    assert check_quantized_count(hdr, {"mixed_precision": {"n_quantized": 1}}) == []
    bad = check_quantized_count(hdr, {"mixed_precision": {"n_quantized": 216}})
    assert bad and "216" in bad[0]


def test_check_scoped_byte_identity():
    pre = {"self_attn.q_proj.weight": "aaa", "embed_tokens.weight": "bbb",
           "lm_head.weight": "fp8hash", "lm_head.weight_quantizer._amax": "x",
           "lm_head.weight_quantizer._scale": "y", "layers.0.mlp.gate_proj.weight": "ccc"}
    post = {"self_attn.q_proj.weight": "aaa", "embed_tokens.weight": "bbb",
            "lm_head.weight": "bf16hash",  # intentionally different (restored) — must be skipped
            "layers.0.mlp.gate_proj.weight": "ccc",
            "action_modality_embed": "z", "action_proj_in.bias.weight": "z",
            "action_proj_in.fc.weight": "z", "action_proj_out.bias.weight": "z",
            "action_proj_out.fc.weight": "z"}
    assert check_scoped_byte_identity(pre, post) == []
    # a changed kept tensor is caught
    post2 = dict(post, **{"self_attn.q_proj.weight": "CHANGED"})
    assert any("self_attn" in p for p in check_scoped_byte_identity(pre, post2))
    # a lingering quantizer sidecar is caught
    post3 = dict(post, **{"lm_head.weight_quantizer._amax": "x"})
    assert any("_amax" in p for p in check_scoped_byte_identity(pre, post3))


def test_check_source_identity_flags_mismatch_and_missing():
    src = {name: f"h{i}" for i, name in enumerate(ADDED_TENSORS)}
    post = dict(src)
    assert check_source_identity(post, src) == []  # all match
    # a mismatched added tensor is caught
    mism = check_source_identity(dict(post, **{ADDED_TENSORS[0]: "WRONG"}), src)
    assert any("does not match" in p for p in mism)
    # a wrong/empty --source (added tensor absent from source_hashes) is a FAILURE, not a silent pass
    missing = check_source_identity(post, {})
    assert missing and all("not found in the BF16 source" in p for p in missing)


def test_check_sidecars():
    cfg = {"action_gen": True}
    qc = {"recipe": "fp8_blockwise_mixed", "quant_lmhead": False,
          "mixed_precision": {"quantized": ["mlp.*", "mlp_moe_gen.*"]}}
    qmd = {"dropped_action_keys": []}
    assert check_sidecars(cfg, qc, qmd) == []
    assert check_sidecars({"action_gen": False}, qc, qmd)  # action_gen not enabled
    assert check_sidecars(cfg, {**qc, "recipe": "changed"}, qmd)  # recipe drift
    assert check_sidecars(cfg, {**qc, "quant_lmhead": True}, qmd)  # lm_head still quantized


# ---- end-to-end orchestrator over a real synthetic mutation ----

def test_probe_passes_on_correct_mutation(synth):
    apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    backup = synth.st.with_name(synth.st.name + ".s5-orig.bak")
    report = probe_checkpoint(str(synth.ckpt), backup_st=str(backup), source_dir=str(synth.source))
    assert report.ok, report.problems
    assert report.facts["action_count"] == 5
    assert report.facts["lm_head_dtype"] == "BF16"


def test_probe_detects_pickle_and_reports_facts(synth):
    apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    # a pre-existing modelopt_state.pt is allowed; an unexpected pickle is flagged
    (synth.ckpt / "transformer" / "rogue.pkl").write_bytes(b"\x80\x04")
    report = probe_checkpoint(str(synth.ckpt))
    assert not report.ok
    assert any("pickle" in p for p in report.problems)


def test_probe_orchestrator_fails_on_sidecar_drift(synth):
    """End-to-end: a predicate failure drives probe_checkpoint(...).ok = False (not just pickle)."""
    apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    qc_path = synth.ckpt / "quantization_config.json"
    qc = json.loads(qc_path.read_text())
    qc["quant_lmhead"] = True  # re-introduce the INV-7 deviation
    qc_path.write_text(json.dumps(qc))
    report = probe_checkpoint(str(synth.ckpt))
    assert not report.ok and any("quant_lmhead" in p for p in report.problems)


def test_probe_orchestrator_fails_on_byte_identity_break(synth):
    """End-to-end: a corrupted kept tensor drives ok = False via the scoped byte-identity check."""
    apply_mutation(str(synth.ckpt), str(synth.source), backup=True)
    backup = synth.st.with_name(synth.st.name + ".s5-orig.bak")
    with open(synth.st, "r+b") as f:  # flip the first data byte (a kept tensor at new offset 0)
        n = struct.unpack("<Q", f.read(8))[0]
        f.seek(8 + n)
        b = f.read(1)
        f.seek(8 + n)
        f.write(bytes([b[0] ^ 0xFF]))
    report = probe_checkpoint(str(synth.ckpt), backup_st=str(backup))
    assert not report.ok and any("byte-identity" in p for p in report.problems)
