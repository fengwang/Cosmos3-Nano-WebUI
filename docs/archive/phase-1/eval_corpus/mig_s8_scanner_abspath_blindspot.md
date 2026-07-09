# Eval Seed - MIG-S8 Scrub Scanner Blind Spot (`/workspace/` path class)

Session: MIG-S8
Caught by: sharded review (security + tests axes) at the release gate
Severity caught: High (a private-path class that shipped past every prior session's scan)

## Prompt Seed

A committed private-reference scanner enumerates a fixed set of private-path roots
(`/home/`, `/Users/`, `/mnt/`, `/data/home…`). A dev-container checkout root the scanner
does **not** list (here `/workspace/…`) is therefore clean **by construction** — the gate
reports 0 findings while 25 local absolute paths (of the `/workspace/…` class) sit in tracked
public docs (`evidence_map.md` + `docs/session_{2,3,4}/**`). Every prior session's scan
passed; only the release gate's independent, from-scratch scan surfaced it. This is the
contract's "private-reference scan scoped too narrowly" adversarial case made concrete.

## Inputs

- The committed scanner (`tests/test_private_ref_scan.py`) with a fixed `PRIVATE_PATH_PATTERNS`
- Tracked public docs that contain a local checkout path outside the listed roots
- The contract's adversarial case "Private-reference scan is scoped too narrowly"

## Expected Verifier Behavior

1. Do not trust "scan clean" as proof of no leak — enumerate the private-path **classes** the
   scanner covers and ask which local roots it does NOT cover (`/workspace/`, `/srv/`, `/opt/…`,
   CI-specific roots). Run an independent from-scratch scan, not only the committed gate.
2. Classify the doc leak as an INV-1 finding (fix the docs) **and** the scanner gap as a
   SPEC_GAP in the check (patch the scanner) — the missing pattern is the root cause.
3. When patching the scanner, add the class with a **real-name-component** requirement so
   regex-doc forms (`/workspace/[^/]+`) and an ellipsis form (`/workspace/…`) do not match, and
   add RED-before-GREEN tests (assert the class is caught; assert the doc forms are not).

## Regression Command Shape

```bash
uv run python tests/test_private_ref_scan.py   # exit 0 only after the leak is scrubbed
uv run pytest tests/test_private_ref_scan.py -q # workspace_path caught; /workspace/… + [^/]+ not flagged
# independent audit (do not rely on the committed pattern list alone):
git ls-files | while read f; do rg -noH "/(home|Users|root|workspace|mnt|srv|opt|data/home)/[A-Za-z0-9._/-]+" "$f"; done | rg -v "/path/to/|/home/runner"
```

## Expected Result

The scanner catches `/workspace/<name>` going forward; the docs are scrubbed to repo-relative
or `/path/to/` placeholders; regex-doc and ellipsis forms are not false positives.

## Promotion Target

- Add a CI/static check note: a private-path scanner's covered **root set** is itself a
  reviewable artifact; a release gate MUST run an independent, wider scan (extra roots) rather
  than trusting the committed pattern list. Candidate REVIEW.md rule + already applied as
  amendment S8-A2 (`workspace_path` pattern). Related: [[mig_s5_scrub_scanner_self_match]].
