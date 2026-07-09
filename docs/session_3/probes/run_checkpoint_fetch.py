#!/usr/bin/env python3
"""T1: fresh `hf download` of one checkpoint at its GPU-S2-pinned revision, verified for no
unresolved LFS pointers and no stale top-level weight index (docs/session_3/specs/
gpu-validation-probes.md, "Fresh checkpoint fetch verification").

Usage: uv run python run_checkpoint_fetch.py --checkpoint {fp8,nvfp4}
"""
from __future__ import annotations

import argparse
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from constants import CHECKPOINTS, REDACT_PREFIXES, VLLM_OMNI_COMMIT
from env_probe import get_hardware_and_driver
from evidence_io import write_fragment
from lib import (
    FileInfo,
    Verdict,
    build_evidence_record,
    check_no_lfs_pointers,
    check_no_stale_index,
    sanitize_error_text,
)

_LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"
REPO_ROOT = Path(__file__).resolve().parents[3]


def _is_lfs_pointer(path: Path) -> bool:
    """Action: sniff a file's first bytes for the literal LFS-pointer-file signature.

    This checks the *downloaded* file's real content (not the source repo's git-attribute
    state, which GPU-S2 already verified via the Hub API) — the question here is narrower
    and simpler: did this session's own fresh download land real content on disk.
    """
    try:
        with path.open("rb") as handle:
            return handle.read(len(_LFS_POINTER_PREFIX)) == _LFS_POINTER_PREFIX
    except OSError:
        return False


def _list_checkpoint_files(local_dir: Path) -> tuple[FileInfo, ...]:
    """Action: walk `local_dir` and build the FileInfo tuple the pure checkers consume."""
    files = []
    for path in sorted(local_dir.rglob("*")):
        if path.is_file():
            rel = str(path.relative_to(local_dir))
            files.append(FileInfo(path=rel, size=path.stat().st_size, is_lfs_pointer=_is_lfs_pointer(path)))
    return tuple(files)


def fetch_checkpoint(repo_id: str, revision: str, local_dir: Path) -> None:
    """Action: fresh `hf download`. Raises `subprocess.CalledProcessError`/`TimeoutExpired`
    on failure. `hf download` resumes from any already-fetched blobs in `local_dir` on a
    retry rather than restarting, so a timeout here is recoverable by re-running with a
    larger budget (classified ENVIRONMENT during GPU-S3's own NVFP4 fetch: the 3600s
    original budget was too tight for this checkpoint's actual transfer time).
    """
    subprocess.run(
        ["hf", "download", repo_id, "--revision", revision, "--local-dir", str(local_dir)],
        check=True, timeout=7200,
    )


def run(checkpoint: str) -> Verdict:
    spec = CHECKPOINTS[checkpoint]
    local_dir = REPO_ROOT / spec.local_dir
    task_id = f"checkpoint_fetch_{checkpoint}"
    hardware, driver_cuda = "unknown", "unknown"
    notes = ""
    try:
        hardware, driver_cuda = get_hardware_and_driver()
        fetch_checkpoint(spec.repo_id, spec.revision, local_dir)
        files = _list_checkpoint_files(local_dir)
        lfs_verdict = check_no_lfs_pointers(files)
        index_verdict = check_no_stale_index(files)
        if lfs_verdict == Verdict.FAIL:
            bad = [f.path for f in files if f.is_lfs_pointer]
            notes = f"unresolved LFS pointer(s) in fresh download: {bad}"
            verdict = Verdict.FAIL
        elif index_verdict == Verdict.FAIL:
            notes = "stale top-level model.safetensors.index.json present in fresh download"
            verdict = Verdict.FAIL
        else:
            verdict = Verdict.PASS
        artifact_metadata = {"file_count": len(files), "total_bytes": sum(f.size for f in files)}
    except Exception as exc:  # noqa: BLE001 — single narrow boundary; see gpu-validation-probes.md
        verdict = Verdict.FAIL
        notes = sanitize_error_text(f"{type(exc).__name__}: {exc}", REDACT_PREFIXES)
        artifact_metadata = None

    record = build_evidence_record(
        task_id=task_id,
        hardware=hardware,
        driver_cuda=driver_cuda,
        checkpoint_repo=spec.repo_id,
        checkpoint_revision=spec.revision,
        vllm_omni_commit=VLLM_OMNI_COMMIT,
        run_at=datetime.now(UTC).isoformat(),
        request_shape={"action": "hf_download", "local_dir": str(spec.local_dir)},
        artifact_path=spec.local_dir,  # repo-root-relative; never the host's absolute prefix (INV-1)
        artifact_metadata=artifact_metadata,
        verdict=verdict,
        notes=notes,
    )
    path = write_fragment(task_id, record)
    print(f"[{checkpoint}] verdict={verdict.name} notes={notes!r} -> {path}")
    return verdict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", choices=sorted(CHECKPOINTS), required=True)
    args = parser.parse_args()
    result = run(args.checkpoint)
    raise SystemExit(0 if result == Verdict.PASS else 1)
