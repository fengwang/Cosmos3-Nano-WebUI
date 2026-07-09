"""S6 self-contained copy step — replace the BF16 symlinks in a `-dist` dir with real byte-identical
copies (incl. the bundled BF16 reasoner) and record provenance, without touching the quantized
`transformer/`. Spec: docs/session_6/specs/self-contained-checkpoint-copy.md.

ACD: `plan_copy` is a Calculation (queries the source layout, no mutation); `execute_copy` is an Action
(file I/O); `verify_copy` computes its verdict as a Calculation over streamed hashes, then performs a
single provenance-write Action (its only side effect, gated by `write_provenance`). Copies are raw bytes
(never a torch round-trip, never a symlink), so byte-identity is guaranteed (INV-5/INV-11). Reuses the
S5 streaming hasher (`rewrite.hash_all_tensors`).
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from checkpoint_prep.rewrite import hash_all_tensors

_CHUNK = 64 << 20  # 64 MiB streaming chunk
_TMP_SUFFIX = ".s6-tmp"
_BF16_BASE_REF = os.environ.get("COSMOS3_BF16_BASE_DIR", "/data/models/Cosmos3-Nano/")  # operator BF16 base mount; back-ref sentinel
_TEXT_SUFFIXES = (".json", ".txt")
_PROVENANCE = "self_contained_provenance.json"

# Borrowed-file inventory (S1 §2 generation-pipeline + root configs, §4 eval-referenced assets) and the
# S4 §4 bundled BF16 reasoner file set. Every entry below is a symlink into the BF16 base today; S6
# copies it into the `-dist` dir. NOTHING here is under `<dist>/transformer/` (the quantized gen tower).
SHARED_DIRS = ("vae", "text_tokenizer", "vision_encoder", "sound_tokenizer", "scheduler")
ROOT_FILES = ("model_index.json", "config.json", "generation_config.json", "checkpoint.json",
              "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt",
              "chat_template.json", "preprocessor_config.json", "video_preprocessor_config.json")
ASSET_FILES = ("example_t2v_prompt.json", "example_t2v_output.mp4", "negative_prompt.json",
               "example_i2v_prompt.json", "example_i2v_input.jpg", "example_t2vs_prompt.json",
               "example_action_fd_agibotworld_first_frame.png",
               "example_action_fd_agibotworld_action_chunks.json",
               "example_action_fd_agibotworld_4chunk_output.mp4")
# The reasoner bundle lives in a SEPARATE dir from the quantized <dist>/transformer/ (S4 layout note).
REASONER_DIRS = ("transformer", "vision_encoder")
REASONER_CONFIGS = ("config.json", "generation_config.json", "tokenizer.json", "tokenizer_config.json",
                    "vocab.json", "merges.txt", "chat_template.json", "preprocessor_config.json",
                    "video_preprocessor_config.json")


class CopyError(RuntimeError):
    """Raised when the planned copy is unsafe (missing source file). Fail-closed: no copy is attempted."""


@dataclass(frozen=True)
class CopyItem:
    rel: str      # path relative to the -dist dir
    kind: str     # "file" | "dir"
    source: str   # absolute source path (BF16 base)
    dest: str     # absolute destination path (in the -dist dir)
    group: str    # provenance group: shared|root|assets|reasoner


@dataclass(frozen=True)
class CopyPlan:
    items: tuple
    dst_dir: str
    source_dir: str


@dataclass
class CopyReport:
    ok: bool
    problems: list
    files: int = 0
    facts: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------- plan (Calculation)

def plan_copy(dst_dir, source_dir) -> CopyPlan:
    """Build the copy plan from the fixed inventory; fail closed if a listed source file is absent.

    Never plans a path under `<dst>/transformer/` — the quantized generation tower is left untouched.
    """
    dst, src = Path(dst_dir), Path(source_dir)
    items: list = []
    missing: list = []

    def add(rel: str, kind: str, src_path: Path, group: str) -> None:
        if not src_path.exists():
            missing.append(str(src_path))
            return
        items.append(CopyItem(rel=rel, kind=kind, source=str(src_path), dest=str(dst / rel), group=group))

    for d in SHARED_DIRS:
        add(d, "dir", src / d, "shared")
    for f in ROOT_FILES:
        add(f, "file", src / f, "root")
    for a in ASSET_FILES:
        add(f"assets/{a}", "file", src / "assets" / a, "assets")
    for d in REASONER_DIRS:
        add(f"reasoner/{d}", "dir", src / d, "reasoner")
    for f in REASONER_CONFIGS:
        add(f"reasoner/{f}", "file", src / f, "reasoner")

    if missing:
        raise CopyError(f"source files absent under {src}: {missing}")
    for it in items:  # guardrail: the quantized transformer is never a copy target
        if it.rel == "transformer" or it.rel.startswith("transformer/"):
            raise CopyError(f"refusing to plan a copy over the quantized transformer: {it.rel}")
    return CopyPlan(items=tuple(items), dst_dir=str(dst), source_dir=str(src))


# ---------------------------------------------------------------------------- symlink sweep (Calculation)

def _points_into(link: Path, base: Path) -> bool:
    """True if `link` is a symlink whose target — absolute OR relative — resolves to the BF16 `base` or
    under it. Resolving (not raw-string matching) catches relative symlinks (e.g. `../Cosmos3-Nano/vae`)."""
    if not link.is_symlink():
        return False
    target = os.readlink(link)
    resolved = Path(target) if os.path.isabs(target) else link.parent / target
    resolved = resolved.resolve(strict=False)
    base_r = base.resolve(strict=False)
    return resolved == base_r or base_r in resolved.parents


def plan_symlink_sweep(dst_dir, source_dir) -> list:
    """Any TOP-LEVEL entry in the `-dist` dir still symlinked into the BF16 source (e.g. the non-serve
    model-card docs/images the fixed inventory skips) → a CopyItem that replaces it with a real copy, so
    the dir ends with ZERO symlinks into the BF16 base (airtight INV-5). Runs AFTER the fixed copy, so it
    only catches leftovers. `README.md` is swept only where it is a symlink (untouched where it is a
    real, checkpoint-specific file)."""
    dst, src = Path(dst_dir), Path(source_dir)
    items: list = []
    for entry in sorted(dst.iterdir()):
        if _points_into(entry, src):
            target = os.readlink(entry)
            # resolve a relative target against the link's parent so the copy opens an absolute source
            source = target if os.path.isabs(target) else str((entry.parent / target).resolve(strict=False))
            items.append(CopyItem(rel=entry.name, kind="dir" if entry.is_dir() else "file",
                                   source=source, dest=str(entry), group="sweep"))
    return items


# ---------------------------------------------------------------------------- execute (Actions)

def _copy_file_bytes(src_path: Path, dest_path: Path) -> None:
    """Stream raw bytes to a temp sibling then atomically move into place (overwrites a symlink)."""
    tmp = dest_path.with_name(dest_path.name + _TMP_SUFFIX)
    if tmp.is_symlink() or tmp.exists():
        tmp.unlink()  # never write THROUGH a pre-existing (possibly symlinked) temp path into the source
    with open(src_path, "rb") as fi, open(tmp, "wb") as fo:
        while True:
            chunk = fi.read(_CHUNK)
            if not chunk:
                break
            fo.write(chunk)
        fo.flush()
        os.fsync(fo.fileno())
    os.replace(tmp, dest_path)


def _ensure_real_dir(path: Path) -> None:
    """Make `path` a real directory, replacing a symlink if present (never write THROUGH a symlink)."""
    if path.is_symlink():
        path.unlink()
    path.mkdir(parents=True, exist_ok=True)


def _ensure_real_parents(dest: Path, root: Path) -> None:
    """De-symlink every directory component between `root` and `dest` (exclusive of dest)."""
    rel = dest.relative_to(root)
    cur = root
    for part in rel.parts[:-1]:
        cur = cur / part
        _ensure_real_dir(cur)


def _copy_tree(src: Path, dst: Path) -> None:
    """Recursively copy `src` into the real directory `dst`, entry by entry, as raw bytes."""
    for child in sorted(src.iterdir()):
        target = dst / child.name
        if child.is_dir():
            _ensure_real_dir(target)
            _copy_tree(child, target)
        else:
            if target.is_symlink():
                target.unlink()
            _copy_file_bytes(child, target)


def execute_copy(plan: CopyPlan) -> None:
    """Materialize every planned item as a real file/dir, atomically replacing dangling symlinks.
    Idempotent (a re-run re-copies over the real files)."""
    root = Path(plan.dst_dir)
    for it in plan.items:
        dest = Path(it.dest)
        _ensure_real_parents(dest, root)
        if it.kind == "dir":
            _ensure_real_dir(dest)
            _copy_tree(Path(it.source), dest)
        else:
            if dest.is_symlink():
                dest.unlink()
            _copy_file_bytes(Path(it.source), dest)


# ---------------------------------------------------------------------------- verify (Calculation)

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def snapshot_transformer_hashes(ckpt_dir) -> dict:
    """Per-tensor sha256 of EVERY safetensors file under `<dist>/transformer/` — the INV-11 baseline
    captured before the copy (the copy must leave these byte-identical). Handles both the diffusers
    (`diffusion_pytorch_model*.safetensors`, FP8-dist) and transformers (`model*.safetensors`, NVFP4-dist)
    namings plus shards; keys are `<filename>/<tensor>` so shard-local names never collide."""
    tdir = Path(ckpt_dir) / "transformer"
    if not tdir.is_dir():
        return {}
    out: dict = {}
    for st in sorted(tdir.glob("*.safetensors")):
        for name, digest in hash_all_tensors(st).items():
            out[f"{st.name}/{name}"] = digest
    return out


def _has_bf16_backref(path: Path) -> bool:
    if path.suffix not in _TEXT_SUFFIXES:
        return False
    try:
        return _BF16_BASE_REF in path.read_text(errors="ignore")
    except OSError:
        return False


def _verify_file(src: Path, dest: Path, rel: str, prov: list, group: str) -> list:
    problems: list = []
    if dest.is_symlink():
        return [f"still a symlink (not self-contained): {rel}"]
    if not dest.is_file():
        return [f"missing copied file: {rel}"]
    sha = _sha256(dest)
    if sha != _sha256(src):
        problems.append(f"sha256 mismatch vs source: {rel}")
    if _has_bf16_backref(dest):
        problems.append(f"BF16 back-reference ({_BF16_BASE_REF}) in copied config: {rel}")
    prov.append({"group": group, "rel": rel, "source": str(src), "sha256": sha,
                 "bytes": dest.stat().st_size})
    return problems


def _verify_tree(src: Path, dest: Path, rel: str, prov: list, group: str) -> list:
    """Every file under `src` has a real, byte-identical, back-reference-free copy under `dest`."""
    problems: list = []
    if dest.is_symlink():
        return [f"still a symlink (not self-contained): {rel}"]
    if not dest.is_dir():
        return [f"missing copied directory: {rel}"]
    for child in sorted(src.iterdir()):
        c_rel = f"{rel}/{child.name}"
        c_dest = dest / child.name
        if child.is_dir():
            problems += _verify_tree(child, c_dest, c_rel, prov, group)
        else:
            problems += _verify_file(child, c_dest, c_rel, prov, group)
    return problems


def verify_copy(plan: CopyPlan, *, transformer_pre_hashes: dict | None = None,
                write_provenance: bool = True) -> CopyReport:
    """Prove self-containment (no symlinks), byte-identity (sha256 == source), no BF16 back-references,
    and that the quantized `transformer/` is byte-unchanged (INV-11). Optionally write provenance."""
    root = Path(plan.dst_dir)
    problems: list = []
    prov: list = []

    for it in plan.items:
        if it.kind == "dir":
            problems += _verify_tree(Path(it.source), Path(it.dest), it.rel, prov, it.group)
        else:
            problems += _verify_file(Path(it.source), Path(it.dest), it.rel, prov, it.group)

    if transformer_pre_hashes is not None:
        post = snapshot_transformer_hashes(root)
        for name, h in transformer_pre_hashes.items():
            if post.get(name) != h:
                problems.append(f"quantized transformer tensor changed (INV-11 violation): {name}")

    # Airtight INV-5: no top-level entry may still be a symlink into the BF16 base (nothing borrowed).
    src_base = Path(plan.source_dir)
    for entry in sorted(root.iterdir()):
        if _points_into(entry, src_base):
            problems.append(f"top-level entry still symlinks into the BF16 base (not self-contained): {entry.name}")

    if write_provenance:
        _write_provenance(root, plan, prov)

    return CopyReport(ok=not problems, problems=problems, files=len(prov),
                      facts={"copied_files": len(prov),
                             "transformer_tensors_checked": len(transformer_pre_hashes or {})})


def _write_provenance(root: Path, plan: CopyPlan, prov: list) -> None:
    data = {
        "tool": "checkpoint_prep.copy_shared (P6-S6)",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dst_dir": str(root),
        "source_dir": plan.source_dir,
        "file_count": len(prov),
        "files": sorted(prov, key=lambda f: f["rel"]),
    }
    (root / _PROVENANCE).write_text(json.dumps(data, indent=2) + "\n")


# ---------------------------------------------------------------------------- orchestration

def make_self_contained(ckpt_dir, source_dir, *, verify: bool = True) -> CopyReport:
    """Plan → snapshot transformer → execute the fixed inventory → sweep any leftover BF16 symlinks →
    verify (+ provenance). Returns the verify report (or an ok report when verify is skipped)."""
    base = plan_copy(ckpt_dir, source_dir)
    pre = snapshot_transformer_hashes(ckpt_dir)
    execute_copy(base)
    sweep = plan_symlink_sweep(ckpt_dir, source_dir)  # after the fixed copy → only non-serve leftovers
    if sweep:
        execute_copy(CopyPlan(items=tuple(sweep), dst_dir=base.dst_dir, source_dir=base.source_dir))
    full = CopyPlan(items=(*base.items, *sweep), dst_dir=base.dst_dir, source_dir=base.source_dir)
    if verify:
        return verify_copy(full, transformer_pre_hashes=pre)
    # no-verify: still record a reconstructible provenance (source paths), sans sha256 (not computed).
    prov = [{"group": it.group, "rel": it.rel, "source": it.source, "sha256": None, "bytes": None}
            for it in full.items]
    _write_provenance(Path(full.dst_dir), full, prov)
    return CopyReport(ok=True, problems=[], files=len(full.items))
