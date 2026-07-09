# Session 8 Design - Release Gate, Evidence Review, and Handoff

Session: MIG-S8
Risk: high · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S8-BETA`
Derived from: `proposal.md` (capabilities) + `brainstorming.md` (approved design)

## Context

`MIG-S1`..`MIG-S7` produced a curated public repo: pinned public vLLM-Omni fork
(`697035018b70…`), verified public HF checkpoints (FP8 `4e181f99…`, NVFP4 `b5c9332e…`,
license `openmdw-1.0`; base `nvidia/Cosmos3-Nano`, `other`), CPU-only CI, local-build
Docker/Compose, an evidence-qualified README, and community-health files — with the X-1
auth mismatch fixed. Everything runtime is **GPU-unverified** (the S8 manual gate) and
drift **D1** is open. Stakeholders: (a) the owner, who records the public-beta GO/NO-GO;
(b) later sessions, which inherit the deferred GPU manual gates and the at-publish tasks.
Constraints: public-verifiable evidence only (`INV-1`, evidence-map rules), no runtime
source edit (docs-only blast radius), no lowering acceptance bars without owner decision,
no Docker publishing, no private citations.

## Goals / Non-Goals

**Goals**
- A reproducible CPU deterministic-check log; every PRD MUST mapped to a gate, public
  evidence, and a verdict; every major public claim tied to a public evidence row.
- The GPU surface honestly recorded as a beta-limited manual gate (`INV-8`), with the
  commands/pins a later run must use.
- A risk register with **no unowned release-blocking risk**, and tracking docs consistent
  with README/Docker/setup.
- A recommended `GATE-MIG-S8-BETA` verdict + rationale for owner ratification, plus a
  handoff and eval seeds.

**Non-Goals**
- No GPU inference, no checkpoint download, no vLLM-Omni image build, no D1 resolution.
- No runtime source / schema / dependency-pin / Docker-publishing / fork-source edit.
- No production-readiness claim; no lowering of acceptance bars without an owner decision.
- No push / tag / release (owner mechanics after ratification).

## Decisions

- **D-1 — CPU checks are the evidence of record; run them live.** Re-run the 7 contract
  checks via `rtk` and capture raw output into `outputs/deterministic_checks.md`. Prior
  sessions' green results are cited but re-verified here (S8 is the release gate). Ref:
  session contract `deterministic_checks`, acceptance criterion "checks not run recorded".
- **D-2 — Acceptance matrix keyed by every PRD MUST.** One row per MUST (FR-1..FR-12 where
  MUST; NFR-1..NFR-6) → owning gate → public evidence pointer → verdict
  `{PASS | BETA-LIMITED | NO-GO}`. *Alternative:* gate-keyed only (rejected — the
  acceptance criterion is explicit about *every PRD MUST*; the gate view is the
  complementary `gate_record.md`). Ref: session contract acceptance_criteria[0].
- **D-3 — GPU surface = BETA-LIMITED, not PASS and not NO-GO.** Owner decision 1 + `INV-8`:
  a beta may ship with manual GPU gates when unverified surfaces are marked. Each
  `EV-MIG-GPU-*` row records NOT-YET-RUN + the exact deferred command + the pin/revisions a
  later run must match; the README already marks every mode GPU-unverified (S7). Drift D1 is
  an owner-visible beta limitation, not silently PASS. *Alternative:* block the beta on GPU
  (rejected — contradicts owner decision + the contract's manual-gate design). Ref:
  `INV-6`/`INV-8`, R-05, R-13, drift D1.
- **D-4 — Evidence review cites public evidence only; separates verified from deferred.**
  Each claim row is tagged *verified-now* (CPU/scan/render/link/license/hygiene) or
  *manual-gate-deferred* (GPU/D1/GitHub-runner/at-publish). No private path/host/codename/
  source citation (`INV-1`, evidence-map rules; S3 docs-scrub lesson). Ref: adversarial
  case "accepts a claim with no public evidence".
- **D-5 — Product code is untouchable; classify before any fix.** If a release-blocking bug
  needs a source fix, stop and route through the Failure Arbiter and to the owner. The
  session edits only docs. *Alternative:* fix inline like S7's X-1 (rejected here — no such
  fix is in scope; any would need an explicit owner amendment). Ref: contract
  forbidden_files, PRD §6.
- **D-6 — Recommendation rule (advisory; owner ratifies).** Recommend **GO (beta / research
  preview)** iff *all* hold, each backed by command/evidence: scrub clean ∧ CPU checks green
  ∧ compose fp8+nvfp4 render clean ∧ `LICENSE`/hygiene present & correct ∧ every runtime
  claim evidence-qualified ∧ no unowned release-blocking risk ∧ GPU surface marked
  beta-limited ∧ acceptance matrix covers every PRD MUST. Otherwise **NO-GO** naming the
  specific unmet clause. Conditions that are true-but-only-resolvable-after-publish (GitHub
  CI run, CI badge, `security/policy`/`discussions` links, Private-vulnerability-reporting)
  are **at-publish conditions on the GO**, not blockers. Ref: session contract done_condition,
  `release_checklist.md` §9.
- **D-7 — Reviewer output is untrusted; high-risk review is mandatory.** 5 read-only
  reviewer subagents + a fresh-context adversarial verifier. Assert `tool_uses > 0` +
  concrete evidence before accepting an axis; reject rubber-stamps (S7 lesson). Ref:
  `project_contract.md` §5 (high risk), `docs/eval_corpus/mig_s7_review_injection_rubber_stamp.md`.
- **D-8 — Commit posture: local commits on `session-8` at clean checkpoints; no push.**
  Matches every prior session + PRD §6. The owner performs push/tag/release after
  ratification. Ref: PRD §6 non-goal.

## Risks / Trade-offs

- **[GPU deferred → users hit broken inference]** → every GPU mode marked beta-limited in
  the README (S7) + gate record + acceptance matrix; recommendation is conditional and names
  the deferred manual gates. Mitigation owner: this session + next GPU session.
- **[CPU CI green locally but GitHub runner unverified]** → recorded as an at-publish item
  (checklist §5; R-05); the recommendation lists it as a post-publish confirmation, and the
  evidence review tags it manual-gate-deferred.
- **[Scrub scanner is a heuristic / `$PRIVATE_REF_PATTERN` unset]** → run the committed
  `tests/test_private_ref_scan.py` (authoritative committed gate) over the controlled
  surface incl. `docs/session_8/**`; document the fallback and the broad-lexical/lockfile
  human gate (S5 FA-3); classify matches, do not edit out-of-radius files.
- **[Final docs contradict README/Docker/setup]** → reconciliation cross-checks the
  acceptance matrix, evidence map, risk register, and README claim matrix for agreement; the
  adversarial verifier tests this failure mode.
- **[Reviewer subagent injection]** → untrusted-output rule; reject no-evidence reviews and
  re-run the axis (S7 precedent).
- **[Recommending GO on incomplete evidence]** → the recommendation rule is explicit and
  each clause is backed by a check; the fresh-context verifier's job is to falsify the GO.

## Migration Plan

1. Refining pack (this doc set) → specs → tasks → plan → execution contract.
2. Re-run CPU deterministic checks; capture raw evidence; classify any failure before
   touching anything.
3. Build the four outputs (deterministic checks → acceptance matrix → evidence review →
   gate record), then reconcile the tracking docs.
4. Sharded review (5 axes) over deliverables + diff; fix only High/Critical; re-check.
5. Fresh-context adversarial verifier against the contract's adversarial cases + failure
   modes; classify any FAIL.
6. Handoff + eval seeds; record the recommended verdict; present for owner ratification.

**Rollback:** every deliverable is an additive or docs-only change; `git restore` per file
reverts cleanly. No runtime behavior can regress (no code touched).

## Open Questions

- **Owner ratification of the recommended verdict** — the GO/NO-GO is the owner's; this
  session records a recommendation and the evidence, and stops at the human gate.
- **GitHub-hosted CI + self-referential links/badges** — resolve only after the repo is
  public; tracked as at-publish items (`release_checklist.md` §9), not S8 blockers.
- **Drift D1 / real vLLM-Omni serve compatibility** — deferred to the GPU session; recorded
  as a beta limitation, not resolved here.
