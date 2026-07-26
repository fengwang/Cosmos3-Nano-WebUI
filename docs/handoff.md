# Session Handoff

## State Snapshot
- **Session: AM-S6** — README "See it in action" + `docs/walkthrough.md`; honest per-mode status; BF16-base
  license reconciliation. Risk low (docs) + **mandatory adversarial honesty pass**.
- **Branch:** `fea/eanble-reasoning-action-phase-5-session-6`.
- **Last commit at start:** `5a626e7` (AM-S5). This session's work is **uncommitted** (owner reviews/commits,
  per the prior-session pattern).
- **Current status: `GATE-AM-S6-DOCS` PASSES.** README carries a "See it in action" section linking
  `docs/walkthrough.md`; the walkthrough teaches every mode by example with 8 owner-fillable
  `docs/images/…` placeholders and **no committed binary**; the README "GPU-verified" set is a subset of
  the owner-passed set (INV-6); the BF16-base license (E-14) is reconciled to **OpenMDW 1.1** and stated
  once; every internal link resolves; sharded review + adversarial honesty pass both **PASS**
  (`docs/session_6/`). **Phase-5 (`AM`) documentation complete.**
- **Changed files (this session, all within the AM-S6 blast radius):**
  - `README.md` — honest all-modes status (Features table + Status & security 2×3 matrix), new
    "See it in action" section + Jump-to anchor, license note (OpenMDW 1.1 base / 1.0 quantized), removed
    the stale BF16/overlay/CPU-gate claims, dropped the legacy base row from the checkpoint table.
  - `docs/walkthrough.md` (**new**) — UI-first per-mode example → expected output + `docs/images/…` placeholders.
  - `docs/model_setup.md` — base license → OpenMDW 1.1 (§1 note ¹ + §2); §6 video row + §8 updated to all-modes.
  - `docs/evidence_map.md` — E-14 resolved; AM-S6 execution audit + the owner video amendment.
  - `docs/risk_register.md` — R-06 / R-09 / R-13 closed (AM-S6).
  - `docs/eval_seed_cases.md` — 3 EV-AM-* seeds recorded satisfied + AM-S6 harvest.
  - `docs/handoff.md` (this file); `docs/session_6/**` (refining pack, `check_links.py`, `.gitignore`,
    `sharded_review.md`, `adversarial_verification.md`, `failure_arbiter.md`, `evidence/P1-owner-video-runs.md`).
- **Checks run:** the 4 contract deterministic checks — `rg "GPU-verified" README.md`,
  `rg "docs/images/" docs/walkthrough.md`, `git status --porcelain docs/images` (empty),
  `docs/session_6/check_links.py` (exit 0) + its `--selftest` negative control (catches a broken anchor);
  blast-radius sweep (no forbidden file changed); sharded review (0 Critical/High); adversarial honesty pass
  (**PASS** after one re-verification).
- **Checks NOT run:** no CPU/GPU test suite (docs-only, out of scope); **no agent-captured (instrumented)
  video GPU probe** — the video-mode evidence is an owner-operated recorded run (`P1-owner-video-runs.md`),
  a weaker-but-disclosed tier (see residual risks).

## Per-mode × per-format verification matrix (final)

| Mode | FP8 | NVFP4 |
|---|---|---|
| **Studio — t2i** | GPU-verified (`GPU-S3`) | GPU-verified (`GPU-S3`) |
| **Studio — t2v / i2v / t2v_audio** | GPU-verified · owner PASS (AM-S6, 2026-07-26) | GPU-verified · owner PASS (AM-S6, 2026-07-26) |
| **Reasoning** | GPU-verified · owner PASS (AM-S2) | GPU-verified · owner PASS (AM-S5) |
| **Action** (FD / ID / policy) | GPU-verified · owner PASS (AM-S3) | GPU-verified · owner PASS (AM-S5) |

**Handoff confirmation (contract requirement):** the README verified set **matches** this owner-passed
matrix (subset check + adversarial pass), and **no caveat was dropped** — guardrails-off, no-auth,
loopback-only, and one-stack-at-a-time are all preserved; the only removed caveat ("720p smoke ≠ verified")
is correctly obsolete now that the owner has verified the video modes.

## Narrative Context
AM-S6 is the phase's last session: it makes the user-facing docs teach each mode honestly now that
AM-S2..S5 GPU-verified all of them. The README got a lean "See it in action" section (per-mode example →
what to expect, no inlined screenshots, FR-9) linking a new UI-first `docs/walkthrough.md`; the per-mode
status was flipped to the all-green matrix; the BF16-base license was reconciled against the HF model card
to **OpenMDW 1.1** (both the docs' bare `other` and the owner's `openmdw-1.0` recollection were wrong).
Mid-session the owner attested the **video sub-modes** work on both formats — an over-claim hazard the
mandatory honesty pass caught (no recorded run), which was resolved by the owner's decision to record the
actual runs (`P1-owner-video-runs.md`, owner-operated tier disclosed) so both INV-6 limbs are on record.

## Decision Log
| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| BF16-base license (E-14) | **OpenMDW 1.1** (HF `license_name`) | bare `other`; owner's `openmdw-1.0` | authoritative HF model card is the tie-breaker; 3 fetches agree | R-09; evidence_map E-14 |
| Video modes → verified | **Record owner run + keep "GPU-verified"** | silently keep (dishonest); downgrade (defies owner); INV-6 exception | owner is the quality-gate authority (Decision 6) + a recorded run satisfies INV-6 (i) | failure_arbiter.md; INV-6 |
| Base row in README table | **Dropped** (kept in model_setup) | keep it relabeled | base is legacy/dormant, not a default dependency; leaner + honest | design.md D4 |
| Status matrix location | **Status & security only** | matrix in both places | avoid a second copy that a future edit can desync (R-09) | design.md D3 |
| Walkthrough video expected-output | **Owner-attested level, drafted prompts** | fabricate specific outputs | R-13: draft inputs OK, never draft outputs | design.md D1; R-13 |

## Next Priority Queue
1. **Owner fills the 8 screenshots** into `docs/images/` (paths below), then optionally reviews the rendered
   README + walkthrough.
2. **(Optional hardening)** capture an instrumented video GPU probe (bytes/dimensions) to upgrade the video
   evidence from the owner-operated tier to the instrumented tier of the t2i/reasoning/action P-files.
3. **Archive the phase-5 (`AM`) pack** per the project's archival convention (this session is the finish
   line); the `AM-S1..S6` docs move under `docs/archive/phase-5/` like the prior phases.

### `docs/images/…` placeholder paths the owner will populate (in walkthrough order)
1. `docs/images/studio-t2i.png`
2. `docs/images/studio-t2v.png`
3. `docs/images/studio-i2v.png`
4. `docs/images/studio-t2v_audio.png`
5. `docs/images/reasoning-chat.png`
6. `docs/images/action-forward_dynamics.png`
7. `docs/images/action-policy.png`
8. `docs/images/action-inverse_dynamics.png`

## Warnings And Gotchas
- **Residual owner-decided limitation (recorded, not gate-failing):** the video-mode "GPU-verified" claim
  rests on an **owner-operated recorded run** (`docs/session_6/evidence/P1-owner-video-runs.md`) + owner
  quality PASS — a weaker evidence tier than the instrumented t2i/reasoning/action probes. It is disclosed
  three times (P1, evidence_map, model_setup), authorized by the owner (the quality-gate authority), and
  scoped strictly to t2v/i2v/t2v_audio × FP8+NVFP4. An agent-captured probe would upgrade the tier later.
- **GitHub blob-view relative links:** the repo convention writes root-relative links inside `docs/*.md`
  (e.g. `docs/images/…`, matching `docs/model_setup.md`'s existing `docs/archive/…`); `check_links.py`
  resolves them repo-root-relative (as the contract phrases them). Note that GitHub's *blob* view resolves
  a relative link against the file's own directory, so from `docs/walkthrough.md` a `docs/images/…` link
  renders as `docs/docs/images/…`. This is a **pre-existing repo-wide convention**, not introduced here; a
  future cleanup could switch `docs/*.md` internal links to file-relative. Out of scope for AM-S6.
- **Known failing tests:** none (no test suite touched; docs-only).
- **Files future sessions must not casually edit:** the frozen-verified serving stacks
  (`deploy/docker-compose.{fp8,nvfp4}.yml`, the `vllm-reasoner*` images/patches); `schemas/openapi.json`
  (INV-8); the proven `vllm-omni` image + `t2i` path (INV-2); `docs/archive/**`.

## Eval Seeds
- **Missed-then-caught check:** `EV-AM-DOCS-VERIFIED-NEEDS-RECORDED-RUN` — the adversarial honesty pass
  caught a video "GPU-verified" over-claim (verbal owner PASS, no recorded run) that the sharded review
  waved through; INV-6 needs both limbs. Recorded in `docs/eval_seed_cases.md` (AM-S6 harvest).
- **Process seed:** `EV-AM-ADVERSARIAL-EARNS-KEEP-ON-DOCS` — run the adversarial pass even on a low-risk
  docs session when the deliverable is to *promote* claims.
- **Honesty seed:** `EV-AM-DISCLOSE-EVIDENCE-TIER` — disclose a weaker evidence tier in the doc; don't let
  the reader assume uniform rigor.
- **New check added:** `docs/session_6/check_links.py` (relative-link + GitHub-anchor resolver with a real
  negative control) — reusable for future docs sessions.
