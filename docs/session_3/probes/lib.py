"""Pure calculations + data shapes shared by every GPU-S3 probe (docs/session_3/design.md D1/D2).

No I/O, no clock, no network, no subprocess anywhere in this module — every `run_*.py` action
script gathers raw data itself and passes it in here as plain parameters. This module is fully
testable without a GPU (see test_lib.py).
"""
from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from enum import Enum, auto

from PIL import Image
from PIL import UnidentifiedImageError

_TOP_LEVEL_STALE_INDEX = "model.safetensors.index.json"
_TERMINAL_SUCCESS = "succeeded"


class Verdict(Enum):
    """A probe's tri-state outcome. Never a bare bool (a FAIL/SCOPED_OUT distinction matters)."""

    PASS = auto()
    FAIL = auto()
    SCOPED_OUT = auto()


@dataclass(frozen=True)
class FileInfo:
    """One file's evidence-relevant facts from a checkpoint directory listing."""

    path: str
    size: int
    is_lfs_pointer: bool


@dataclass(frozen=True)
class EvidenceRecord:
    """One probe's recorded outcome — the INV-8 field set (project_contract.md §3) plus
    `run_at`, an explicit provenance timestamp (ISO 8601, caller-supplied — this module
    never reads a clock itself). Without it, two fragments with identical content are
    indistinguishable from "genuinely re-run and got the same result" vs. "never re-run at
    all" — exactly the gap a fresh-context adversarial verifier found in this session when
    a checkpoint-mount fix landed after a fragment was written: the fragment's hash alone
    couldn't prove whether it reflected a rerun against the fix or a stale pre-fix result.
    """

    task_id: str
    hardware: str
    driver_cuda: str
    checkpoint_repo: str
    checkpoint_revision: str
    vllm_omni_commit: str
    request_shape: dict
    artifact_path: str | None
    artifact_metadata: dict | None
    verdict: Verdict
    run_at: str
    notes: str = ""


def check_no_lfs_pointers(files: tuple[FileInfo, ...]) -> Verdict:
    """Verdict.PASS iff no file in `files` is an unresolved LFS/Xet pointer."""
    return Verdict.FAIL if any(f.is_lfs_pointer for f in files) else Verdict.PASS


def check_no_stale_index(files: tuple[FileInfo, ...]) -> Verdict:
    """Verdict.PASS iff no file in `files` is a top-level `model.safetensors.index.json`.

    A nested index (e.g. `transformer/model.safetensors.index.json`) is not the stale-top-level
    packaging bug GPU-S2 fixed, so it does not fail this check.
    """
    stale = any(f.path == _TOP_LEVEL_STALE_INDEX for f in files)
    return Verdict.FAIL if stale else Verdict.PASS


def check_valid_image(image_bytes: bytes, expected_dims: tuple[int, int] | None) -> Verdict:
    """Verdict.PASS iff `image_bytes` decodes as a valid image and, when `expected_dims` is
    given, its (width, height) matches exactly.

    Pure: decodes only the in-memory `image_bytes` parameter; no filesystem/network access.
    A decode failure is expected, meaningful domain data here (bad artifact), not a bug —
    it is caught narrowly and returned as Verdict.FAIL rather than propagated.
    """
    if not image_bytes:
        return Verdict.FAIL
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.verify()
        if expected_dims is not None:
            with Image.open(io.BytesIO(image_bytes)) as img:
                if img.size != expected_dims:
                    return Verdict.FAIL
    except (UnidentifiedImageError, OSError):
        return Verdict.FAIL
    return Verdict.PASS


def check_job_terminal(status_history: tuple[str, ...], success_status: str = _TERMINAL_SUCCESS) -> Verdict:
    """Verdict.PASS iff the last entry in `status_history` equals `success_status`; FAIL
    otherwise (including a failure/cancellation status, or a history that never reached a
    terminal state). `success_status` is explicit because the jobs API uses "succeeded"
    while vLLM-Omni's own async video API uses "completed" — no hidden vocabulary assumption.
    """
    if not status_history:
        return Verdict.FAIL
    return Verdict.PASS if status_history[-1] == success_status else Verdict.FAIL


def sanitize_error_text(text: str, redact_prefixes: tuple[str, ...]) -> str:
    """Pure: replace every occurrence of each `redact_prefixes` string in `text` with
    "<redacted>". Exception messages from a failed subprocess call
    (`CalledProcessError`/`TimeoutExpired`) embed the full argv, including any absolute
    host path passed to it — this is the general-purpose guard against that leaking into a
    committed evidence fragment's `notes` field (project_contract.md INV-1), applied at
    every run_*.py script's exception boundary rather than left to the specific fields that
    happened to leak once (see docs/session_3/design.md's INV-1 finding).
    """
    for prefix in redact_prefixes:
        if prefix:
            text = text.replace(prefix, "<redacted>")
    return text


def content_hash(data: bytes) -> str:
    """Pure: `sha256(data).hexdigest()`. Lets evidence cite an artifact by hash+size
    instead of committing the binary (project_contract.md §6: no generated media in-repo),
    matching the precedent in docs/evidence_map.md's GPU-S1 T2I row.
    """
    return hashlib.sha256(data).hexdigest()


def check_valid_video(video_bytes: bytes) -> Verdict:
    """Verdict.PASS iff `video_bytes` starts with a recognized MP4 or WebM container
    signature. Pure: sniffs only the in-memory bytes parameter.
    """
    if len(video_bytes) < 12:
        return Verdict.FAIL
    is_mp4 = video_bytes[4:8] == b"ftyp"
    is_webm = video_bytes[:4] == b"\x1a\x45\xdf\xa3"
    return Verdict.PASS if (is_mp4 or is_webm) else Verdict.FAIL


def encode_multipart(form: dict[str, str], boundary: str) -> tuple[str, bytes]:
    """Pure: encode a `str -> str` form as `multipart/form-data`. Returns (content_type, body).

    `boundary` is an explicit parameter (never generated internally via `uuid4`/`random`)
    so the same form always encodes to the same bytes — this stays a Calculation.
    """
    parts: list[bytes] = []
    for key, value in form.items():
        parts += [
            f"--{boundary}".encode(),
            f'Content-Disposition: form-data; name="{key}"'.encode(),
            b"",
            str(value).encode("utf-8"),
        ]
    parts += [f"--{boundary}--".encode(), b""]
    return f"multipart/form-data; boundary={boundary}", b"\r\n".join(parts)


def check_dockerfile_unmodified(has_uncommitted_diff: bool) -> Verdict:
    """Verdict.PASS iff `deploy/vllm-omni.Dockerfile` has no uncommitted diff against HEAD.

    This session is forbidden from editing that file (session_3_contract.yaml
    blast_radius.forbidden_files), so "no diff" is sufficient evidence that the cached
    `cosmos3-nano-vllm-omni:local` image — built and evidenced by GPU-S1 — still reflects
    its content. mtime comparison was tried first and rejected: `git checkout` bumps a
    file's mtime on branch switch even when its content is byte-identical (confirmed via
    a real GPU-S3 branch switch, which made the Dockerfile look "newer" than the image
    despite an identical sha256), so mtime is not a reliable signal in a git workflow.
    """
    return Verdict.FAIL if has_uncommitted_diff else Verdict.PASS


def evidence_record_to_dict(record: EvidenceRecord) -> dict:
    """Pure: `EvidenceRecord` -> a JSON-serializable dict (`Verdict` becomes its `.name` string)."""
    return {
        "task_id": record.task_id,
        "hardware": record.hardware,
        "driver_cuda": record.driver_cuda,
        "checkpoint_repo": record.checkpoint_repo,
        "checkpoint_revision": record.checkpoint_revision,
        "vllm_omni_commit": record.vllm_omni_commit,
        "request_shape": record.request_shape,
        "artifact_path": record.artifact_path,
        "artifact_metadata": record.artifact_metadata,
        "verdict": record.verdict.name,
        "run_at": record.run_at,
        "notes": record.notes,
    }


def merge_evidence(fragments: dict[str, dict], expected_task_ids: tuple[str, ...]) -> dict:
    """Pure: merge fragment dicts into one evidence bundle. Never fails on a missing
    fragment — `expected_task_ids` not present in `fragments` are listed under `missing`
    rather than raising, per evidence-aggregation.md's "aggregates without blocking".
    """
    present = tuple(k for k in expected_task_ids if k in fragments)
    missing = tuple(k for k in expected_task_ids if k not in fragments)
    unexpected = tuple(k for k in fragments if k not in expected_task_ids)
    return {
        "fragments": dict(fragments),
        "present_task_ids": present,
        "missing_task_ids": missing,
        "unexpected_task_ids": unexpected,
    }


def render_summary(merged: dict) -> str:
    """Pure: `merge_evidence`'s output -> a human-readable Markdown summary."""
    lines = ["# GPU-S3 Evidence Summary", ""]
    lines.append("| Task | Verdict | Checkpoint Revision | vLLM-Omni Commit | Request Mode | Run At |")
    lines.append("|---|---|---|---|---|---|")
    for task_id in merged["present_task_ids"]:
        frag = merged["fragments"][task_id]
        mode = (frag.get("request_shape") or {}).get("mode", "-")
        lines.append(
            f"| {task_id} | {frag['verdict']} | {frag['checkpoint_revision'][:12]} "
            f"| {frag['vllm_omni_commit'][:12]} | {mode} | {frag.get('run_at', '-')} |"
        )
    if merged["missing_task_ids"]:
        lines.append("")
        lines.append(f"**Missing (not yet run):** {', '.join(merged['missing_task_ids'])}")
    lines.append("")
    for task_id in merged["present_task_ids"]:
        frag = merged["fragments"][task_id]
        if frag["verdict"] != "PASS":
            lines.append(f"- **{task_id}** ({frag['verdict']}): {frag['notes']}")
    return "\n".join(lines) + "\n"


def build_evidence_record(
    *,
    task_id: str,
    hardware: str,
    driver_cuda: str,
    checkpoint_repo: str,
    checkpoint_revision: str,
    vllm_omni_commit: str,
    request_shape: dict,
    artifact_path: str | None,
    artifact_metadata: dict | None,
    verdict: Verdict,
    run_at: str,
    notes: str = "",
) -> EvidenceRecord:
    """Build an `EvidenceRecord`.

    Raises `ValueError` if `verdict` is not `Verdict.PASS` and `notes` is empty — a
    non-passing result must always carry a reason (no silent FAIL/SCOPED_OUT). `run_at`
    is required (no default): every real evidence record needs a provenance timestamp,
    gathered by the caller (e.g. `datetime.now(timezone.utc).isoformat()`) — this stays a
    Calculation because the clock read happens at the call site, not in here.
    """
    if verdict != Verdict.PASS and not notes:
        raise ValueError(f"notes is required when verdict is {verdict.name}")
    return EvidenceRecord(
        task_id=task_id,
        hardware=hardware,
        driver_cuda=driver_cuda,
        checkpoint_repo=checkpoint_repo,
        checkpoint_revision=checkpoint_revision,
        vllm_omni_commit=vllm_omni_commit,
        request_shape=request_shape,
        artifact_path=artifact_path,
        artifact_metadata=artifact_metadata,
        verdict=verdict,
        run_at=run_at,
        notes=notes,
    )
