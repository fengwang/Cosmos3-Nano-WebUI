"""Unit tests for the fail-closed reasoner BF16 source guard (P6-S4).

Derived from `docs/session_4/specs/reasoner-source-guard.md`. Torch-free, no GPU: exercises the pure
verdict Calculation, the header-reading Action, the CLI exit codes, and the `build_reasoner` fail-fast.
The keep/drop rule mirrors `submodules/vllm/.../models/cosmos3.py` `WeightsMapper`.
"""
from __future__ import annotations

import json
import struct

import pytest

from engines.vllm.reasoner_preflight import (
    ReasonerSourceError,
    ReasonerSourceErrorCode as C,
    assert_reasoner_source,
    read_transformer_headers,
    reasoner_source_verdict,
)


def _hdr(tensors: dict) -> dict:
    """A parsed-safetensors-header shape: {name: {dtype, shape, data_offsets}}."""
    return {n: {"dtype": dt, "shape": [1], "data_offsets": [0, 0]} for n, dt in tensors.items()}


# ---- pure verdict Calculation ----

def test_bf16_kept_is_servable():
    assert reasoner_source_verdict(_hdr({
        "layers.0.mlp.gate_proj.weight": "BF16",
        "layers.0.self_attn.q_proj.weight": "BF16",
        "lm_head.weight": "BF16",
        "embed_tokens.weight": "BF16",
        "blocks.0.attn.qkv.weight": "BF16",  # visual tower, kept
        "norm.weight": "BF16",
    })) is None


def test_fp8_kept_mlp_rejected():
    r = reasoner_source_verdict(_hdr({
        "layers.0.mlp.gate_proj.weight": "F8_E4M3", "lm_head.weight": "BF16"}))
    assert r is not None and r.code is C.QUANTIZED_WEIGHT
    assert r.tensor == "layers.0.mlp.gate_proj.weight" and r.dtype == "F8_E4M3"


def test_fp8_lm_head_rejected():
    # FP8-dist quantizes lm_head to F8_E4M3 (R-19) — a reasoner-kept tensor → reject.
    r = reasoner_source_verdict(_hdr({
        "layers.0.mlp.gate_proj.weight": "BF16", "lm_head.weight": "F8_E4M3"}))
    assert r is not None and r.code is C.QUANTIZED_WEIGHT and r.tensor == "lm_head.weight"


def test_nvfp4_packed_kept_rejected():
    # NVFP4 packs the kept FFN as `*.weight_packed` (U8) + scale sidecars; the sidecar suffix check
    # fires first (before the dtype check), so the code is precisely QUANT_SIDECAR.
    r = reasoner_source_verdict(_hdr({
        "layers.0.mlp.gate_proj.weight_packed": "U8",
        "layers.0.mlp.gate_proj.weight_block_scale": "F8_E4M3",
        "lm_head.weight": "BF16"}))
    assert r is not None and r.code is C.QUANT_SIDECAR and r.tensor == "layers.0.mlp.gate_proj.weight_packed"


def test_fp8_quantizer_sidecar_on_kept_rejected():
    r = reasoner_source_verdict(_hdr({
        "layers.0.mlp.gate_proj.weight": "BF16",  # dtype fine, but the sidecar betrays quantization
        "layers.0.mlp.gate_proj.weight_quantizer._amax": "BF16",
        "lm_head.weight": "BF16"}))
    assert r is not None and r.code is C.QUANT_SIDECAR


def test_dropped_gen_tower_quant_is_ignored():
    # only reasoner-DROPPED generation-tower tensors are quantized → servable (guard must not over-reject)
    assert reasoner_source_verdict(_hdr({
        "layers.0.mlp_moe_gen.gate_proj.weight": "F8_E4M3",
        "layers.0.self_attn.add_q_proj.weight": "F8_E4M3",
        "proj_in.weight": "F8_E4M3",
        "time_embedder.linear_1.weight": "F8_E4M3",
        "layers.0.mlp.gate_proj.weight": "BF16",  # the kept understanding FFN is BF16
        "lm_head.weight": "BF16",
    })) is None


def test_int_buffer_kept_not_falsely_rejected():
    # a legitimate non-float buffer among kept tensors must not be mistaken for a quantized weight
    assert reasoner_source_verdict(_hdr({
        "layers.0.mlp.gate_proj.weight": "BF16",
        "lm_head.weight": "BF16",
        "layers.0.self_attn.rotary_emb.inv_freq": "F32",
    })) is None


def test_empty_understanding_tower_rejected():
    r = reasoner_source_verdict(_hdr({
        "proj_in.weight": "BF16", "time_embedder.linear_1.weight": "BF16"}))
    assert r is not None and r.code is C.EMPTY_UNDERSTANDING_TOWER


# ---- header-reading Action + CLI ----

def _write_st(path, tensors: dict) -> None:
    blob = json.dumps(_hdr(tensors)).encode()
    path.write_bytes(struct.pack("<Q", len(blob)) + blob)


def test_read_headers_and_assert_ok(tmp_path):
    (tmp_path / "transformer").mkdir()
    _write_st(tmp_path / "transformer" / "model.safetensors",
              {"layers.0.mlp.gate_proj.weight": "BF16", "lm_head.weight": "BF16"})
    hdr = read_transformer_headers(str(tmp_path))
    assert "layers.0.mlp.gate_proj.weight" in hdr
    assert_reasoner_source(str(tmp_path))  # no raise


def test_multi_shard_headers_merged(tmp_path):
    (tmp_path / "transformer").mkdir()
    _write_st(tmp_path / "transformer" / "model-00001-of-00002.safetensors", {"layers.0.mlp.gate_proj.weight": "BF16"})
    _write_st(tmp_path / "transformer" / "model-00002-of-00002.safetensors", {"lm_head.weight": "BF16"})
    hdr = read_transformer_headers(str(tmp_path))
    assert {"layers.0.mlp.gate_proj.weight", "lm_head.weight"} <= set(hdr)


def test_no_transformer_dir_rejected(tmp_path):
    with pytest.raises(ReasonerSourceError) as e:
        read_transformer_headers(str(tmp_path))
    assert e.value.rejection.code is C.NO_TRANSFORMER_WEIGHTS


def test_malformed_header_length_rejected(tmp_path):
    # a corrupt/hostile file declaring a 1 TiB header must fail closed, not attempt a huge allocation
    (tmp_path / "transformer").mkdir()
    (tmp_path / "transformer" / "model.safetensors").write_bytes(struct.pack("<Q", 1 << 40))
    with pytest.raises(ReasonerSourceError) as e:
        read_transformer_headers(str(tmp_path))
    assert e.value.rejection.code is C.MALFORMED_HEADER


def test_assert_raises_on_quantized_dir(tmp_path):
    (tmp_path / "transformer").mkdir()
    _write_st(tmp_path / "transformer" / "model.safetensors", {"layers.0.mlp.gate_proj.weight": "F8_E4M3"})
    with pytest.raises(ReasonerSourceError):
        assert_reasoner_source(str(tmp_path))


def test_cli_exit_codes(tmp_path):
    from engines.vllm.reasoner_preflight import _main
    (tmp_path / "ok" / "transformer").mkdir(parents=True)
    _write_st(tmp_path / "ok" / "transformer" / "model.safetensors", {"layers.0.mlp.gate_proj.weight": "BF16", "lm_head.weight": "BF16"})
    (tmp_path / "bad" / "transformer").mkdir(parents=True)
    _write_st(tmp_path / "bad" / "transformer" / "model.safetensors", {"layers.0.mlp.gate_proj.weight": "F8_E4M3"})
    assert _main([str(tmp_path / "ok")]) == 0
    assert _main([str(tmp_path / "bad")]) == 1
    assert _main([]) == 2  # usage


# ---- build_reasoner fail-fast (guard runs before the vllm import; host has no vllm) ----

def test_build_reasoner_runs_guard_before_vllm_import(tmp_path):
    (tmp_path / "transformer").mkdir()
    _write_st(tmp_path / "transformer" / "model.safetensors", {"layers.0.mlp.gate_proj.weight": "F8_E4M3"})
    from engines.vllm.loader import ReasonerConfig, build_reasoner
    with pytest.raises(ReasonerSourceError):  # NOT ImportError → proves the guard runs first
        build_reasoner(ReasonerConfig(model_dir=str(tmp_path)))


def test_build_reasoner_passes_guard_for_bf16_then_reaches_vllm(tmp_path):
    """A valid BF16 dir passes the guard; construction then proceeds to `from vllm import LLM`.

    On the torch-free host loop vllm is absent, so reaching the import raises ImportError — which
    (being NOT a ReasonerSourceError) proves the guard admitted the source and control moved on.
    """
    import importlib.util
    if importlib.util.find_spec("vllm") is not None:
        pytest.skip("vllm present: this host-loop test asserts the guard admits bf16 then the import is reached")
    (tmp_path / "transformer").mkdir()
    _write_st(tmp_path / "transformer" / "model.safetensors",
              {"layers.0.mlp.gate_proj.weight": "BF16", "lm_head.weight": "BF16"})
    from engines.vllm.loader import ReasonerConfig, build_reasoner
    with pytest.raises(ImportError):  # got PAST the guard (no ReasonerSourceError) → hit the vllm import
        build_reasoner(ReasonerConfig(model_dir=str(tmp_path)))
