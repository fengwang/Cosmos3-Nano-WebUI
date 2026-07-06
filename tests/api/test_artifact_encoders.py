"""Artifact encoders (host: trajectory JSON + import-safety; gated-live: png/mp4 via the oracle venv).

Spec: session_7/specs/{generation,action}-endpoints.md — the worker encodes the engine output into a
retrievable per-mode artifact. PNG/MP4 need numpy/PIL/imageio (the oracle extra), absent on the
torch-free host loop → guarded with importorskip; the trajectory JSON encoder is stdlib-pure.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from jobs import artifacts


def test_artifacts_module_imports_torch_free():
    # The module must import without numpy/PIL/imageio/torch (host loop) — heavy imports are deferred.
    assert hasattr(artifacts, "write_trajectory_json")
    assert hasattr(artifacts, "write_image_png")
    assert hasattr(artifacts, "write_video_mp4")


def test_write_trajectory_json_roundtrip(tmp_path):
    traj = [[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]]
    path = artifacts.write_trajectory_json(traj, "job-traj", directory=str(tmp_path))
    assert path.endswith(".json") and path.startswith(str(tmp_path))
    assert json.loads(Path(path).read_text()) == traj


def test_write_trajectory_json_accepts_array_like(tmp_path):
    class _Arr:
        def tolist(self):
            return [[1, 2], [3, 4]]

    path = artifacts.write_trajectory_json(_Arr(), "job-arr", directory=str(tmp_path))
    assert json.loads(Path(path).read_text()) == [[1, 2], [3, 4]]


def test_trajectory_path_is_traversal_safe(tmp_path):
    path = artifacts.write_trajectory_json([[0.0]], "../escape", directory=str(tmp_path))
    assert path.startswith(str(tmp_path))  # sanitized basename; stays within the directory


def test_write_image_png(tmp_path):
    np = pytest.importorskip("numpy")
    pytest.importorskip("PIL")
    frames = [np.zeros((8, 8, 3), dtype=np.float32)]
    path = artifacts.write_image_png(frames, "job-img", directory=str(tmp_path))
    assert path.endswith(".png")
    assert Path(path).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_write_video_mp4(tmp_path):
    np = pytest.importorskip("numpy")
    iio = pytest.importorskip("imageio.v3")
    pytest.importorskip("imageio_ffmpeg")
    frames = [np.zeros((16, 16, 3), dtype=np.float32) for _ in range(4)]
    path = artifacts.write_video_mp4(frames, "job-vid", directory=str(tmp_path), fps=8)
    assert path.endswith(".mp4")
    assert len(iio.imread(path, index=None)) == 4  # decodes to the written frame count
