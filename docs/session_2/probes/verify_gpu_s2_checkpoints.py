#!/usr/bin/env python3
"""Torch-free HF checkpoint LFS/index verification probe (GPU-S2).

Impure shell (network + filesystem + file write) around a pure core
(classify-lfs-placement / has-stale-index / looks-like-orphan-pointer /
derive-verdict / build-bundle / render). Imports neither ``torch`` nor
``diffusers``. Complements
``docs/archive/phase-1/session_4/probes/verify_hf_checkpoints.py`` (which
checks loadability/drift) with the specific packaging checks GPU-S2 owns:
no stale top-level weight index, correct LFS-vs-regular-git placement by
size/type, and no orphaned LFS-pointer content in a file that should be
real.

Evidence sources:
- HF network (authoritative for "what a user downloads"): ``HfApi.list_repo_files``
  and ``HfApi.get_paths_info`` for the manifest (size + `.lfs` attribute),
  ``hf_hub_download`` for a handful of KB-sized small-file byte checks (never
  a large weight file).

Usage:
  python3 docs/session_2/probes/verify_gpu_s2_checkpoints.py            # full probe
  python3 docs/session_2/probes/verify_gpu_s2_checkpoints.py --check    # pure-core spec assertions

Cost note: only small (non-large-pattern) files are ever downloaded, to
confirm their content isn't orphaned LFS-pointer text. No `*.safetensors`/
`*.pt`/media file's bytes are ever requested.
"""
from __future__ import annotations

import argparse
import enum
import fnmatch
import json
import os
import pathlib
import sys

FP8_REPO = "wfen/Cosmos3-Nano-FP8-Blockwise"
NVFP4_REPO = "wfen/Cosmos3-Nano-NVFP4-Blockwise"
FP8_REVISION = "9bf5d6ae164688487bdb71947ccc6ebe70d12900"
NVFP4_REVISION = "5514c42b9759739f545e0d0dee453db8d8525fbc"
STALE_INDEX_NAME = "model.safetensors.index.json"
LFS_POINTER_SIGNATURE = b"version https://git-lfs.github.com/spec/v1"
SIZE_THRESHOLD_BYTES = 10 * 1024 * 1024  # Owner Decision 4 (PRD): >10 MB -> LFS
# Non-plain-text extensions that use LFS regardless of size (Owner Decision 4).
BINARY_PATTERNS = ("*.safetensors", "*.pt", "*.pth", "*.ckpt", "*.mp4", "*.webm",
                    "*.png", "*.jpg", "*.jpeg", "*.mp3")
# Known, owner-accepted exceptions: dev-scratch files (D3) left as orphaned
# LFS-pointer content on purpose (Owner Decision 3) — not a probe failure.
KNOWN_DEV_SCRATCH_ORPHANS = {
    FP8_REPO: {"_s2_postfix.md", "_s2_rerun.md", "_s2_verify.md"},
    NVFP4_REPO: {"transformer/producer_provenance.json"},
}


# --- Data (enums) ------------------------------------------------------

class Verdict(enum.Enum):
    OK = "ok"
    STALE_INDEX_PRESENT = "stale_index_present"
    SHOULD_NOT_BE_LFS = "small_plain_text_incorrectly_lfs_backed"
    ORPHANED_POINTER = "orphaned_lfs_pointer_content"
    KNOWN_DEV_SCRATCH_ORPHAN = "known_dev_scratch_orphan_left_as_is"


# --- Pure calculations --------------------------------------------------

def is_large_or_binary(path: str, size: int | None) -> bool:
    """Pure: does this path legitimately stay LFS under Owner Decision 4?"""
    if size is not None and size > SIZE_THRESHOLD_BYTES:
        return True
    return any(fnmatch.fnmatch(path, pat) for pat in BINARY_PATTERNS)


def has_stale_index(files: list[str]) -> bool:
    """Pure: is the stale top-level weight index still present?"""
    return STALE_INDEX_NAME in files


def looks_like_lfs_pointer(content_prefix: bytes) -> bool:
    """Pure: does this byte prefix look like an unresolved LFS pointer?"""
    return content_prefix.startswith(LFS_POINTER_SIGNATURE)


def classify_lfs_placement(repo_id: str, path: str, size: int | None, is_lfs: bool) -> Verdict:
    """Pure: is this manifest entry's LFS-vs-regular placement correct?

    A known dev-scratch orphan (Owner Decision 3) is left LFS-pointer-shaped
    on purpose — it fails the general rule by design, not by regression.
    """
    if path in KNOWN_DEV_SCRATCH_ORPHANS.get(repo_id, ()):
        return Verdict.KNOWN_DEV_SCRATCH_ORPHAN
    expect_lfs = is_large_or_binary(path, size)
    if is_lfs and not expect_lfs:
        return Verdict.SHOULD_NOT_BE_LFS
    return Verdict.OK


def classify_content(repo_id: str, path: str, content_prefix: bytes | None) -> Verdict:
    """Pure: does this file's actual content still look like an orphaned pointer?"""
    if content_prefix is None:
        return Verdict.OK  # not probed (e.g. a large file we deliberately never fetch)
    if not looks_like_lfs_pointer(content_prefix):
        return Verdict.OK
    if path in KNOWN_DEV_SCRATCH_ORPHANS.get(repo_id, ()):
        return Verdict.KNOWN_DEV_SCRATCH_ORPHAN
    return Verdict.ORPHANED_POINTER


def derive_findings(repo_id: str, files: list[str], manifest: dict[str, dict],
                     content_prefixes: dict[str, bytes]) -> dict:
    """Pure: assemble this repo's full verdict set from gathered evidence."""
    findings = {
        "stale_index_present": has_stale_index(files),
        "lfs_placement": {},
        "content": {},
    }
    for path in files:
        meta = manifest.get(path, {})
        v = classify_lfs_placement(repo_id, path, meta.get("size"), meta.get("is_lfs", False))
        if v is not Verdict.OK:
            findings["lfs_placement"][path] = v.value
    for path, prefix in content_prefixes.items():
        v = classify_content(repo_id, path, prefix)
        if v is not Verdict.OK:
            findings["content"][path] = v.value
    return findings


def probe_passed(findings: dict) -> bool:
    """Pure: a repo passes iff no stale index, and every LFS-placement /
    content finding is either OK or the known, owner-approved dev-scratch
    exception — never an unexpected `SHOULD_NOT_BE_LFS` or `ORPHANED_POINTER`."""
    if findings["stale_index_present"]:
        return False
    allowed = {Verdict.KNOWN_DEV_SCRATCH_ORPHAN.value}
    bad_placement = {p: v for p, v in findings["lfs_placement"].items() if v not in allowed}
    bad_content = {p: v for p, v in findings["content"].items() if v not in allowed}
    return not bad_placement and not bad_content


# --- Pure-core self test (spec-derived assertions) ----------------------

def run_self_check() -> int:
    """Pure spec-derived assertions; no network or filesystem. Returns process code."""
    assert is_large_or_binary("transformer/model.safetensors", 14_000_000_000) is True
    assert is_large_or_binary("text_tokenizer/tokenizer.json", 11_422_654) is True  # oversized text
    assert is_large_or_binary("config.json", 8166) is False
    assert is_large_or_binary("BIAS.md", 4720) is False

    assert has_stale_index(["config.json", "model.safetensors.index.json"]) is True
    assert has_stale_index(["config.json", "transformer/model.safetensors"]) is False

    assert looks_like_lfs_pointer(b"version https://git-lfs.github.com/spec/v1\noid ...") is True
    assert looks_like_lfs_pointer(b'{\n  "allow_patterns_overrides": []\n}') is False

    assert classify_lfs_placement(FP8_REPO, "config.json", 8166, True) is Verdict.SHOULD_NOT_BE_LFS
    assert classify_lfs_placement(FP8_REPO, "config.json", 8166, False) is Verdict.OK
    assert classify_lfs_placement(FP8_REPO, "transformer/model.safetensors", 14_000_000_000, True) is Verdict.OK
    assert classify_lfs_placement(FP8_REPO, "_s2_postfix.md", 235, True) is Verdict.KNOWN_DEV_SCRATCH_ORPHAN
    assert classify_lfs_placement(NVFP4_REPO, "transformer/producer_provenance.json", 396, True) is Verdict.KNOWN_DEV_SCRATCH_ORPHAN

    pointer_bytes = b"version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 4720\n"
    assert classify_content(FP8_REPO, "config.json", b'{\n  "a": 1') is Verdict.OK
    assert classify_content(FP8_REPO, "config.json", pointer_bytes) is Verdict.ORPHANED_POINTER
    assert classify_content(FP8_REPO, "_s2_postfix.md", pointer_bytes) is Verdict.KNOWN_DEV_SCRATCH_ORPHAN
    assert classify_content(NVFP4_REPO, "transformer/producer_provenance.json",
                             pointer_bytes) is Verdict.KNOWN_DEV_SCRATCH_ORPHAN
    assert classify_content(FP8_REPO, "config.json", None) is Verdict.OK  # not probed

    ok_findings = {"stale_index_present": False, "lfs_placement": {}, "content": {}}
    assert probe_passed(ok_findings) is True
    bad_findings = {"stale_index_present": True, "lfs_placement": {}, "content": {}}
    assert probe_passed(bad_findings) is False
    dev_scratch_only = {"stale_index_present": False, "lfs_placement": {},
                         "content": {"_s2_postfix.md": Verdict.KNOWN_DEV_SCRATCH_ORPHAN.value}}
    assert probe_passed(dev_scratch_only) is True
    unexpected_orphan = {"stale_index_present": False, "lfs_placement": {},
                          "content": {"config.json": Verdict.ORPHANED_POINTER.value}}
    assert probe_passed(unexpected_orphan) is False

    assert "torch" not in sys.modules and "diffusers" not in sys.modules
    print("self-check: OK (all pure-core spec assertions passed)")
    return 0


# --- Action shell (network + filesystem) ---------------------------------

def fetch_manifest(api, repo_id: str, revision: str) -> tuple[list[str], dict[str, dict]]:
    """Action: file list + size/lfs metadata for one repo at one revision."""
    files = sorted(api.list_repo_files(repo_id, revision=revision))
    paths_info = api.get_paths_info(repo_id, files, revision=revision, expand=True)
    manifest: dict[str, dict] = {}
    for o in paths_info:
        lfs = getattr(o, "lfs", None)
        manifest[o.path] = {"size": getattr(o, "size", None), "is_lfs": lfs is not None}
    return files, manifest


def fetch_small_file_prefixes(repo_id: str, revision: str, files: list[str],
                               manifest: dict[str, dict], max_bytes: int = 64) -> dict[str, bytes]:
    """Action: download the first bytes of every non-large-pattern file, to
    check for orphaned LFS-pointer content. Never touches a large/binary file."""
    from huggingface_hub import hf_hub_download
    prefixes: dict[str, bytes] = {}
    for path in files:
        meta = manifest.get(path, {})
        if is_large_or_binary(path, meta.get("size")):
            continue
        local = hf_hub_download(repo_id, path, revision=revision)
        with open(local, "rb") as fh:
            prefixes[path] = fh.read(max_bytes)
    return prefixes


def probe_repo(api, repo_id: str, revision: str) -> dict:
    """Action facade for one checkpoint repo at one revision."""
    files, manifest = fetch_manifest(api, repo_id, revision)
    prefixes = fetch_small_file_prefixes(repo_id, revision, files, manifest)
    findings = derive_findings(repo_id, files, manifest, prefixes)
    return {
        "repo_id": repo_id,
        "revision": revision,
        "n_files": len(files),
        "n_small_files_content_checked": len(prefixes),
        "findings": findings,
        "passed": probe_passed(findings),
    }


def render_summary(bundle: dict) -> str:
    lines = ["# GPU-S2 checkpoint LFS/index verification — probe summary", ""]
    for r in bundle["repos"]:
        lines.append(f"## {r['repo_id']} @ {r['revision']}")
        lines.append(f"- files: {r['n_files']}; content-checked: {r['n_small_files_content_checked']}")
        lines.append(f"- stale index present: {r['findings']['stale_index_present']}")
        lines.append(f"- bad LFS placement: {r['findings']['lfs_placement'] or 'none'}")
        lines.append(f"- content findings: {r['findings']['content'] or 'none'}")
        lines.append(f"- **PASSED: {r['passed']}**")
        lines.append("")
    return "\n".join(lines)


def run_probe(out_dir: str) -> dict:
    """Action facade: probe both repos at their new revisions, write evidence."""
    from huggingface_hub import HfApi
    api = HfApi()
    repos = [
        probe_repo(api, FP8_REPO, FP8_REVISION),
        probe_repo(api, NVFP4_REPO, NVFP4_REVISION),
    ]
    bundle = {"repos": repos}
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "evidence.json"), "w") as fh:
        json.dump(bundle, fh, indent=2, sort_keys=True)
    with open(os.path.join(out_dir, "summary.md"), "w") as fh:
        fh.write(render_summary(bundle))
    return bundle


def main() -> int:
    ap = argparse.ArgumentParser(description="GPU-S2 checkpoint LFS/index verification probe")
    ap.add_argument("--check", action="store_true", help="run pure-core spec assertions only")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent), help="output dir")
    args = ap.parse_args()

    if args.check:
        return run_self_check()

    bundle = run_probe(args.out)
    print(render_summary(bundle))
    return 0 if all(r["passed"] for r in bundle["repos"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
