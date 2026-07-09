#!/usr/bin/env python3
"""Torch-free HF checkpoint LFS/index verification probe (GPU-S2).

Impure shell (network) around a pure core (classify-lfs-placement /
has-stale-index / classify-large-file-stability / derive-findings /
probe-passed / render). Imports neither ``torch`` nor ``diffusers``.
Complements ``docs/archive/phase-1/session_4/probes/verify_hf_checkpoints.py``
(loadability/drift) with the packaging checks GPU-S2 owns: no stale
top-level weight index, correct LFS-vs-regular-git placement by size/type
in *both* directions, and no large weight file silently de-LFS'd across the
fix (R-04).

Evidence source: ``HfApi.list_repo_files`` + ``HfApi.get_paths_info`` for
the manifest (size, `.lfs` attribute, LFS sha256) at both the pre-fix and
post-fix revision. No file's byte content is ever downloaded — a file's
``.lfs`` attribute reports whether its raw git blob is pointer-shaped
regardless of the *current* `.gitattributes` state (confirmed empirically:
this is a different, more reliable signal than `hf_hub_download`, whose
resolve endpoint transparently smudges LFS pointers even for a path no
current attribute rule matches — that path was tried during this session's
own sharded review and dropped for exactly this reason; see
``docs/session_2/sharded_review.md`` Correctness Finding 2).

Usage:
  python3 docs/session_2/probes/verify_gpu_s2_checkpoints.py            # full probe
  python3 docs/session_2/probes/verify_gpu_s2_checkpoints.py --check    # pure-core spec assertions
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
PRE_FIX_FP8_REVISION = "4e181f996abf03f3425298ef692e6e5e56fd46a4"
PRE_FIX_NVFP4_REVISION = "b5c9332efbaefa72c99890b1b1150da12ca9256c"
STALE_INDEX_NAME = "model.safetensors.index.json"
SIZE_THRESHOLD_BYTES = 10 * 1024 * 1024  # Owner Decision 4 (PRD): >10 MB -> LFS
# Non-plain-text extensions that use LFS regardless of size (Owner Decision 4).
BINARY_PATTERNS = ("*.safetensors", "*.pt", "*.pth", "*.ckpt", "*.mp4", "*.webm",
                    "*.png", "*.jpg", "*.jpeg", "*.mp3")
# Large/oversized files whose LFS sha256 must stay stable across the fix (R-04).
LARGE_FILE_PATTERNS = BINARY_PATTERNS + ("text_tokenizer/tokenizer.json",)
# Known, owner-approved exceptions: dev-scratch files (D3) left as orphaned
# LFS-pointer content on purpose (Owner Decision 3) — not a probe failure.
KNOWN_DEV_SCRATCH_ORPHANS = {
    FP8_REPO: {"_s2_postfix.md", "_s2_rerun.md", "_s2_verify.md"},
    NVFP4_REPO: {"transformer/producer_provenance.json"},
}


# --- Data (enums) ------------------------------------------------------

class Verdict(enum.Enum):
    OK = "ok"
    SHOULD_NOT_BE_LFS = "small_plain_text_incorrectly_lfs_backed"
    SHOULD_BE_LFS = "large_or_binary_file_missing_lfs_backing"  # R-04: de-LFS regression
    KNOWN_DEV_SCRATCH_ORPHAN = "known_dev_scratch_orphan_left_as_is"
    LFS_SHA_CHANGED = "large_file_lfs_sha256_changed_across_fix"  # R-04: content changed
    NOT_PROBED = "not_probed"  # e.g. path didn't exist at the pre-fix revision


# --- Pure calculations --------------------------------------------------

def is_large_or_binary(path: str, size: int | None) -> bool:
    """Pure: does this path legitimately stay LFS under Owner Decision 4?"""
    if size is not None and size > SIZE_THRESHOLD_BYTES:
        return True
    return any(fnmatch.fnmatch(path, pat) for pat in BINARY_PATTERNS)


def has_stale_index(files: list[str]) -> bool:
    """Pure: is the stale top-level weight index still present?"""
    return STALE_INDEX_NAME in files


def classify_lfs_placement(repo_id: str, path: str, size: int | None, is_lfs: bool) -> Verdict:
    """Pure: is this manifest entry's LFS-vs-regular placement correct, in
    EITHER direction — a small plain-text file wrongly LFS-backed, or a
    large/binary file that lost its LFS backing (the R-04 de-LFS regression).

    A known dev-scratch orphan (Owner Decision 3) is left LFS-pointer-shaped
    on purpose — it fails the general rule by design, not by regression.
    """
    if path in KNOWN_DEV_SCRATCH_ORPHANS.get(repo_id, ()):
        return Verdict.KNOWN_DEV_SCRATCH_ORPHAN
    expect_lfs = is_large_or_binary(path, size)
    if is_lfs and not expect_lfs:
        return Verdict.SHOULD_NOT_BE_LFS
    if expect_lfs and not is_lfs:
        return Verdict.SHOULD_BE_LFS
    return Verdict.OK


def is_large_file_pattern(path: str) -> bool:
    """Pure: is this one of the specific large/oversized files R-04 tracks?"""
    return any(fnmatch.fnmatch(path, pat) for pat in LARGE_FILE_PATTERNS)


def classify_large_file_stability(pre_sha: str | None, post_sha: str | None) -> Verdict:
    """Pure (R-04): did a large file's LFS content change across the fix?"""
    if pre_sha is None or post_sha is None:
        return Verdict.NOT_PROBED
    return Verdict.OK if pre_sha == post_sha else Verdict.LFS_SHA_CHANGED


def derive_findings(repo_id: str, files: list[str], manifest: dict[str, dict],
                     pre_fix_manifest: dict[str, dict]) -> dict:
    """Pure: assemble this repo's full verdict set from gathered evidence."""
    findings = {"stale_index_present": has_stale_index(files),
                "lfs_placement": {}, "large_file_stability": {}}
    for path in files:
        meta = manifest.get(path, {})
        v = classify_lfs_placement(repo_id, path, meta.get("size"), meta.get("is_lfs", False))
        if v is not Verdict.OK:
            findings["lfs_placement"][path] = v.value
        if is_large_file_pattern(path):
            pre_sha = pre_fix_manifest.get(path, {}).get("lfs_sha256")
            post_sha = meta.get("lfs_sha256")
            v2 = classify_large_file_stability(pre_sha, post_sha)
            if v2 is not Verdict.OK:
                findings["large_file_stability"][path] = v2.value
    return findings


def probe_passed(findings: dict) -> bool:
    """Pure: a repo passes iff no stale index, every LFS-placement finding
    is either OK or the known dev-scratch exception, and every large file's
    LFS content is stable across the fix (R-04) — `NOT_PROBED` is allowed
    (e.g. a file legitimately new in this fix has no pre-fix counterpart)."""
    if findings["stale_index_present"]:
        return False
    allowed_placement = {Verdict.KNOWN_DEV_SCRATCH_ORPHAN.value}
    bad_placement = {p: v for p, v in findings["lfs_placement"].items() if v not in allowed_placement}
    bad_stability = {p: v for p, v in findings["large_file_stability"].items()
                      if v == Verdict.LFS_SHA_CHANGED.value}
    return not bad_placement and not bad_stability


# --- Pure-core self test (spec-derived assertions) ----------------------

def run_self_check() -> int:
    """Pure spec-derived assertions; no network or filesystem. Returns process code."""
    assert is_large_or_binary("transformer/model.safetensors", 14_000_000_000) is True
    assert is_large_or_binary("text_tokenizer/tokenizer.json", 11_422_654) is True  # oversized text
    assert is_large_or_binary("transformer/modelopt_state.pt", 670_423) is True  # pattern, not size
    assert is_large_or_binary("config.json", 8166) is False
    assert is_large_or_binary("BIAS.md", 4720) is False

    assert has_stale_index(["config.json", "model.safetensors.index.json"]) is True
    assert has_stale_index(["config.json", "transformer/model.safetensors"]) is False

    # SHOULD_NOT_BE_LFS: a small plain-text file incorrectly LFS-backed.
    assert classify_lfs_placement(FP8_REPO, "config.json", 8166, True) is Verdict.SHOULD_NOT_BE_LFS
    assert classify_lfs_placement(FP8_REPO, "config.json", 8166, False) is Verdict.OK
    # SHOULD_BE_LFS: the R-04 de-LFS regression direction — a large file that lost LFS backing.
    assert classify_lfs_placement(
        FP8_REPO, "transformer/model.safetensors", 14_000_000_000, False) is Verdict.SHOULD_BE_LFS
    assert classify_lfs_placement(
        FP8_REPO, "transformer/model.safetensors", 14_000_000_000, True) is Verdict.OK
    # Known dev-scratch orphans are exempt in both repos, regardless of is_lfs.
    assert classify_lfs_placement(FP8_REPO, "_s2_postfix.md", 235, True) is Verdict.KNOWN_DEV_SCRATCH_ORPHAN
    assert classify_lfs_placement(
        NVFP4_REPO, "transformer/producer_provenance.json", 396, True) is Verdict.KNOWN_DEV_SCRATCH_ORPHAN

    assert is_large_file_pattern("transformer/model.safetensors") is True
    assert is_large_file_pattern("text_tokenizer/tokenizer.json") is True
    assert is_large_file_pattern("config.json") is False

    assert classify_large_file_stability("abc123", "abc123") is Verdict.OK
    assert classify_large_file_stability("abc123", "def456") is Verdict.LFS_SHA_CHANGED
    assert classify_large_file_stability(None, "def456") is Verdict.NOT_PROBED
    assert classify_large_file_stability("abc123", None) is Verdict.NOT_PROBED

    ok_findings = {"stale_index_present": False, "lfs_placement": {}, "large_file_stability": {}}
    assert probe_passed(ok_findings) is True
    bad_index = {"stale_index_present": True, "lfs_placement": {}, "large_file_stability": {}}
    assert probe_passed(bad_index) is False
    dev_scratch_only = {"stale_index_present": False,
                         "lfs_placement": {"_s2_postfix.md": Verdict.KNOWN_DEV_SCRATCH_ORPHAN.value},
                         "large_file_stability": {}}
    assert probe_passed(dev_scratch_only) is True
    unexpected_placement = {"stale_index_present": False,
                             "lfs_placement": {"config.json": Verdict.SHOULD_NOT_BE_LFS.value},
                             "large_file_stability": {}}
    assert probe_passed(unexpected_placement) is False
    de_lfs_regression = {"stale_index_present": False, "lfs_placement": {},
                          "large_file_stability": {"transformer/model.safetensors": Verdict.LFS_SHA_CHANGED.value}}
    assert probe_passed(de_lfs_regression) is False
    not_probed_is_fine = {"stale_index_present": False, "lfs_placement": {},
                           "large_file_stability": {"vae/config.json": Verdict.NOT_PROBED.value}}
    assert probe_passed(not_probed_is_fine) is True

    assert "torch" not in sys.modules and "diffusers" not in sys.modules
    print("self-check: OK (all pure-core spec assertions passed)")
    return 0


# --- Action shell (network only — no file content is ever downloaded) ---

def fetch_manifest(api, repo_id: str, revision: str) -> tuple[list[str], dict[str, dict]]:
    """Action: file list + size/lfs metadata for one repo at one revision."""
    files = sorted(api.list_repo_files(repo_id, revision=revision))
    paths_info = api.get_paths_info(repo_id, files, revision=revision, expand=True)
    manifest: dict[str, dict] = {}
    for o in paths_info:
        lfs = getattr(o, "lfs", None)
        manifest[o.path] = {
            "size": getattr(o, "size", None),
            "is_lfs": lfs is not None,
            "lfs_sha256": getattr(lfs, "sha256", None) if lfs else None,
        }
    return files, manifest


def probe_repo(api, repo_id: str, revision: str, pre_fix_revision: str) -> dict:
    """Action facade for one checkpoint repo: post-fix manifest (authoritative
    for the file list) plus the pre-fix manifest (for the R-04 stability check)."""
    files, manifest = fetch_manifest(api, repo_id, revision)
    _, pre_fix_manifest = fetch_manifest(api, repo_id, pre_fix_revision)
    findings = derive_findings(repo_id, files, manifest, pre_fix_manifest)
    return {
        "repo_id": repo_id,
        "revision": revision,
        "pre_fix_revision": pre_fix_revision,
        "n_files": len(files),
        "findings": findings,
        "passed": probe_passed(findings),
    }


def render_summary(bundle: dict) -> str:
    lines = ["# GPU-S2 checkpoint LFS/index verification — probe summary", ""]
    for r in bundle["repos"]:
        lines.append(f"## {r['repo_id']} @ {r['revision']} (pre-fix: {r['pre_fix_revision']})")
        lines.append(f"- files: {r['n_files']}")
        lines.append(f"- stale index present: {r['findings']['stale_index_present']}")
        lines.append(f"- LFS placement findings: {r['findings']['lfs_placement'] or 'none'}")
        lines.append(f"- large-file stability findings: {r['findings']['large_file_stability'] or 'none'}")
        lines.append(f"- **PASSED: {r['passed']}**")
        lines.append("")
    return "\n".join(lines)


def run_probe(out_dir: str) -> dict:
    """Action facade: probe both repos at their new revisions, write evidence."""
    from huggingface_hub import HfApi
    api = HfApi()
    repos = [
        probe_repo(api, FP8_REPO, FP8_REVISION, PRE_FIX_FP8_REVISION),
        probe_repo(api, NVFP4_REPO, NVFP4_REVISION, PRE_FIX_NVFP4_REVISION),
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
