# AM-S6 Design — README "See it in action" + `docs/walkthrough.md`

Date: 2026-07-26 · Session: AM-S6 · Inputs: `docs/session_6/{brainstorming,proposal}.md`.

## Context

Docs-only, low-risk, run last by design (project_contract §two-pass item 8, R-13). All three modes are
owner-PASSed on FP8 + NVFP4 (AM-S2..S5); the owner additionally attested the video sub-modes on
2026-07-26. The README is already an ADHD-optimized single file (LX-S2 output). The one factual conflict
is the BF16-base license (E-14), resolved against the authoritative HF source. The dominant risk is
honesty: promoting modes to "verified" is exactly where over-claims live (R-06).

## Goals / Non-Goals

**Goals.** (1) README "See it in action" per-mode, prose, linked. (2) `docs/walkthrough.md` UI-first,
per-mode example → expected output, owner-fillable `docs/images/…` placeholders, no binary. (3) README
per-mode status == the owner-passed matrix (INV-6); zero-BF16 onboarding. (4) E-14 license reconciled,
stated once (R-09). (5) All internal links resolve; honesty pass clean.

**Non-Goals.** Any code/config/deploy/webui edit; inlined screenshots (FR-9); committing images (INV-1);
fixing a product bug surfaced by an example (file it); re-verifying any mode (owner already did).

## Decisions

- **D1 — Report, don't re-derive.** Expected-output prose is copied from recorded runs
  (`docs/session_{2,3,4,5}/evidence/*`, `docs/model_setup.md` §6), never guessed (R-13). *Alt:* invent
  plausible outputs → rejected (R-13 breach).
- **D2 — Video via owner attestation, recorded as an amendment.** INV-6 needs (i) a recorded run +
  (ii) owner quality PASS. The owner supplied (ii) verbally and attests (i) on their hardware; captured
  as a dated attestation + amendment to the AM-S5 smoke-only matrix (same form as prior owner PASSes).
  *Alt:* refuse until a fresh GPU-probe is filed → rejected: GPU verification is the owner's gate
  (Decision 6), and the owner is the authority; *Alt:* silently flip status → rejected (R-06; no record).
- **D3 — Status in two places, matrix once.** Features table statuses updated in place; the 2×3
  per-mode × per-format matrix lives only in Status & security. *Alt:* matrix in both → duplication a
  future edit can desync (R-09/INV-6). 
- **D4 — Drop the base row from the README table.** Base is legacy/dormant, not a default dependency;
  the full 3-row licensed table stays in `docs/model_setup.md` (source of truth). *Alt:* keep it →
  clutter + implies it is required.
- **D5 — License stated as "OpenMDW 1.1", HF-tag nuance noted once.** The bare HF `license: other` is
  kept honest by naming `license_name: openmdw1.1-license` + link; avoids the misleading "other".
- **D6 — Walkthrough = Setup-once + per-mode, UI-first, API in `<details>`.** Matches how the owner
  captures screenshots and how the modes were blessed ("check every WebUI tab"); the exact curl bodies
  already live in `docs/session_3/action_demo_runbook.md`, so link/summarize, don't re-inline (FR-9).
- **D7 — ADHD posture preserved.** Keep the README's hook/TL;DR/mermaid/`<details>`/anchors; the new
  section + walkthrough are scannable, short-lined, fenced-command, anchored.

## Risks / Trade-offs

- **[R-06 over-claim / lost caveat]** → verified set asserted ⊆ owner-passed set by a deterministic
  README sweep + the mandatory adversarial honesty pass; guardrails-off / no-auth / one-stack-at-a-time
  caveats explicitly preserved.
- **[R-13 fiction]** → every expected-output line traces to a cited recorded run or the owner attestation;
  drafted *inputs* only where R-13 permits (video prompts), never drafted *outputs*.
- **[R-09 license drift]** → single source of truth in `model_setup.md`; README states it once and links;
  negative-control link check to prove the resolver catches a broken link.
- **[INV-1 binary]** → `git status --porcelain docs/images` must be empty; placeholders are markdown links.
- **[Video amendment scope creep]** → amendment strictly limited to the 3 video modes × 2 formats the
  owner named; nothing else in the AM-S5 matrix is re-touched.

## Migration Plan

Pure docs; no runtime migration. Order: (1) model_setup license → (2) README status + See-it-in-action →
(3) walkthrough → (4) evidence/risk/eval/handoff → (5) deterministic checks + link resolver → (6) sharded
review → (7) adversarial honesty pass → (8) fix High/Critical → (9) verify done. **Rollback** = `git
checkout` the docs (no deploy artifact). Commits only at a clean checkpoint if requested (prior-session
pattern: owner reviews/commits).

## Open Questions
None. E-14 resolved (OpenMDW 1.1); walkthrough video treatment = drafted prompts (owner chose (a)); the
two judgment calls = drop base row + matrix-once (owner approved).
