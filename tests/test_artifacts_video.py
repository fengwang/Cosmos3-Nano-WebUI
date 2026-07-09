"""Tests for video artifact writers (spec: vllm-omni-generation-adapter byte-passthrough;
legacy-hygiene-cherrypick fps). Host-testable; no torch, no encode for the passthrough path.
"""
from __future__ import annotations

import os

from jobs import artifacts


def test_write_video_bytes_writes_unmodified(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    data = b"\x00\x01MP4-BYTES\xff"
    path = artifacts.write_video_bytes(data, "job-abc")
    assert path.startswith(str(tmp_path))
    assert path.endswith(".mp4")
    with open(path, "rb") as fh:
        assert fh.read() == data  # byte-for-byte, no re-encode (fps/frames preserved)


def test_write_video_bytes_rejects_traversal(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    path = artifacts.write_video_bytes(b"x", "../../etc/evil")  # crafted id
    real = os.path.realpath(path)
    assert real.startswith(os.path.realpath(str(tmp_path)) + os.sep)  # contained (INV-8)


def test_default_video_fps_is_24():
    # phase-4 441ad51 cherry-pick (R-06): frame-based encoders default to 24 fps, not 16.
    import inspect

    assert inspect.signature(artifacts.write_video_mp4).parameters["fps"].default == 24
    assert inspect.signature(artifacts.write_video_with_audio).parameters["fps"].default == 24
