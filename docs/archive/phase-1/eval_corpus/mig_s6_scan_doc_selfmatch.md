# Eval Seed - MIG-S6 A Scan-Finding Write-up Re-Trips the Scanner

Session: MIG-S6
Caught by: sharded review (tests axis), reproduced by the adversarial verifier
Severity caught: Critical (committed private-reference gate went red after being green)

## Prompt Seed

A `failure_arbiter.md` (or any doc) that **quotes the raw literal** a content scanner
flagged will itself be scanned and re-flagged, because the scanner's `SCAN_ROOTS`
include `docs/`. Here FA-1 fixed a `mnt_path` (`/mnt/<name>`) hit in a spec and
`.env.example`, then the write-up documenting FA-1 pasted the same literal five times —
so `tests/test_private_ref_scan.py` went from clean back to 5 findings, all inside
`docs/session_6/failure_arbiter.md`. The doc's own "post-fix: scan clean" line was then
false against the committed tree.

## Inputs

- `tests/test_private_ref_scan.py` (`SCAN_ROOTS` includes `docs`; `mnt_path` rule
  `/mnt/[A-Za-z0-9._-]+`; only `/path/to/` is a sanctioned placeholder)
- Any session doc that quotes a flagged finding verbatim

## Expected Verifier Behavior

1. After writing a doc that reports a scan finding, RE-RUN the scanner over the whole
   tree (not just the originally-offending file).
2. Observe the doc itself is now flagged.
3. Neutralize the quoted literal in a non-matchable form (e.g. `/mnt/‹dir›` with
   non-ASCII guillemets, or `/mnt/<name>` with angle brackets, or describe it) — do NOT
   modify the out-of-blast-radius scanner.
4. Re-run → clean.

## Regression Command Shape

```bash
uv run python tests/test_private_ref_scan.py   # must be clean AFTER writing every doc,
                                                # including the failure-arbiter write-up
```

## Expected Result

The full-tree scan is clean, and no session doc contains a scanner-matchable private-path
/ secret literal — including docs that report scan findings.

## Promotion Target

- REVIEW.md / project contract template rule: "a scan-finding write-up is itself
  scanned; quote flagged patterns in a non-matchable form, and re-run the scanner over
  the whole tree after authoring docs, not only after fixing source."
- Also a standing sharded-review (tests axis) check: confirm the committed scan is green
  on the final tree, not just at the moment the source fix landed.
