# Eval Seed - MIG-S5 Scrub Scanner Must Not Match Its Own Pattern Docs

Session: MIG-S5
Caught by: deterministic check (the committed scanner's own clean-tree test) during TDD
Severity caught: Medium (would-be false-positive CI block)

## Prompt Seed

A committed private-reference scanner that scans `docs/` will flag the
*documentation* of scrub patterns — its own and prior sessions' — as findings
unless designed against it (the `EV-MIG-SCRUB-COMMAND-SANITY` case). Concretely,
the first clean-tree run flagged 4 hits of the `/data/home` root pattern that were
actually `rg -e '...'` examples and regex fragments (like a `/data/home`-rooted
`[^/]+` alternation) inside `docs/session_3` / `docs/session_4` scrub docs — not
real leaked paths.

## Inputs

- The committed scanner (`tests/test_private_ref_scan.py`)
- The controlled surface it scans (`.github`, `api`, `webui`, `tests`, `schemas`, `docs`)
- Prior-session scrub docs that legitimately document private-reference patterns

## Expected Verifier Behavior

1. Classify a hit inside pattern documentation as **TEST_BUG**, not a product fix
   (per `docs/session_1/scrub_checklist.md` result table).
2. Resolve by making the check precise, not by deleting the finding: each
   private-path pattern requires a **real name component** after the root (so a bare
   root or a regex fragment does not match, exactly as `/home/` + `[` never matched);
   exclude the scanner file itself and the S1 checklist.
3. Build every secret fixture by string concatenation so no literal secret-shaped
   string is ever committed (even in test/doc files).

## Regression Command Shape

```bash
uv run python tests/test_private_ref_scan.py         # exit 0, "clean (0 findings)"
uv run pytest tests/test_private_ref_scan.py -q      # planted secret caught; placeholders + docs ignored
```

## Expected Result

Clean tree = 0 findings; a concatenation-built secret / a committed weight file is
caught; documented `/path/to/...` placeholders and prior pattern docs are not
flagged. A hit in pattern documentation ⇒ tighten the pattern or exclude the doc
(TEST_BUG); a hit in runtime/config/workflow ⇒ BUG/SPEC_GAP.

## Promotion Target

Keep the "real-name-component + exclude scanner/checklist + concat fixtures"
technique. Candidate REVIEW.md rule: a committed scrub scanner MUST be sanity-tested
against its own and prior sessions' pattern documentation before it gates CI.
