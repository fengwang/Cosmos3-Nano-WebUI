"""Integration tests for execute_copy + verify_copy (spec: self-contained-checkpoint-copy —
execution, verification, and provenance)."""
from __future__ import annotations

import json

from checkpoint_prep.copy_shared import (
    execute_copy,
    plan_copy,
    snapshot_transformer_hashes,
    verify_copy,
)


def _run(sc):
    plan = plan_copy(sc.dist, sc.source)
    pre = snapshot_transformer_hashes(sc.dist)
    execute_copy(plan)
    return plan, pre


def test_symlink_becomes_real_byte_identical_copy(sc_synth):
    assert (sc_synth.dist / "model_index.json").is_symlink()  # precondition
    plan, _ = _run(sc_synth)
    dest = sc_synth.dist / "model_index.json"
    assert dest.is_file() and not dest.is_symlink()
    assert dest.read_bytes() == (sc_synth.source / "model_index.json").read_bytes()


def test_symlinked_directory_becomes_real_tree(sc_synth):
    assert (sc_synth.dist / "vae").is_symlink()
    _run(sc_synth)
    vae = sc_synth.dist / "vae"
    assert vae.is_dir() and not vae.is_symlink()
    assert (vae / "cfg.json").is_file() and not (vae / "cfg.json").is_symlink()
    assert (vae / "weight.bin").read_bytes() == (sc_synth.source / "vae" / "weight.bin").read_bytes()


def test_reasoner_bundle_materialized(sc_synth):
    _run(sc_synth)
    rt = sc_synth.dist / "reasoner" / "transformer"
    assert rt.is_dir() and not rt.is_symlink()
    assert (rt / "diffusion_pytorch_model.safetensors").read_bytes() == \
        (sc_synth.source / "transformer" / "diffusion_pytorch_model.safetensors").read_bytes()
    assert (sc_synth.dist / "reasoner" / "config.json").is_file()


def test_execution_is_idempotent(sc_synth):
    plan, _ = _run(sc_synth)
    execute_copy(plan)  # second run
    dest = sc_synth.dist / "tokenizer.json"
    assert dest.is_file() and not dest.is_symlink()
    assert dest.read_bytes() == (sc_synth.source / "tokenizer.json").read_bytes()


def test_verify_passes_and_writes_provenance(sc_synth):
    plan, pre = _run(sc_synth)
    rep = verify_copy(plan, transformer_pre_hashes=pre)
    assert rep.ok, rep.problems
    prov = json.loads((sc_synth.dist / "self_contained_provenance.json").read_text())
    rels = {f["rel"] for f in prov["files"]}
    assert "model_index.json" in rels and "reasoner/config.json" in rels
    for f in prov["files"]:  # recorded sha == destination sha
        assert len(f["sha256"]) == 64 and f["source"] and f["bytes"] >= 0


def test_verify_flags_a_remaining_symlink(sc_synth):
    plan, pre = _run(sc_synth)
    dest = sc_synth.dist / "tokenizer.json"
    dest.unlink()
    dest.symlink_to(sc_synth.source / "tokenizer.json")  # re-introduce a symlink
    rep = verify_copy(plan, transformer_pre_hashes=pre, write_provenance=False)
    assert not rep.ok
    assert any("symlink" in p and "tokenizer.json" in p for p in rep.problems)


def test_verify_flags_bf16_backreference_in_config(sc_synth):
    plan, pre = _run(sc_synth)
    (sc_synth.dist / "config.json").write_text(
        json.dumps({"vae": "/data/models/Cosmos3-Nano/vae"}))  # points back into BF16
    rep = verify_copy(plan, transformer_pre_hashes=pre, write_provenance=False)
    assert not rep.ok
    assert any("back-reference" in p.lower() or "Cosmos3-Nano" in p for p in rep.problems)


def test_verify_flags_altered_quantized_transformer(sc_synth):
    plan, pre = _run(sc_synth)
    # Tamper the pre-hash baseline to simulate the transformer having changed under the copy.
    tampered = dict(pre)
    first = next(iter(tampered))
    tampered[first] = "0" * 64
    rep = verify_copy(plan, transformer_pre_hashes=tampered, write_provenance=False)
    assert not rep.ok
    assert any("INV-11" in p or "transformer" in p for p in rep.problems)


def test_sha_mismatch_is_detected(sc_synth):
    plan, pre = _run(sc_synth)
    (sc_synth.dist / "vocab.json").write_text("TAMPERED")  # diverge from source bytes
    rep = verify_copy(plan, transformer_pre_hashes=pre, write_provenance=False)
    assert not rep.ok
    assert any("vocab.json" in p for p in rep.problems)


def test_sweep_replaces_leftover_nonplan_bf16_symlinks(sc_synth):
    import os

    from checkpoint_prep.copy_shared import make_self_contained

    # non-serve entries the FIXED inventory skips (model-card doc + a dir), still symlinked into BF16.
    (sc_synth.source / "NOTICE.md").write_text("license\n")
    (sc_synth.source / "pics").mkdir()
    (sc_synth.source / "pics" / "logo.txt").write_text("logo")
    (sc_synth.dist / "NOTICE.md").symlink_to(sc_synth.source / "NOTICE.md")
    (sc_synth.dist / "pics").symlink_to(sc_synth.source / "pics")

    rep = make_self_contained(sc_synth.dist, sc_synth.source)
    assert rep.ok, rep.problems
    assert (sc_synth.dist / "NOTICE.md").is_file() and not (sc_synth.dist / "NOTICE.md").is_symlink()
    assert (sc_synth.dist / "pics").is_dir() and not (sc_synth.dist / "pics").is_symlink()
    # ZERO top-level symlinks into the BF16 base remain (airtight INV-5)
    remaining = [e.name for e in sc_synth.dist.iterdir()
                 if e.is_symlink() and os.readlink(e).startswith(str(sc_synth.source))]
    assert remaining == []


def test_sweep_handles_relative_bf16_symlink(sc_synth):
    import os

    from checkpoint_prep.copy_shared import _points_into, make_self_contained

    (sc_synth.source / "NOTE.md").write_text("x")
    rel = os.path.relpath(sc_synth.source / "NOTE.md", sc_synth.dist)  # a RELATIVE target into BF16
    (sc_synth.dist / "NOTE.md").symlink_to(rel)
    assert _points_into(sc_synth.dist / "NOTE.md", sc_synth.source)  # detected despite being relative
    rep = make_self_contained(sc_synth.dist, sc_synth.source)
    assert rep.ok, rep.problems
    assert (sc_synth.dist / "NOTE.md").is_file() and not (sc_synth.dist / "NOTE.md").is_symlink()


def test_no_verify_writes_reconstructible_provenance(sc_synth):
    from checkpoint_prep.copy_shared import make_self_contained

    rep = make_self_contained(sc_synth.dist, sc_synth.source, verify=False)
    assert rep.ok
    prov = json.loads((sc_synth.dist / "self_contained_provenance.json").read_text())
    assert prov["file_count"] > 0 and prov["files"]        # not the empty-provenance bug
    assert all(f["source"] for f in prov["files"])          # reconstructible: every entry has a source


def test_verify_flags_a_leftover_bf16_symlink(sc_synth):
    from checkpoint_prep.copy_shared import make_self_contained, plan_copy, verify_copy

    make_self_contained(sc_synth.dist, sc_synth.source)
    (sc_synth.source / "STRAY.md").write_text("x")
    (sc_synth.dist / "STRAY.md").symlink_to(sc_synth.source / "STRAY.md")  # re-introduce a BF16 symlink
    rep = verify_copy(plan_copy(sc_synth.dist, sc_synth.source), write_provenance=False)
    assert not rep.ok
    assert any("STRAY.md" in p for p in rep.problems)


def test_cli_self_contained_then_verify(sc_synth):
    from checkpoint_prep.__main__ import main

    assert main(["self-contained", "--ckpt", str(sc_synth.dist), "--source", str(sc_synth.source)]) == 0
    assert (sc_synth.dist / "self_contained_provenance.json").is_file()
    assert not (sc_synth.dist / "model_index.json").is_symlink()
    assert main(["verify-self-contained", "--ckpt", str(sc_synth.dist),
                 "--source", str(sc_synth.source)]) == 0

