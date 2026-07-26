# AM-S6 Proposal — README "See it in action" + `docs/walkthrough.md`

Date: 2026-07-26 · Session: AM-S6 · Source: `docs/session_6/brainstorming.md` (owner-approved).

## Motivation

Phase-5 (`AM`) made all three modes real: AM-S2..AM-S5 GPU-verified Studio, Reasoning, and Action
on **both FP8 and NVFP4** off the quantized-only checkpoint (zero BF16), each with the owner's manual
quality PASS. The user-facing docs still describe the pre-phase world — "only text→image is verified;
reasoning/action are CPU-tested behind a GPU gate; reasoning+action add the BF16 base via
`make up-fp8-reasoning`" — which is now false and, on the promotion side, the exact **over-claim**
hazard the phase-3/4 reviews caught (R-06). AM-S6 makes the docs teach each mode by example, honestly,
and reconciles the one outstanding factual conflict (the BF16-base license, E-14).

## Specific changes agreed

1. Add a lean README **"See it in action"** section (per-mode example input → what to expect, prose),
   linking a new `docs/walkthrough.md`; add it to the Jump-to nav. No inlined screenshots (FR-9).
2. Create **`docs/walkthrough.md`** — UI-first, ADHD posture: shared *Setup once* + per-mode
   (steps → expected output → `docs/images/<mode>-<example>.png` placeholder → `<details>` API pointer).
   Studio t2i fully worked; compact video block; Reasoning; Action (FD worked + policy/ID one-liners).
3. Update the README **honest status** to the final matrix: Studio (t2i/t2v/i2v/t2v_audio), Reasoning,
   and Action all **GPU-verified on FP8 + NVFP4** (owner PASS). Includes the **owner-authorized video
   amendment** (2026-07-26). Remove obsolete "video smoke ≠ verified" caveats and the stale BF16/overlay
   references. Reflect zero-BF16 onboarding.
4. Reconcile the **BF16-base license** (E-14) to **OpenMDW 1.1** in `docs/model_setup.md` and the README
   Licensing note, stated once and consistently; quantized checkpoints stay OpenMDW 1.0.
5. **Verify**: every internal link/anchor in the edited docs resolves; the adversarial honesty pass finds
   no surviving over-claim or lost caveat. Close R-06/R-09/R-13 and the AM-S6 rows of evidence/risk/eval.

## Capabilities (contract between proposal and specifications)

Each capability gets a spec file under `docs/session_6/specs/`.

### New capabilities
- **`readme-see-it-in-action`** — the README "See it in action" section **and** the honest per-mode ×
  per-format verification status (Features table + Status & security matrix). Backed by
  `EV-AM-README-VERIFIED-SUBSET`.
- **`walkthrough-per-mode`** — `docs/walkthrough.md`: per-mode example input → expected output, UI-first
  steps, `docs/images/…` placeholders, no committed binary. Backed by `EV-AM-WALKTHROUGH-STRUCTURE`.

### Modified capabilities
- **`docs-links-and-license`** — internal-link/anchor integrity across the edited docs **and** the
  single, consistent BF16-base license statement (E-14 → OpenMDW 1.1) in `docs/model_setup.md` +
  README. Backed by `EV-AM-DOCS-LINKS-RESOLVE`.

## Impact

- **Docs:** `README.md`, `docs/walkthrough.md` (new), `docs/model_setup.md`, `docs/evidence_map.md`,
  `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/handoff.md`, `docs/session_6/**`.
- **Code / APIs / deploy:** none (out of scope; INV-8 untouched, no `schemas/openapi.json` change).
- **External:** the walkthrough references `docs/images/*` paths the **owner** populates later (INV-1);
  no image binary is committed by this session.
- **Honesty surface:** the video amendment moves 3 modes × 2 formats from "smoke-only" to "verified" on
  the owner's recorded attestation — the single highest-scrutiny item for the adversarial pass.
