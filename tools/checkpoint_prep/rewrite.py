"""Effectful rewrite shell — Actions only (file I/O). Pure logic imported from mutation.py.

Streams tensor payloads as opaque bytes (never interprets them), so byte-identity is guaranteed and FP8
dtypes are never round-tripped through torch. The mutation is atomic (write temp → verify → move
original aside → rename temp into place) and reversible (retained `*.s5-orig.bak`).
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
from pathlib import Path

from checkpoint_prep.mutation import (
    ACTION_TENSORS,
    ADDED_TENSORS,
    MutationError,
    build_layout,
    plan_mutation,
    updated_sidecars,
)
from checkpoint_prep.safetensors_io import build_header_bytes

_CHUNK = 64 << 20  # 64 MiB streaming chunk
_BACKUP_SUFFIX = ".s5-orig.bak"
_TMP_SUFFIX = ".s5-tmp"
_TRANSFORMER_ST = "diffusion_pytorch_model.safetensors"


# ---------------------------------------------------------------------------- header/hashing Actions

def read_header_file(path: str | os.PathLike) -> tuple[dict, int]:
    with open(path, "rb") as f:
        n = struct.unpack("<Q", f.read(8))[0]
        return json.loads(f.read(n)), n


def _data_start(n: int) -> int:
    return 8 + n


def hash_tensor(path: str | os.PathLike, data_start: int, entry: dict) -> str:
    """sha256 of a tensor's raw byte slice, streamed (no full-file load)."""
    s, e = entry["data_offsets"]
    h = hashlib.sha256()
    remaining = e - s
    with open(path, "rb") as f:
        f.seek(data_start + s)
        while remaining > 0:
            chunk = f.read(min(_CHUNK, remaining))
            if not chunk:
                raise MutationError(f"unexpected EOF hashing {path} range {s}:{e}")
            h.update(chunk)
            remaining -= len(chunk)
    return h.hexdigest()


def hash_all_tensors(path: str | os.PathLike) -> dict:
    """{tensor_name: sha256} over every tensor in a safetensors file."""
    header, n = read_header_file(path)
    ds = _data_start(n)
    return {k: hash_tensor(path, ds, v) for k, v in header.items() if k != "__metadata__"}


def _elem_count(entry: dict | None) -> int:
    if not entry:
        return 0
    n = 1
    for d in entry["shape"]:
        n *= d
    return n


# ---------------------------------------------------------------------------- source resolution

def _resolve_source_tensors(source_transformer_dir: Path, names) -> dict:
    """Locate each requested tensor across the BF16 source transformer shards.

    Returns {name: (shard_path, data_start, header_entry)}. Scans shard *headers* only (cheap).
    """
    found: dict = {}
    for shard in sorted(source_transformer_dir.glob("*.safetensors")):
        header, n = read_header_file(shard)
        ds = _data_start(n)
        for name in names:
            if name in header and name not in found:
                found[name] = (str(shard), ds, header[name])
    missing = [n for n in names if n not in found]
    if missing:
        raise MutationError(f"source tensors not found under {source_transformer_dir}: {missing}")
    return found


# ---------------------------------------------------------------------------- rewrite + verify

def _copy_range(src_path: str, src_data_start: int, byte_range, out) -> None:
    s, e = byte_range
    remaining = e - s
    with open(src_path, "rb") as f:
        f.seek(src_data_start + s)
        while remaining > 0:
            chunk = f.read(min(_CHUNK, remaining))
            if not chunk:
                raise MutationError(f"unexpected EOF copying {src_path} range {s}:{e}")
            out.write(chunk)
            remaining -= len(chunk)


def _write_rewrite(fp8_path, fp8_ds, fp8_header, plan, layout, srcmap, out_path) -> None:
    """Write header + contiguous data block: kept tensors verbatim from fp8, added from BF16 source."""
    keep = set(plan.keep)
    with open(out_path, "wb") as out:
        out.write(build_header_bytes(layout.entries))
        for name in layout.order:
            if name in keep:
                _copy_range(str(fp8_path), fp8_ds, fp8_header[name]["data_offsets"], out)
            else:  # added (5 action + BF16 lm_head)
                shard_path, ds, entry = srcmap[name]
                _copy_range(shard_path, ds, entry["data_offsets"], out)


def _verify_output(out_path, plan, pre_hashes: dict, src_hashes: dict) -> None:
    """Raise MutationError unless every kept tensor is byte-identical to pre, every added tensor matches
    the source, and the FP8 lm_head quantizer sidecars are gone."""
    header, n = read_header_file(out_path)
    ds = _data_start(n)
    present = {k for k in header if k != "__metadata__"}
    for name in plan.keep:
        if name not in present:
            raise MutationError(f"verify: kept tensor missing from output: {name}")
        if hash_tensor(out_path, ds, header[name]) != pre_hashes[name]:
            raise MutationError(f"verify: kept tensor not byte-identical: {name}")
    for name in plan.add:
        if name not in present:
            raise MutationError(f"verify: added tensor missing from output: {name}")
        if hash_tensor(out_path, ds, header[name]) != src_hashes[name]:
            raise MutationError(f"verify: added tensor does not match BF16 source: {name}")
    for name in (n for n in plan.drop if n not in ADDED_TENSORS):  # the 2 quantizer sidecars
        if name in present:
            raise MutationError(f"verify: dropped FP8 lm_head sidecar still present: {name}")


# ---------------------------------------------------------------------------- backup / restore

def _backup_move(path: Path) -> Path:
    bak = path.with_name(path.name + _BACKUP_SUFFIX)
    os.replace(path, bak)  # atomic move aside (same filesystem)
    return bak


def restore_backup(ckpt_dir: str | os.PathLike) -> list:
    """Restore every `*.s5-orig.bak` under ckpt_dir to its original name. Returns restored paths."""
    root = Path(ckpt_dir)
    restored = []
    for bak in sorted(root.rglob("*" + _BACKUP_SUFFIX)):
        target = bak.with_name(bak.name[: -len(_BACKUP_SUFFIX)])
        os.replace(bak, target)
        restored.append(str(target))
    if not restored:
        raise MutationError(f"no {_BACKUP_SUFFIX} backups found under {ckpt_dir}")
    return restored


# ---------------------------------------------------------------------------- orchestration

def apply_mutation(ckpt_dir: str | os.PathLike, source_dir: str | os.PathLike,
                   *, backup: bool = True, verify: bool = True) -> dict:
    """Append the 5 BF16 action tensors + restore the BF16 lm_head into the FP8-dist transformer,
    atomically and reversibly. Returns a provenance report. Raises MutationError on any unsafe step."""
    ck, src = Path(ckpt_dir), Path(source_dir)
    tdir = ck / "transformer"
    st = tdir / _TRANSFORMER_ST
    cfg_path = tdir / "config.json"
    qc_path = ck / "quantization_config.json"
    qmd_path = ck / "quantizer_map_diff.json"

    cfg = json.loads(cfg_path.read_text())
    fp8_header, fp8_n = read_header_file(st)
    fp8_ds = _data_start(fp8_n)

    srcmap = _resolve_source_tensors(src / "transformer", ADDED_TENSORS)
    bf16_src = {name: entry for name, (_p, _ds, entry) in srcmap.items()}

    plan = plan_mutation(fp8_header, bf16_src, cfg)  # raises if unsafe / already mutated (fail-closed)
    layout = build_layout(plan, fp8_header, bf16_src)

    pre_hashes = {name: hash_tensor(st, fp8_ds, fp8_header[name]) for name in plan.keep}
    src_hashes = {name: hash_tensor(p, ds, entry) for name, (p, ds, entry) in srcmap.items()}
    dropped_scale_elements = (
        _elem_count(fp8_header.get("lm_head.weight_quantizer._amax"))
        + _elem_count(fp8_header.get("lm_head.weight_quantizer._scale"))
    )

    tmp = st.with_name(st.name + _TMP_SUFFIX)
    try:
        _write_rewrite(st, fp8_ds, fp8_header, plan, layout, srcmap, tmp)
        if verify:
            _verify_output(tmp, plan, pre_hashes, src_hashes)
    except BaseException:
        if tmp.exists():
            tmp.unlink()
        raise

    # commit: move original aside (backup) then rename temp into place
    if backup:
        _backup_move(st)
    os.replace(tmp, st)

    # config + sidecars (tiny; backup-move then write new)
    if backup:
        _backup_move(cfg_path)
        _backup_move(qc_path)
        _backup_move(qmd_path)
    cfg["action_gen"] = True
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")
    new_qc, new_qmd = updated_sidecars(
        json.loads((qc_path.with_name(qc_path.name + _BACKUP_SUFFIX)).read_text()) if backup
        else json.loads(qc_path.read_text()),
        json.loads((qmd_path.with_name(qmd_path.name + _BACKUP_SUFFIX)).read_text()) if backup
        else json.loads(qmd_path.read_text()),
        dropped_scale_elements=dropped_scale_elements,
    )
    qc_path.write_text(json.dumps(new_qc, indent=2) + "\n")
    qmd_path.write_text(json.dumps(new_qmd, indent=2) + "\n")

    return {
        "ckpt_dir": str(ck),
        "source_dir": str(src),
        "action_count_before": sum(1 for a in ACTION_TENSORS if a in fp8_header),
        "action_count_after": sum(1 for a in ACTION_TENSORS if a in read_header_file(st)[0]),
        "lm_head_dtype_before": fp8_header["lm_head.weight"]["dtype"],
        "lm_head_dtype_after": read_header_file(st)[0]["lm_head.weight"]["dtype"],
        "kept_tensor_count": len(plan.keep),
        "added_tensors": list(plan.add),
        "dropped_tensors": list(plan.drop),
        "dropped_scale_elements": dropped_scale_elements,
        "backup": backup,
        "verified": verify,
    }
