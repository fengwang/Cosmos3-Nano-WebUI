"""Prove the hand-rolled safetensors writer (`build_header_bytes` + raw data block) produces a file the
real `safetensors` library accepts — the critical de-risk for the real 17.5 GB rewrite.

Uses F32 tensors with self-consistent byte counts (numpy has no bf16) so `safe_open(framework="numpy")`
can materialize them and confirm the header offsets/padding are valid.
"""
from __future__ import annotations

import struct

import pytest

from checkpoint_prep.safetensors_io import build_header_bytes, parse_header

np = pytest.importorskip("numpy")
safetensors = pytest.importorskip("safetensors")
from safetensors import safe_open  # noqa: E402


def _write(path, arrays):
    entries, blob, cursor = {}, bytearray(), 0
    for name, arr in arrays.items():
        raw = arr.tobytes()
        entries[name] = {"dtype": "F32", "shape": list(arr.shape), "data_offsets": [cursor, cursor + len(raw)]}
        blob += raw
        cursor += len(raw)
    path.write_bytes(build_header_bytes(entries) + bytes(blob))


def test_writer_output_loads_in_safetensors_library(tmp_path):
    arrays = {
        "layers.0.mlp.gate_proj.weight": np.arange(24, dtype=np.float32).reshape(6, 4),
        "lm_head.weight": np.linspace(-1, 1, 20, dtype=np.float32).reshape(5, 4),
        "action_proj_in.fc.weight": np.full((2, 3), 7.0, dtype=np.float32),
    }
    p = tmp_path / "model.safetensors"
    _write(p, arrays)

    with safe_open(str(p), framework="numpy") as f:
        assert set(f.keys()) == set(arrays)
        for name, expected in arrays.items():
            np.testing.assert_array_equal(f.get_tensor(name), expected)


def test_writer_header_is_8byte_aligned_and_reparses(tmp_path):
    arrays = {"a": np.zeros((3,), dtype=np.float32), "b": np.ones((5,), dtype=np.float32)}
    p = tmp_path / "m.safetensors"
    _write(p, arrays)
    raw = p.read_bytes()
    n = struct.unpack("<Q", raw[:8])[0]
    assert (8 + n) % 8 == 0  # data block starts 8-byte aligned
    header, _ = parse_header(raw)
    assert set(k for k in header if k != "__metadata__") == {"a", "b"}
