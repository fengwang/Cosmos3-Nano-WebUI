#!/usr/bin/env python3
"""AM-S6 deterministic check: relative-link + in-page-anchor resolver.

Scope (per docs/session_6_contract.yaml deterministic_checks): README.md, docs/walkthrough.md,
docs/model_setup.md. Every relative file link must point to an existing repo path, and every
`#anchor` fragment must match a heading slug (GitHub's algorithm) in its target document.

Conventions (matching how the contract phrases placeholder paths, e.g. `docs/images/x.png` written
inside docs/walkthrough.md): relative paths are resolved **repo-root-relative**. External links
(http/https/mailto) are skipped. Image placeholders under `docs/images/` are exempt from the
existence check by design — they are the owner-filled placeholders (INV-1), not yet present.

Usage:
    python docs/session_6/check_links.py            # check the three contract docs; exit 0 iff all resolve
    python docs/session_6/check_links.py --selftest # negative control: a broken anchor must be caught
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_DOCS = ["README.md", "docs/walkthrough.md", "docs/model_setup.md"]
IMAGE_PLACEHOLDER_PREFIX = "docs/images/"  # exempt from existence (INV-1 placeholders)

_MD_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")  # [t](url) / ![t](url "title")
_HTML_LINK = re.compile(r"(?:href|src)\s*=\s*[\"']([^\"']+)[\"']")
_ATX_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE = re.compile(r"^\s*(```+|~~~+)")


def _strip_inline_markdown(text: str) -> str:
    """Reduce heading text to what GitHub slugs: link text only, no code/emphasis markers."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # [text](url) -> text
    text = text.replace("`", "").replace("**", "").replace("*", "").replace("~~", "")
    return text


def github_slug(heading_text: str) -> str:
    """Approximate github-slugger: lowercase, drop chars outside [a-z0-9 _-], spaces -> '-'."""
    s = _strip_inline_markdown(heading_text).strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)  # \w keeps underscores (GitHub does too)
    s = s.replace(" ", "-")
    return s


def slugs_of(path: Path) -> set[str]:
    """The set of anchor slugs a markdown file exposes (headings outside code fences, de-duped)."""
    slugs: set[str] = set()
    counts: dict[str, int] = {}
    in_fence = False
    fence_marker = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _FENCE.match(line)
        if m:
            marker = m.group(1)[:3]
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif line.strip().startswith(fence_marker):
                in_fence = False
            continue
        if in_fence:
            continue
        h = _ATX_HEADING.match(line)
        if not h:
            continue
        base = github_slug(h.group(2))
        n = counts.get(base, 0)
        slug = base if n == 0 else f"{base}-{n}"
        counts[base] = n + 1
        slugs.add(slug)
    return slugs


def _iter_links(path: Path):
    """Yield (lineno, target) for md + html links, skipping fenced code blocks."""
    in_fence = False
    fence_marker = ""
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = _FENCE.match(line)
        if m:
            marker = m.group(1)[:3]
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif line.strip().startswith(fence_marker):
                in_fence = False
            continue
        if in_fence:
            continue
        for rx in (_MD_LINK, _HTML_LINK):
            for target in rx.findall(line):
                yield i, target


def check_docs(docs: list[str]) -> list[str]:
    """Return a list of human-readable errors; empty means all links/anchors resolve."""
    errors: list[str] = []
    slug_cache: dict[Path, set[str]] = {}

    def slugs_for(p: Path) -> set[str]:
        if p not in slug_cache:
            slug_cache[p] = slugs_of(p) if p.exists() else set()
        return slug_cache[p]

    for rel in docs:
        src = REPO_ROOT / rel
        if not src.exists():
            errors.append(f"{rel}: target document does not exist")
            continue
        for lineno, target in _iter_links(src):
            t = target.strip()
            if t.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            path_part, _, frag = t.partition("#")
            # Resolve the file part (repo-root-relative by convention).
            if path_part == "":
                target_doc = src  # pure in-page anchor
            else:
                clean = path_part.split("?")[0]
                if clean.startswith(IMAGE_PLACEHOLDER_PREFIX):
                    continue  # owner-filled placeholder, exempt from existence (INV-1)
                target_doc = (REPO_ROOT / clean).resolve()
                if not target_doc.exists():
                    errors.append(f"{rel}:{lineno}: broken relative link -> '{path_part}'")
                    continue
            # Resolve the fragment against the target document's heading slugs.
            if frag:
                if target_doc.suffix.lower() != ".md":
                    continue  # fragments into non-markdown are not slug-checkable
                if frag not in slugs_for(target_doc):
                    tgt = "(same file)" if path_part == "" else path_part
                    errors.append(f"{rel}:{lineno}: broken anchor '#{frag}' in {tgt}")
    return errors


def _selftest() -> int:
    """Negative control: a deliberately broken anchor MUST be reported (proves the check isn't a no-op)."""
    with tempfile.TemporaryDirectory() as d:
        bad = Path(d) / "bad.md"
        bad.write_text("# Real Heading\n\n[ok](#real-heading) [broken](#does-not-exist)\n", encoding="utf-8")
        # Point the resolver's slug/existence machinery at this file directly.
        errs = []
        for lineno, target in _iter_links(bad):
            _, _, frag = target.partition("#")
            if frag and frag not in slugs_of(bad):
                errs.append(f"bad.md:{lineno}: broken anchor '#{frag}'")
    if errs:
        print("selftest OK — broken anchor detected:", errs[0])
        return 0
    print("selftest FAIL — broken anchor was NOT detected (resolver is a no-op)", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    errors = check_docs(TARGET_DOCS)
    if errors:
        print(f"FAIL — {len(errors)} unresolved link(s)/anchor(s):", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        return 1
    print(f"OK — all relative links and anchors resolve in: {', '.join(TARGET_DOCS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
