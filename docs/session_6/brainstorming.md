# AM-S6 Brainstorming — README "See it in action" + `docs/walkthrough.md`

Date: 2026-07-26 · Session: AM-S6 · Risk: low (docs) + **mandatory adversarial honesty pass**
Contract: `docs/session_6_contract.yaml` · PRD Decision 8 / FR-7 / FR-9 · project_contract §two-pass item 8, R-06/R-09/R-13, INV-1/6/7.

## 1. Context (explored)

- **Phase state:** AM-S2..AM-S5 GPU-verified all three modes (Studio, Reasoning, Action)
  on **both FP8 and NVFP4** off the quantized-only checkpoint (zero BF16), owner PASS
  (Feng, 2026-07-25/26). This session is the *last* one — it **reports** those outcomes,
  it does not create them (except the owner-authorized video amendment below).
- **Docs only.** Blast radius = `README.md`, `docs/walkthrough.md` (new),
  `docs/model_setup.md`, `docs/evidence_map.md`, `docs/risk_register.md`,
  `docs/eval_seed_cases.md`, `docs/handoff.md`, `docs/session_6/**`. No code/config/deploy/webui.
- **ADHD posture (phase-4 / LX-S2).** README stays one lean file; heavy visual walkthrough
  linked out (FR-9). Checkable properties (from archived `EV-LX-README-STRUCTURE`): hook before
  deep install; TL;DR near top; ≥1 `mermaid` fence (≤7 nodes); `<details>` progressive disclosure
  (blank line after `</summary>`); in-page anchors/TOC; fenced commands with language IDs;
  scannable "properties not prose".
- **WebUI facts (read-only) for UI-first steps:** primary nav = **Studio** (`/studio`),
  **Reasoning** (`/chat`), **Action** (`/action`), History. Action tab has an **Embodiment**
  select (`agibotworld (29-D, 3D)` / `av (9-D, 2D plots)`), a **Mode** select
  (Policy / Forward dynamics; Inverse dynamics for `av`), a **Run demo** button, and a result
  region with a 3D robot viewer + 2D trajectory plots + inspection panel.

## 2. Confirmed intent (interview outcome)

- **Outcome:** lean README "See it in action" (per-mode example input → what to expect, prose)
  linking a new UI-first `docs/walkthrough.md` with owner-fillable `docs/images/<mode>-<example>.png`
  placeholders; README per-mode status flipped to the now-all-green matrix; BF16-base license
  reconciled to **OpenMDW 1.1**.
- **Success:** `GATE-AM-S6-DOCS` — see it in action links the walkthrough; per-mode
  example→expected-output + placeholders, **no committed binary**; README "GPU-verified" set ⊆
  owner-passed set (INV-6); links resolve; adversarial honesty pass finds no surviving over-claim.
- **Out of scope:** fixing a product bug a doc example reveals (file it); adding image binaries;
  changing any AM-S2..S5 result.

### 2a. Owner-authorized amendment — video modes now verified (2026-07-26)

During refinement the owner (Feng) attested: **Text→Video, Image→Video, and Text→Video+Audio were
tested on both FP8 and NVFP4, all high quality.** The owner is the quality-gate authority
(PRD Decision 6), so this is an owner quality **PASS**. Because the AM-S5 recorded matrix listed
video as *smoke-only*, it is logged as an **owner-authorized amendment** (dated attestation, same
form as AM-S2/S3/S5) in `docs/evidence_map.md` / `docs/handoff.md` / `docs/eval_seed_cases.md`.
Net: **all four Studio generation modes (t2i/t2v/i2v/t2v_audio) → GPU-verified on both formats**;
the obsolete "720p smoke does not promote video to verified" caveats are removed (they would now
contradict the status).

## 3. Design exploration (approaches → chosen)

**Q1 — honest status rendering.**
- (A) **[chosen]** update the Features table status column in place **+** add the 2×3 per-mode ×
  per-format matrix in **Status & security** only. Trade-off: leanest honest update; no duplication.
- (B) matrix in both Features and Status & security → redundant, more to keep consistent (R-09 risk).
- (C) bigger restructure → violates "keep the README lean / minimal-diff" and FR-9.

**Q2 — walkthrough structure.**
- (A) **[chosen]** shared **Setup once** preamble + per-mode section (what you'll see → numbered
  UI steps → expected output → image placeholder → `<details>` reproduce-via-API). DRY, scannable.
- (B) fully self-contained per-mode (repeat setup) → duplication, longer, less ADHD-friendly.

**Q3 — base checkpoint row in the README table.**
- (A) **[chosen]** drop it from the README table (base is legacy/dormant, not a default dependency);
  keep the full 3-row table with the reconciled license in `docs/model_setup.md` (source of truth).
  Leaner + honest; contract says "state once, consistently, in model_setup (and the README table if
  present)" — README table need not carry the base.
- (B) keep it, relabeled "legacy/dormant only". More clutter; risks the reader treating it as required.

**Q4 — walkthrough Studio video treatment.**
- (A) **[chosen]** t2i is the one *fully*-worked Studio example (grounded in the recorded run);
  video modes get a compact block with **drafted** representative prompts and expected-output at the
  owner-attested level ("~1280×720, ~49 frames; t2v_audio adds a soundtrack") + placeholders. R-13:
  example inputs may be drafted; expected-output stays at what the owner approved.
- (B) owner hand-feeds exact video prompts → unnecessary for a docs pass; owner fills real screenshots.

## 4. Validated design

### A. README "See it in action" (new `##` section after **Features**; added to the Jump-to nav)
Concise prose, no inlined screenshots (FR-9): one line per mode (Studio incl. video / Reasoning /
Action) → example input → what to expect → link to `docs/walkthrough.md`.

### B. Honest status (two edits)
1. **Features table** statuses → truth: t2i/t2v/i2v/t2v_audio **GPU-verified** (FP8+NVFP4);
   Reasoning **GPU-verified** (FP8+NVFP4); Action FD/ID/policy **GPU-verified** (FP8+NVFP4).
2. **Status & security** → replace the stale "only t2i" bullets with the 2×3 matrix (all
   GPU-verified · owner PASS). Remove the obsolete video-smoke caveat.
   Fix the 3 stale spots: top **NOTE** box; Quickstart "other modes not yet"; the `<details>`
   "adds the BF16 base: `make up-fp8-reasoning`" → all modes on a plain `make up-fp8`/`up-nvfp4`,
   zero-BF16.

### C. License reconciliation (E-14 → **OpenMDW 1.1** for the base)
Authoritative HF source (3 independent fetches — rendered page, API JSON, raw model-card
frontmatter): `nvidia/Cosmos3-Nano` = `license: other` + `license_name: openmdw1.1-license` +
`license_link: https://openmdw.ai/license/1-1/` → real license **OpenMDW 1.1** (bare `other` is only
because OpenMDW is not in HF's SPDX picklist). Quantized `wfen/*` checkpoints confirmed **OpenMDW 1.0**.
Edit `docs/model_setup.md` §1 table + §2 and the README Licensing note; state once, consistently.

### D. `docs/walkthrough.md` (new, UI-first, ADHD posture)
TL;DR + "Jump to" → **Setup once** (bring up a stack, `make health`, open `:3000`) → per-mode:
- **Studio** — t2i fully worked ("a red apple on a wooden table, studio photo", 480×480 → clean
  studio-style image); compact video block (t2v/i2v/t2v_audio, drafted prompts, attested output).
- **Reasoning** — a recorded prompt/answer (e.g. "List three primary colors" → `Red, Blue, Yellow`,
  or the AM-S4 gripper-friction reasoning) → coherent streamed answer.
- **Action** — forward_dynamics fully worked (Embodiment `agibotworld` + Mode `Forward dynamics`
  → **Run demo** → ~620 KB MP4 rollout + 3D robot view); one-liners for policy + inverse_dynamics.
Each step: expected output (from recorded runs) + `![…](docs/images/<mode>-<example>.png)` +
`<details>` "reproduce via API" → `docs/session_3/action_demo_runbook.md` / `docs/model_setup.md`.

### Image placeholders (walkthrough order, all under `docs/images/`, `<mode>-<example>.png`)
1. `docs/images/studio-t2i.png`
2. `docs/images/studio-t2v.png`
3. `docs/images/studio-i2v.png`
4. `docs/images/studio-t2v_audio.png`
5. `docs/images/reasoning-chat.png`
6. `docs/images/action-forward_dynamics.png`
7. `docs/images/action-policy.png`
8. `docs/images/action-inverse_dynamics.png`

## 5. Open items
None — intent + design confirmed (owner explicit yes, 2026-07-26), incl. the video amendment.
