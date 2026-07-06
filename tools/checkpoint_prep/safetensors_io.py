"""Pure safetensors header (de)serialization — no file I/O, no torch.

Safetensors layout: 8-byte little-endian uint64 header length N, then N bytes of JSON mapping
tensor-name -> {dtype, shape, data_offsets:[start,end]} (+ optional "__metadata__"), then the data
block (data_offsets are relative to the start of the data block). We only ever touch the header; tensor
payloads are copied verbatim by the shell (`rewrite.py`).
"""
from __future__ import annotations

import json
import struct

HEADER_ALIGN = 8


def parse_header(raw: bytes) -> tuple[dict, int]:
    """Parse the leading 8-byte length + JSON header from `raw`. Returns (header_dict, header_len N)."""
    if len(raw) < 8:
        raise ValueError("safetensors buffer too small for the 8-byte header length")
    n = struct.unpack("<Q", raw[:8])[0]
    if len(raw) < 8 + n:
        raise ValueError(f"safetensors header truncated: need {8 + n} bytes, have {len(raw)}")
    return json.loads(raw[8 : 8 + n]), n


def build_header_bytes(entries: dict, metadata: dict | None = None) -> bytes:
    """Serialize `entries` (name -> {dtype, shape, data_offsets}) to an 8-byte-aligned safetensors
    header: `struct.pack('<Q', N) + json (padded with spaces to a multiple of 8)`.

    The reference safetensors writer pads the header to an 8-byte boundary with trailing spaces (valid
    JSON whitespace), so the data block starts aligned. We reproduce that convention.
    """
    obj = dict(entries)
    if metadata is not None:
        obj["__metadata__"] = metadata
    blob = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    pad = (-len(blob)) % HEADER_ALIGN
    blob += b" " * pad
    return struct.pack("<Q", len(blob)) + blob
