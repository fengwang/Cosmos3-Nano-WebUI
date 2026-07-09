"""Integrity probe — deterministic, fail-fast verification that the mutated FP8 checkpoint is safe to
serve (NFR-6, INV-11 scoped). Pure predicates over headers/sidecars/hashes + a thin Action orchestrator
+ a CLI. Spec: docs/session_5/specs/checkpoint-integrity-probe.md.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from checkpoint_prep.mutation import ACTION_TENSORS, ADDED_TENSORS, DROPPED_LMHEAD, expected_shapes
from checkpoint_prep.rewrite import _TRANSFORMER_ST, hash_all_tensors, hash_tensor, read_header_file

_BF16 = "BF16"
_FP8 = "F8_E4M3"
# quantized MLP targets: layers.<n>.mlp.* and layers.<n>.mlp_moe_gen.*
_MLP_TARGET = re.compile(r"(^|\.)layers\.\d+\.(mlp|mlp_moe_gen)\.")
_QUANT_SIDECAR = ("weight_quantizer._amax", "weight_quantizer._scale", "weight_packed",
                  "weight_block_scale", "weight_global_scale")
_ALLOWED_PICKLES = frozenset({"modelopt_state.pt"})  # pre-existing, never read by the serving adapter


@dataclass
class ProbeReport:
    ok: bool
    problems: list
    facts: dict = field(default_factory=dict)


def _is_quant(name: str, meta: dict) -> bool:
    return meta.get("dtype") == _FP8 or any(name.endswith(s) for s in _QUANT_SIDECAR)


# ---------------------------------------------------------------------------- pure predicates

def check_action_set(header: dict, cfg: dict) -> list:
    """The 5 action tensors are present, BF16, and shape-match the transformer config."""
    problems, exp = [], expected_shapes(cfg)
    for a in ACTION_TENSORS:
        if a not in header:
            problems.append(f"action tensor missing: {a}")
            continue
        if header[a].get("dtype") != _BF16:
            problems.append(f"action tensor {a} dtype {header[a].get('dtype')} != BF16")
        if list(header[a].get("shape", [])) != exp[a]:
            problems.append(f"action tensor {a} shape {header[a].get('shape')} != {exp[a]}")
    return problems


def check_inv7_structure(header: dict) -> list:
    """lm_head + embed_tokens are BF16, and every quantized tensor is an mlp/mlp_moe_gen target."""
    problems = []
    lm = header.get("lm_head.weight")
    if lm is None or lm.get("dtype") != _BF16:
        problems.append(f"lm_head.weight dtype {lm.get('dtype') if lm else None} != BF16 (INV-7)")
    if header.get("embed_tokens.weight", {}).get("dtype") != _BF16:
        problems.append("embed_tokens.weight not BF16 (INV-7)")
    for name, meta in header.items():
        if name == "__metadata__":
            continue
        if _is_quant(name, meta) and not _MLP_TARGET.search(name):
            problems.append(f"quantized tensor outside mlp/mlp_moe_gen (INV-7 violation): {name}")
    return problems


def check_quantized_count(header: dict, quantization_config: dict) -> list:
    """The number of F8 weight tensors equals the sidecar's declared n_quantized."""
    n = sum(1 for name, meta in header.items()
            if name != "__metadata__" and name.endswith(".weight") and meta.get("dtype") == _FP8)
    declared = quantization_config.get("mixed_precision", {}).get("n_quantized")
    if declared is not None and n != declared:
        return [f"F8 weight count {n} != quantization_config n_quantized {declared}"]
    return []


def check_scoped_byte_identity(pre_hashes: dict, post_hashes: dict) -> list:
    """Every pre-existing tensor except the intentionally-replaced lm_head set is byte-identical; the
    FP8 lm_head quantizer sidecars are gone; the added tensors are present."""
    problems = []
    for name, h in pre_hashes.items():
        if name in DROPPED_LMHEAD:  # lm_head.weight (replaced) + its 2 quantizer sidecars (removed)
            continue
        if name not in post_hashes:
            problems.append(f"pre-existing tensor missing after mutation: {name}")
        elif post_hashes[name] != h:
            problems.append(f"pre-existing tensor changed (byte-identity broken): {name}")
    for name in DROPPED_LMHEAD:
        if name.endswith("._amax") or name.endswith("._scale"):
            if name in post_hashes:
                problems.append(f"FP8 lm_head quantizer sidecar still present: {name}")
    for name in ADDED_TENSORS:
        if name not in post_hashes:
            problems.append(f"expected added tensor missing: {name}")
    return problems


def check_sidecars(cfg: dict, quantization_config: dict, quantizer_map_diff: dict) -> list:
    """action_gen enabled; recipe preserved; lm_head no longer quantized; action keys resolved."""
    problems = []
    if cfg.get("action_gen") is not True:
        problems.append("transformer config action_gen != true")
    if quantization_config.get("recipe") != "fp8_blockwise_mixed":
        problems.append(f"quantization_config recipe changed: {quantization_config.get('recipe')!r}")
    if quantization_config.get("quant_lmhead") is not False:
        problems.append("quant_lmhead != false")
    if "lm_head" in quantization_config.get("mixed_precision", {}).get("quantized", []):
        problems.append("lm_head still listed in mixed_precision.quantized")
    if quantizer_map_diff.get("dropped_action_keys"):
        problems.append(f"dropped_action_keys not resolved: {quantizer_map_diff.get('dropped_action_keys')}")
    return problems


def check_source_identity(post_hashes: dict, source_hashes: dict) -> list:
    """Added tensors are byte-identical to the BF16 source (defends R-11 / wrong-source).

    A missing source tensor is a FAILURE (not a silent pass): it means the given source dir does not
    actually carry the tensor, so source-identity was never verified (e.g. a wrong --source dir).
    """
    problems = []
    for name in ADDED_TENSORS:
        if name not in source_hashes:
            problems.append(f"added tensor {name} not found in the BF16 source (wrong --source dir?)")
        elif post_hashes.get(name) != source_hashes[name]:
            problems.append(f"added tensor {name} does not match BF16 source bytes")
    return problems


def check_pickle_free(transformer_dir: Path) -> list:
    """No serving pickle other than the pre-existing, unused modelopt_state.pt."""
    pickles = [p.name for p in transformer_dir.iterdir()
               if p.is_file() and p.suffix in (".pt", ".pkl", ".bin")]
    unexpected = sorted(p for p in pickles if p not in _ALLOWED_PICKLES)
    return [f"unexpected serving pickle(s) present: {unexpected}"] if unexpected else []


# ---------------------------------------------------------------------------- Action orchestrator

def _source_hashes(source_transformer_dir: Path, names) -> dict:
    # Header-scan + hash only the requested slices (mirrors rewrite._resolve_source_tensors); hashing
    # every tensor in every shard would read ~30 GB to obtain ~1.3 GB of needed hashes.
    out: dict = {}
    for shard in sorted(source_transformer_dir.glob("*.safetensors")):
        header, n = read_header_file(shard)
        ds = 8 + n
        for name in names:
            if name in header and name not in out:
                out[name] = hash_tensor(shard, ds, header[name])
    return out


def probe_checkpoint(ckpt_dir, *, backup_st: str | None = None, source_dir: str | None = None) -> ProbeReport:
    """Run all applicable checks over a mutated checkpoint directory. Byte-identity requires the
    pre-mutation backup; source-identity requires the BF16 source dir."""
    ck = Path(ckpt_dir)
    tdir = ck / "transformer"
    st = tdir / _TRANSFORMER_ST
    header, _ = read_header_file(st)
    cfg = json.loads((tdir / "config.json").read_text())
    qc = json.loads((ck / "quantization_config.json").read_text())
    qmd = json.loads((ck / "quantizer_map_diff.json").read_text())

    problems: list = []
    problems += check_action_set(header, cfg)
    problems += check_inv7_structure(header)
    problems += check_quantized_count(header, qc)
    problems += check_sidecars(cfg, qc, qmd)
    problems += check_pickle_free(tdir)

    if backup_st or source_dir:
        post_hashes = hash_all_tensors(st)
        if backup_st:
            problems += check_scoped_byte_identity(hash_all_tensors(backup_st), post_hashes)
        if source_dir:
            problems += check_source_identity(
                post_hashes, _source_hashes(Path(source_dir) / "transformer", ADDED_TENSORS))

    facts = {
        "action_count": sum(1 for a in ACTION_TENSORS if a in header),
        "lm_head_dtype": header.get("lm_head.weight", {}).get("dtype"),
        "f8_weight_count": sum(1 for n, m in header.items()
                               if n != "__metadata__" and n.endswith(".weight") and m.get("dtype") == _FP8),
        "n_quantized": qc.get("mixed_precision", {}).get("n_quantized"),
        "recipe": qc.get("recipe"),
        "action_gen": cfg.get("action_gen"),
        "byte_identity_checked": bool(backup_st),
        "source_identity_checked": bool(source_dir),
    }
    return ProbeReport(ok=not problems, problems=problems, facts=facts)


def snapshot_facts(ckpt_dir) -> dict:
    """Pre-mutation provenance: facts + per-tensor sha256 (for the byte-identity record)."""
    ck = Path(ckpt_dir)
    tdir = ck / "transformer"
    st = tdir / _TRANSFORMER_ST
    header, _ = read_header_file(st)
    cfg = json.loads((tdir / "config.json").read_text())
    return {
        "ckpt_dir": str(ck),
        "tensor_count": sum(1 for k in header if k != "__metadata__"),
        "action_count": sum(1 for a in ACTION_TENSORS if a in header),
        "action_gen": cfg.get("action_gen"),
        "lm_head_dtype": header.get("lm_head.weight", {}).get("dtype"),
        "hashes": hash_all_tensors(st),
    }


def _main(argv) -> int:
    import argparse

    p = argparse.ArgumentParser(description="Cosmos3-Nano FP8 checkpoint integrity probe (P6-S5)")
    p.add_argument("ckpt_dir")
    p.add_argument("--backup", default=None, help="pre-mutation transformer safetensors backup (byte-identity)")
    p.add_argument("--source", default=None, help="BF16 source dir (added-tensor identity)")
    p.add_argument("--snapshot", action="store_true", help="dump pre-mutation facts+hashes JSON; exit 0")
    a = p.parse_args(argv)
    if a.snapshot:
        print(json.dumps(snapshot_facts(a.ckpt_dir), indent=2))
        return 0
    report = probe_checkpoint(a.ckpt_dir, backup_st=a.backup, source_dir=a.source)
    print(json.dumps({"ok": report.ok, "problems": report.problems, "facts": report.facts}, indent=2))
    return 0 if report.ok else 1


if __name__ == "__main__":
    import sys

    raise SystemExit(_main(sys.argv[1:]))
