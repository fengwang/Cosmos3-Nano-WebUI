# Eval Seed - MIG-S8 A Silently-Broken Scan Reports "Clean"

Session: MIG-S8
Caught by: sharded review (tests axis) at the release gate
Severity caught: Medium→High (a load-bearing scrub gate that could not fail)

## Prompt Seed

A manual scrub gate ("check #15") was recorded in prose as "clean". Its absolute-path sub-scan
used `rg` with a **negative look-around** (`(?!…)`) — unsupported by `rg`'s Rust regex engine —
run with `2>/dev/null`. `rg` exited 2 (bad pattern); `2>/dev/null` swallowed the error; the
loop produced no output; the gate reported "clean". A broken scan and a truly clean scan were
**indistinguishable** because no command + exit code was recorded. The same failure mode
applies to any check whose "pass" is "no output" and whose errors are discarded.

A twin recurrence in the same session: writing a *real* private path (`/data/home_<user>`) as a
**negative example** inside the review/arbiter doc tripped the committed scanner — documentation
of a finding must be redacted just like the code, or it becomes the leak. See
[[mig_s3_docs_private_scrub_recurrence]].

## Inputs

- A shell scan whose "clean" signal is empty stdout, with `2>/dev/null`
- A regex engine that rejects some constructs (look-around in RE2/Rust regex)
- A results record that stores a prose verdict, not the command + exit code

## Expected Verifier Behavior

1. Treat "empty output = clean" as unproven unless the **exit code** is recorded and is the
   expected one (`rg`: 1 = clean/no-match, 0 = match, 2 = error). Never accept `2>/dev/null` on
   a gate scan.
2. Re-run every load-bearing scan with a **known counterexample** to prove it can fail
   (RED-before-GREEN), and record the exact command + exit code, matching the format of the
   other checks.
3. Classify a scan that cannot fail as **TEST_BUG**; fix the scan, do not delete the finding.
4. When a review/arbiter doc must reference a private path, redact it (e.g. `/workspace/…`,
   `/data/home_<user>`) so the doc does not itself carry the literal.

## Regression Command Shape

```bash
# a gate scan must record its exit code and never discard stderr:
rg -n "<pattern>" <files>; echo "exit=$?"    # 1 = clean, 0 = match, 2 = BROKEN pattern
uv run python tests/test_private_ref_scan.py # committed scanner is the durable gate (exit-coded)
```

## Expected Result

A broken/invalid scan is detected (exit 2 ≠ expected 1) instead of masquerading as clean; each
gate records command + exit code; a planted counterexample makes the scan fail.

## Promotion Target

Candidate REVIEW.md / project-contract rule: a release-gate scan is only evidence if it records
the exact command **and** its exit code, is proven to fail on a counterexample, and never runs
under `2>/dev/null`. Prefer the committed exit-coded scanner over ad-hoc shell `rg` for gating.
