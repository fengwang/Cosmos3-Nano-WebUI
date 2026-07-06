"""Committed private-reference / secret scan (Session 5, MIG-S5).

Purpose (INV-1, R-01, R-14, EV-MIG-SCRUB, EV-MIG-DOCS-SCRUB): fail CI and local
runs if a private absolute path, a secret/token *value*, or a committed
model-weight / generated-media file appears anywhere on the change-controlled
public surface (`.github`, `api`, `webui`, `tests`, `schemas`, `docs`).

Sanity (EV-MIG-SCRUB-COMMAND-SANITY): a scan that matches its own pattern
documentation is a false positive. This module therefore (a) detects only
**high-confidence** signals — secret *values* and private *absolute paths*, not the
mere presence of words like "token"/"secret" (which occur legitimately across the
imported source: auth fields, TS `apiKey`, schema properties) — and (b) excludes
its own source and `docs/session_1/scrub_checklist.md`, which define the patterns.
The broader lexical name-assignment scan from the S1 checklist remains a
human-reviewed release-gate step (S8), where matches are triaged, not auto-blocked.

Structure (ACD): `scan_text` / `is_weight_media` / `is_excluded` are pure
Calculations; file reading in `scan_tree` and the `__main__` exit are the Actions
at the edges.

Run:
    uv run pytest tests/test_private_ref_scan.py       # gate (pass == clean)
    uv run python tests/test_private_ref_scan.py       # CLI (exit 1 == findings)
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Change-controlled public surface (the contract's scan surface + schemas).
SCAN_ROOTS = ("api", "webui", "tests", "schemas", "docs", ".github")

# Directories never scanned: generated, vendored, cache, or VCS.
EXCLUDE_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        ".next",
        ".benchmarks",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "coverage",
    }
)

# Files excluded from the content scan: this scanner (defines the patterns), the S1
# checklist (documents the patterns), and large generated lockfiles.
EXCLUDE_RELPATHS = frozenset(
    {
        "tests/test_private_ref_scan.py",
        "docs/session_1/scrub_checklist.md",
        "webui/pnpm-lock.yaml",
        "uv.lock",
    }
)

# Model-weight / generated-media file extensions (S1 checklist set). Detected by the
# committed file's extension, not by text mentions of the extension.
WEIGHT_MEDIA_EXTS = frozenset({".safetensors", ".pt", ".pth", ".ckpt", ".mp4", ".mov", ".avi"})

# Allowed placeholder path prefixes (contract-sanctioned examples).
ALLOWED_PLACEHOLDER_PREFIXES = ("/path/to/",)

# High-confidence secret *value* patterns.
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key_header", re.compile(r"BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY")),
    ("hf_token", re.compile(r"\bhf_[A-Za-z0-9]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
)

# Private absolute-path patterns. Each requires a real name component after the
# root, which (like `/home/[a-z]` failing to match because `[` is not a path char)
# lets these skip the *documented* scrub patterns in prior sessions' scan docs
# (`/data/home'`, `/data/home_[^ ]+`) while still catching a real leaked path.
# `/home/runner` is the GitHub Actions runner home and is not private.
PRIVATE_PATH_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("home_path", re.compile(r"/home/(?!runner\b)[A-Za-z0-9._-]+")),
    ("users_path", re.compile(r"/Users/[A-Za-z0-9._-]+")),
    ("private_mount", re.compile(r"/data/home[_/][A-Za-z0-9][A-Za-z0-9._/-]*")),
)


@dataclass(frozen=True)
class Finding:
    """A single scan hit (pure data)."""

    rel_path: str
    line: int
    rule: str
    snippet: str

    def __str__(self) -> str:
        return f"{self.rel_path}:{self.line}: [{self.rule}] {self.snippet}"


def is_weight_media(rel_path: str) -> bool:
    """Calculation: does this path name a model-weight / generated-media file?"""
    return Path(rel_path).suffix.lower() in WEIGHT_MEDIA_EXTS


def is_excluded(rel_path: str) -> bool:
    """Calculation: is this relative path excluded from the content scan?"""
    posix = rel_path.replace(os.sep, "/")
    if posix in EXCLUDE_RELPATHS:
        return True
    return any(part in EXCLUDE_DIR_NAMES for part in posix.split("/"))


def scan_text(rel_path: str, text: str) -> list[Finding]:
    """Calculation: return findings for one file's text (pure over its inputs).

    Allowed placeholder prefixes (e.g. ``/path/to/``) are never findings; the
    patterns already do not match them, and this guard keeps that true if a broader
    pattern is added later.
    """
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in (*SECRET_PATTERNS, *PRIVATE_PATH_PATTERNS):
            for m in pattern.finditer(line):
                token = m.group(0)
                if any(token.startswith(p) for p in ALLOWED_PLACEHOLDER_PREFIXES):
                    continue
                findings.append(Finding(rel_path, lineno, rule, token))
    return findings


def _iter_files(root: Path):
    """Action (edge): yield (rel_path, abs_path) for files under a scan root."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
        for name in filenames:
            abs_path = Path(dirpath) / name
            rel = abs_path.relative_to(REPO_ROOT).as_posix()
            yield rel, abs_path


def scan_tree(repo_root: Path = REPO_ROOT) -> list[Finding]:
    """Action + Calculation: walk the controlled surface and collect findings."""
    findings: list[Finding] = []
    for root_name in SCAN_ROOTS:
        root = repo_root / root_name
        if not root.exists():
            continue
        for rel, abs_path in _iter_files(root):
            if is_weight_media(rel):
                findings.append(Finding(rel, 0, "weight_media_file", abs_path.suffix))
                continue
            if is_excluded(rel):
                continue
            try:
                data = abs_path.read_bytes()
            except OSError:
                continue
            if b"\x00" in data:  # binary asset (image, font, ...) — not text
                continue
            findings.extend(scan_text(rel, data.decode("utf-8", errors="ignore")))
    return findings


# --------------------------------------------------------------------------- tests
# Fixtures are built by concatenation so no literal secret-shaped string is committed
# (EV-MIG-SCRUB-COMMAND-SANITY).


def test_private_key_header_is_caught():
    assert scan_text("x", "-----BEGIN " + "OPENSSH PRIVATE KEY-----")


def test_hf_and_sk_and_aws_tokens_caught():
    assert scan_text("x", "token=hf_" + "A" * 40)
    assert scan_text("x", "key=sk-" + "A" * 40)
    assert scan_text("x", "id=AKIA" + "ABCDEFGHIJKLMNOP")


def test_private_paths_caught():
    assert scan_text("x", "cd /home/" + "alice/project")
    assert scan_text("x", "/Users/" + "bob/dev")
    assert scan_text("x", "/data/home" + "_someone/models")


def test_runner_home_not_flagged():
    assert scan_text("x", "/home/runner/work/repo") == []


def test_weight_media_file_detected_by_extension():
    assert is_weight_media("models/unet.safetensors")
    assert is_weight_media("clips/demo.mp4")
    assert not is_weight_media("misc/logo.png")
    assert not is_weight_media("docs/notes.md")


def test_placeholder_not_flagged():
    assert scan_text("docs/x.md", "COSMOS3_MODEL_DIR=/path/to/Cosmos3-Nano-FP8-Blockwise") == []


def test_scanner_and_checklist_are_excluded():
    assert is_excluded("tests/test_private_ref_scan.py")
    assert is_excluded("docs/session_1/scrub_checklist.md")
    assert is_excluded("api/app/__pycache__/main.pyc")
    assert not is_excluded("api/app/main.py")


def test_clean_tree_has_no_findings():
    findings = scan_tree()
    assert findings == [], "private-reference scan findings:\n" + "\n".join(map(str, findings))


def _main() -> int:
    """Action (edge): CLI — scan and report; exit 1 on any finding."""
    findings = scan_tree()
    if findings:
        print(f"PRIVATE-REF SCAN: {len(findings)} finding(s):", file=sys.stderr)
        for f in findings:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("PRIVATE-REF SCAN: clean (0 findings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
