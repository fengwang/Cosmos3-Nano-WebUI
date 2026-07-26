# AM-S6 Execution Contract

Date: 2026-07-26 · Session: AM-S6 (docs) · Risk: low + **mandatory adversarial honesty pass**.
Authority: `docs/session_6_contract.yaml`, `docs/project_contract.md`, `docs/prd.md` (dominant).

## Planned file changes
- `README.md` — honest all-modes status (Features table + Status & security 2×3 matrix), new
  "See it in action" section + nav anchor, license note (OpenMDW 1.1 base / 1.0 quantized), remove stale
  BF16/overlay/CPU-gate claims + drop the base checkpoint row.
- `docs/walkthrough.md` — **new**; UI-first per-mode example → expected output + `docs/images/…`
  placeholders + `<details>` API pointers.
- `docs/model_setup.md` — reconcile the base license to OpenMDW 1.1 (§1 table + §2), stated once.
- `docs/evidence_map.md` — AM-S6 audit row; E-14 resolved (OpenMDW 1.1); dated owner **video amendment**.
- `docs/risk_register.md` — close R-06 / R-09 / R-13 (AM-S6).
- `docs/eval_seed_cases.md` — mark the 3 EV-AM-* seeds exercised + AM-S6 harvest.
- `docs/handoff.md` — rewrite for AM-S6.
- `docs/session_6/**` — this pack (+ `check_links.py`, `sharded_review.md`, `adversarial_verification.md`).

## Allowed blast radius
Exactly `docs/session_6_contract.yaml → blast_radius.allowed_files`. **Forbidden:** any `api/**`,
`webui/**`, `deploy/**`, `Makefile`, `.env.example`, `schemas/openapi.json`, `docs/images/**` (binaries),
`docs/archive/**`, model/checkpoint/media files. Stop if an edit would fall outside this set.

## First test to write
`docs/session_6/check_links.py` (Task 1) — the relative-link + GitHub-anchor resolver, with a `--selftest`
negative control that a deliberately broken link exits non-zero. Written **before** the doc edits (it must
go RED while `docs/walkthrough.md` is absent, GREEN after).

## Checks after each task
- After **license** (Task 2): `rg -n "OpenMDW|openmdw|\bother\b" docs/model_setup.md`.
- After **README** (Task 3): `rg -n "GPU-verified" README.md`; `rg -n "up-fp8-reasoning|adds the BF16
  base|reasoning and action also use the BF16 base|only \*\*text" README.md` (→ empty);
  `rg -n "^## See it in action" README.md`.
- After **walkthrough** (Task 4): `rg -n "docs/images/" docs/walkthrough.md`;
  `git status --porcelain docs/images` (empty); `uv run python docs/session_6/check_links.py` (GREEN).
- Full (Task 6): all four contract `deterministic_checks` + the resolver.

## Review axes to run at the end
Sharded review (read-only): correctness, readability, security, tests, architecture, performance — but
for a docs session the load-bearing axes are **correctness (= claim ↔ evidence fidelity)**,
**architecture (= INV/blast-radius adherence)**, and **readability (ADHD posture)**.

## Adversarial verifier brief
Fresh context; does not see this conversation. Sees only the session contract, the diff, and the
evidence. Job: **falsify** `GATE-AM-S6-DOCS`. Specifically hunt the contract's adversarial cases:
1. A mode called "GPU-verified" whose owner gate was FAIL/unrecorded (INV-6) — incl. the **video
   amendment**: is the dated owner attestation actually recorded, and is the claim scoped to exactly what
   the owner said (t2v/i2v/t2v_audio × FP8+NVFP4)?
2. An NVFP4-format limitation omitted, implying more than passed (INV-7).
3. A walkthrough "expected output" for a mode/format that never ran (R-13).
4. A committed image binary instead of a placeholder (INV-1).
5. The BF16 license stated two ways across README ↔ model_setup (R-09).
6. A dropped/softened caveat (guardrails-off, no-auth, one-stack-at-a-time) while adding upbeat examples.
Output: disproven/unsupported claims, strongest counterexample, PASS/FAIL.

## Concrete done condition (`GATE-AM-S6-DOCS`)
All true: README has a "See it in action" section linking `docs/walkthrough.md`; the walkthrough has a
per-mode example input → expected output + `docs/images/…` placeholders with **no committed binary**; the
README "GPU-verified" set is a **subset** of the owner-passed set (t2i/t2v/i2v/t2v_audio/Reasoning/Action
× FP8+NVFP4, all owner PASS incl. the recorded 2026-07-26 video amendment); the BF16 license is reconciled
to OpenMDW 1.1 and stated once; **every internal link resolves** (`check_links.py` exit 0, negative
control proven); and the adversarial honesty pass returns **PASS** (no surviving over-claim or lost caveat).
