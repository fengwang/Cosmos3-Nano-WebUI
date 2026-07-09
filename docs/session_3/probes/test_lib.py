"""Unit tests for the pure calculations in lib.py. No GPU, no network, no filesystem."""
from __future__ import annotations

import io

from PIL import Image

from lib import (
    EvidenceRecord,
    FileInfo,
    Verdict,
    build_evidence_record,
    check_dockerfile_unmodified,
    check_job_terminal,
    check_no_lfs_pointers,
    check_no_stale_index,
    check_valid_image,
    check_valid_video,
    content_hash,
    encode_multipart,
    evidence_record_to_dict,
    merge_evidence,
    render_summary,
    sanitize_error_text,
)


def _valid_png_bytes(size: tuple[int, int] = (2, 2)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size).save(buf, format="PNG")
    return buf.getvalue()


def test_check_no_lfs_pointers_flags_a_pointer_file():
    files = (
        FileInfo(path="a.json", size=120, is_lfs_pointer=False),
        FileInfo(path="config.json", size=45, is_lfs_pointer=True),
    )
    assert check_no_lfs_pointers(files) == Verdict.FAIL


def test_check_no_lfs_pointers_passes_when_clean():
    files = (FileInfo(path="a.json", size=120, is_lfs_pointer=False),)
    assert check_no_lfs_pointers(files) == Verdict.PASS


def test_check_no_lfs_pointers_passes_on_empty_input():
    assert check_no_lfs_pointers(()) == Verdict.PASS


def test_check_no_stale_index_flags_top_level_index():
    files = (FileInfo(path="model.safetensors.index.json", size=900, is_lfs_pointer=False),)
    assert check_no_stale_index(files) == Verdict.FAIL


def test_check_no_stale_index_ignores_nested_index():
    files = (FileInfo(path="transformer/model.safetensors.index.json", size=900, is_lfs_pointer=False),)
    assert check_no_stale_index(files) == Verdict.PASS


def test_check_valid_image_rejects_non_image_bytes():
    assert check_valid_image(b"not an image", expected_dims=None) == Verdict.FAIL


def test_check_valid_image_accepts_a_real_png():
    assert check_valid_image(_valid_png_bytes(), expected_dims=None) == Verdict.PASS


def test_check_valid_image_checks_expected_dims():
    png = _valid_png_bytes((4, 4))
    assert check_valid_image(png, expected_dims=(4, 4)) == Verdict.PASS
    assert check_valid_image(png, expected_dims=(8, 8)) == Verdict.FAIL


def test_check_valid_image_rejects_empty_bytes():
    assert check_valid_image(b"", expected_dims=None) == Verdict.FAIL


def test_check_job_terminal_pass_on_succeeded():
    assert check_job_terminal(("queued", "running", "succeeded")) == Verdict.PASS


def test_check_job_terminal_fail_on_failed():
    assert check_job_terminal(("queued", "running", "failed")) == Verdict.FAIL


def test_check_job_terminal_fail_when_never_terminal():
    assert check_job_terminal(("queued", "running")) == Verdict.FAIL


def test_sanitize_error_text_redacts_every_occurrence_of_every_prefix():
    # Deliberately not shaped like a real private-path prefix (see
    # tests/test_private_ref_scan.py's home_path/workspace_path rules) — this file is
    # committed, and the redaction logic itself is prefix-agnostic, so any two distinct
    # absolute-path-shaped strings exercise it equally well.
    text = "Command '/opt/example/y --dir /opt/example/y/z' failed; see /srv/example-repo/models"
    result = sanitize_error_text(text, redact_prefixes=("/opt/example/y", "/srv/example-repo"))
    assert "/opt/example/y" not in result
    assert "/srv/example-repo" not in result
    assert result.count("<redacted>") == 3  # two /opt/example/y occurrences + one /srv/example-repo


def test_sanitize_error_text_is_a_noop_without_a_match():
    assert sanitize_error_text("no paths here", redact_prefixes=("/opt/example",)) == "no paths here"


def test_content_hash_is_deterministic_and_matches_known_sha256():
    assert content_hash(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert content_hash(b"abc") == content_hash(b"abc")
    assert content_hash(b"abc") != content_hash(b"abd")


def test_check_job_terminal_uses_explicit_success_status_for_video():
    assert check_job_terminal(("queued", "completed"), success_status="completed") == Verdict.PASS
    assert check_job_terminal(("queued", "completed")) == Verdict.FAIL  # default is "succeeded"


def test_check_valid_video_accepts_mp4_signature():
    mp4_header = b"\x00\x00\x00\x18" + b"ftyp" + b"\x00" * 16
    assert check_valid_video(mp4_header) == Verdict.PASS


def test_check_valid_video_accepts_webm_signature():
    webm_header = b"\x1a\x45\xdf\xa3" + b"\x00" * 16
    assert check_valid_video(webm_header) == Verdict.PASS


def test_check_valid_video_rejects_short_or_unrecognized_bytes():
    assert check_valid_video(b"not a video") == Verdict.FAIL
    assert check_valid_video(b"") == Verdict.FAIL


def test_check_valid_video_rejects_long_bytes_with_no_valid_signature():
    # >=12 bytes (past the length guard) but neither the MP4 nor WebM signature —
    # a body-shaped-but-wrong-container response must still fail, not merely short input.
    assert check_valid_video(b"\x00" * 20) == Verdict.FAIL


def test_encode_multipart_is_deterministic_given_a_boundary():
    form = {"prompt": "a cat", "seed": "42"}
    ct1, body1 = encode_multipart(form, boundary="fixedboundary")
    ct2, body2 = encode_multipart(form, boundary="fixedboundary")
    assert (ct1, body1) == (ct2, body2)
    assert b"a cat" in body1 and b"fixedboundary" in body1


def test_check_dockerfile_unmodified_pass_when_clean():
    assert check_dockerfile_unmodified(has_uncommitted_diff=False) == Verdict.PASS


def test_check_dockerfile_unmodified_fail_when_dirty():
    assert check_dockerfile_unmodified(has_uncommitted_diff=True) == Verdict.FAIL


def test_build_evidence_record_requires_notes_on_non_pass():
    try:
        build_evidence_record(
            task_id="t", hardware="h", driver_cuda="d", checkpoint_repo="r",
            checkpoint_revision="rev", vllm_omni_commit="c", request_shape={},
            artifact_path=None, artifact_metadata=None, verdict=Verdict.FAIL,
            run_at="2026-07-09T00:00:00+00:00", notes="",
        )
    except ValueError:
        return
    raise AssertionError("expected ValueError for FAIL verdict with empty notes")


def test_merge_evidence_lists_missing_without_failing():
    fragments = {"t1": {"verdict": "PASS"}}
    merged = merge_evidence(fragments, expected_task_ids=("t1", "t2"))
    assert merged["present_task_ids"] == ("t1",)
    assert merged["missing_task_ids"] == ("t2",)
    assert merged["unexpected_task_ids"] == ()


def test_merge_evidence_is_deterministic():
    fragments = {"t1": {"verdict": "PASS"}, "t2": {"verdict": "FAIL"}}
    a = merge_evidence(fragments, expected_task_ids=("t1", "t2"))
    b = merge_evidence(fragments, expected_task_ids=("t1", "t2"))
    assert a == b


def test_render_summary_lists_missing_and_non_pass_notes():
    fragments = {
        "t1": {
            "verdict": "FAIL", "notes": "boom", "checkpoint_revision": "abcdef0123456789",
            "vllm_omni_commit": "0123456789abcdef", "request_shape": {"mode": "t2i"},
        },
    }
    merged = merge_evidence(fragments, expected_task_ids=("t1", "t2"))
    summary = render_summary(merged)
    assert "t1" in summary and "FAIL" in summary and "boom" in summary
    assert "t2" in summary  # listed as missing


def test_build_evidence_record_allows_empty_notes_on_pass():
    record = build_evidence_record(
        task_id="t", hardware="h", driver_cuda="d", checkpoint_repo="r",
        checkpoint_revision="rev", vllm_omni_commit="c", request_shape={},
        artifact_path="/tmp/a.png", artifact_metadata={}, verdict=Verdict.PASS,
        run_at="2026-07-09T00:00:00+00:00", notes="",
    )
    assert isinstance(record, EvidenceRecord)
    assert record.verdict == Verdict.PASS


def test_build_evidence_record_preserves_every_field_without_transposition():
    # Distinct values per field, not just distinct types — catches a field mix-up
    # (e.g. checkpoint_repo/checkpoint_revision swapped) that isinstance()/one-field
    # assertions would miss (INV-8: every field must attribute the right repo/revision).
    record = build_evidence_record(
        task_id="task-1", hardware="hw-1", driver_cuda="driver-1", checkpoint_repo="repo-1",
        checkpoint_revision="rev-1", vllm_omni_commit="commit-1", request_shape={"k": "v"},
        artifact_path="art.png", artifact_metadata={"m": 1}, verdict=Verdict.PASS,
        run_at="2026-07-09T01:23:45+00:00", notes="",
    )
    assert record.task_id == "task-1"
    assert record.hardware == "hw-1"
    assert record.driver_cuda == "driver-1"
    assert record.checkpoint_repo == "repo-1"
    assert record.checkpoint_revision == "rev-1"
    assert record.vllm_omni_commit == "commit-1"
    assert record.request_shape == {"k": "v"}
    assert record.artifact_path == "art.png"
    assert record.artifact_metadata == {"m": 1}
    assert record.run_at == "2026-07-09T01:23:45+00:00"


def test_evidence_record_to_dict_renders_bare_verdict_name():
    # render_summary compares this dict's "verdict" against the literal string "PASS" —
    # str(Verdict.PASS) would instead produce "Verdict.PASS" and silently break that compare.
    record = build_evidence_record(
        task_id="t", hardware="h", driver_cuda="d", checkpoint_repo="r",
        checkpoint_revision="rev", vllm_omni_commit="c", request_shape={"mode": "t2i"},
        artifact_path="a.png", artifact_metadata={"size_bytes": 1}, verdict=Verdict.PASS,
        run_at="2026-07-09T00:00:00+00:00", notes="",
    )
    as_dict = evidence_record_to_dict(record)
    assert as_dict["verdict"] == "PASS"
    assert as_dict == {
        "task_id": "t", "hardware": "h", "driver_cuda": "d", "checkpoint_repo": "r",
        "checkpoint_revision": "rev", "vllm_omni_commit": "c", "request_shape": {"mode": "t2i"},
        "run_at": "2026-07-09T00:00:00+00:00",
        "artifact_path": "a.png", "artifact_metadata": {"size_bytes": 1}, "verdict": "PASS", "notes": "",
    }
