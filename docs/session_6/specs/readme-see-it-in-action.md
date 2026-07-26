# Spec — `readme-see-it-in-action`

Capability: the README "See it in action" section **and** the honest per-mode × per-format
verification status. Backed by `EV-AM-README-VERIFIED-SUBSET` (INV-6/INV-7, R-06).

## ADDED Requirements

### Requirement: README "See it in action" section
The README SHALL contain a `## See it in action` section, placed after `## Features`, that gives — in
prose, for each verified mode (Studio, Reasoning, Action) — a one-line example input and what to expect,
and links to `docs/walkthrough.md`. The section SHALL NOT inline screenshots (FR-9) and SHALL be added to
the "Jump to" navigation.

#### Scenario: Section present and links the walkthrough
- WHEN `rg -n "^## See it in action" README.md` runs
- THEN it matches exactly one heading, and within that section a relative link to `docs/walkthrough.md`
  resolves to an existing file.

#### Scenario: Listed in the Jump-to nav
- WHEN the README "Jump to:" line is read
- THEN it contains an anchor link to `#see-it-in-action`.

#### Scenario: No inlined screenshot (FR-9)
- WHEN the "See it in action" section body is read
- THEN it contains no image embed (`![...](...)`); visual steps live only in `docs/walkthrough.md`.

### Requirement: Honest per-mode verification status
The README Features table and Status & security section SHALL state a mode/format as "GPU-verified" only
if it has a recorded run AND the owner's recorded quality PASS (INV-6); the "GPU-verified" set SHALL be a
subset of the owner-passed set (per format, per mode), and any mode/format that did not pass SHALL be
documented honestly, not hidden or over-claimed (INV-7). Zero-BF16 onboarding SHALL be reflected.

#### Scenario: Verified set is a subset of the owner-passed set
- WHEN every "GPU-verified" claim in `README.md` is compared to the owner-passed set in
  `docs/evidence_map.md` / `docs/handoff.md` (t2i, t2v, i2v, t2v_audio, Reasoning, Action — each on FP8
  and NVFP4, owner PASS)
- THEN every README "GPU-verified" claim is present in the owner-passed set (no claim exceeds it).

#### Scenario: A per-mode × per-format matrix exists in Status & security
- WHEN the "Status & security" section is read
- THEN it contains a matrix mapping each mode to FP8 and NVFP4 status, with Reasoning and Action marked
  owner PASS, consistent with the AM-S5 handoff matrix + the 2026-07-26 video amendment.

#### Scenario: Stale pre-phase claims are gone
- WHEN `rg -n "only \*\*text|other modes are (implemented and CPU-tested|not yet)|up-fp8-reasoning|adds the BF16 base|reasoning and action also use the BF16 base" README.md` runs
- THEN it returns no matches (every stale "only t2i / CPU-tested gate / BF16 overlay" claim is removed).

#### Scenario: Video modes not over-claimed beyond the owner attestation
- WHEN the README marks t2v/i2v/t2v_audio "GPU-verified"
- THEN `docs/evidence_map.md` carries the dated owner attestation (Feng, 2026-07-26) for those modes on
  both formats, and no obsolete "720p smoke does not promote video to verified" caveat remains to
  contradict it.
