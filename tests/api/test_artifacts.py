"""Spec: async-job-model — local artifact storage (E3 + traversal-safe)."""
from __future__ import annotations

from jobs.artifacts import _STUB_PNG, fetch, write_stub


def test_write_stub_then_fetch_roundtrip(tmp_path):
    path = write_stub("job123", directory=str(tmp_path))
    assert path.endswith("job123.png")
    found = fetch("job123", directory=str(tmp_path))
    assert found is not None
    fetched_path, media_type = found
    assert fetched_path == path and media_type == "image/png"
    with open(path, "rb") as handle:
        assert handle.read().startswith(b"\x89PNG\r\n\x1a\n")  # a valid PNG (sniffable)


def test_stub_is_a_valid_png():
    assert _STUB_PNG.startswith(b"\x89PNG\r\n\x1a\n")


def test_artifact_path_stays_within_directory_even_with_traversal_id(tmp_path):
    # a crafted job id with traversal/separators must not escape the artifact dir (sanitized basename)
    path = write_stub("../../etc/evil", directory=str(tmp_path))
    assert str(tmp_path) in path
    assert "/etc/evil" not in path


def test_fetch_missing_returns_none(tmp_path):
    assert fetch("does-not-exist", directory=str(tmp_path)) is None
