#!/usr/bin/env python3
"""Merge every evidence_*.json fragment into evidence.json + summary.md
(docs/session_3/specs/evidence-aggregation.md).

Usage: uv run python aggregate.py
"""
from __future__ import annotations

import json

from evidence_io import FRAGMENT_DIR, read_all_fragments
from lib import merge_evidence, render_summary

EXPECTED_TASK_IDS = (
    "checkpoint_fetch_fp8",
    "checkpoint_fetch_nvfp4",
    "direct_t2i_fp8",
    "direct_t2i_nvfp4",
    "fullstack_t2i_fp8",
    "fullstack_t2i_nvfp4",
    "t2v_smoke",
)


def run() -> dict:
    fragments = read_all_fragments()
    merged = merge_evidence(fragments, expected_task_ids=EXPECTED_TASK_IDS)
    (FRAGMENT_DIR / "evidence.json").write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n")
    (FRAGMENT_DIR / "summary.md").write_text(render_summary(merged))
    return merged


if __name__ == "__main__":
    result = run()
    print(f"present: {result['present_task_ids']}")
    print(f"missing: {result['missing_task_ids']}")
