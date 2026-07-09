"""Action shell: evidence fragment file I/O. All probes and aggregate.py share this so the
on-disk shape (one JSON object per fragment file) never desyncs between writer and reader.
"""
from __future__ import annotations

import json
from pathlib import Path

from lib import EvidenceRecord, evidence_record_to_dict

FRAGMENT_DIR = Path(__file__).parent


def fragment_path(task_id: str) -> Path:
    return FRAGMENT_DIR / f"evidence_{task_id}.json"


def write_fragment(task_id: str, record: EvidenceRecord) -> Path:
    """Write `record` as `evidence_<task_id>.json`; returns the written path."""
    path = fragment_path(task_id)
    path.write_text(json.dumps(evidence_record_to_dict(record), indent=2, sort_keys=True) + "\n")
    return path


def read_all_fragments() -> dict[str, dict]:
    """Read every `evidence_*.json` fragment present, keyed by task_id (from the filename)."""
    fragments: dict[str, dict] = {}
    for path in sorted(FRAGMENT_DIR.glob("evidence_*.json")):
        task_id = path.stem[len("evidence_"):]
        fragments[task_id] = json.loads(path.read_text())
    return fragments
