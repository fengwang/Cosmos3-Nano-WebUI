# Session 8 Proposal - Release Gate, Evidence Review, and Handoff

Session: MIG-S8
Risk: high · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S8-BETA`
Derived from: `brainstorming.md` (approved 2026-07-07)

## Motivation

The migration touches public source, dependency pins, model setup, CI, Docker, README
claims, and release hygiene across `MIG-S1`..`MIG-S7`. Before the GitHub repo is called
ready for public beta, a final, adversarial, evidence-based review must reconcile every
gate, re-run the CPU deterministic checks, record the manual GPU gate status, ensure no
release-blocking risk is unowned, confirm public claims match public evidence, and produce
an owner GO/NO-GO with a reproducible evidence bundle. This session produces **no runtime
behavior change** — it is a verification, reconciliation, and handoff pass.

## Specific changes agreed

1. Re-run the 7 contract CPU deterministic checks live and capture raw output; record
   any check that cannot run, with reason.
2. Produce the four session outputs: acceptance matrix (per PRD MUST), deterministic-checks
   log, evidence review, and gate record.
3. Record the entire GPU inference surface (`EV-MIG-GPU-*`) as a **NOT-YET-RUN /
   beta-limited** manual gate (owner decision 1), each with the exact deferred command and
   the pin/revisions any later run must match. Drift D1 recorded as an owner-visible beta
   limitation.
4. Reconcile `evidence_map.md`, `risk_register.md`, `eval_seed_cases.md`, and
   `release_checklist.md` to the final migration state — no unowned release-blocking risk.
5. Record a **recommended** `GATE-MIG-S8-BETA` verdict with rationale for owner
   ratification (owner decision 2).
6. Run the high-risk review gates: 5-axis sharded review (read-only subagents) + a
   fresh-context adversarial verifier; fix only High/Critical (doc/evidence errors);
   classify any failure with the Failure Arbiter.
7. Write the public-beta handoff and add `docs/eval_corpus/mig_s8_*.md` eval seeds.

No runtime source, schema, dependency pin, Docker publishing workflow, or vLLM-Omni fork
source is edited. If a release-blocking bug needs a source fix, stop and surface to the
owner (no fix without approval).

## Capabilities

These are the S8 capabilities. Each gets a spec file under `docs/session_8/specs/`.

### New capabilities

- **deterministic-checks** — re-run the contract's CPU checks and record a deterministic,
  reproducible pass/fail log, including checks that cannot run and why.
- **acceptance-matrix** — map every PRD MUST to its gate, public evidence, and a verdict
  in `{PASS | BETA-LIMITED | NO-GO}`.
- **evidence-review** — tie each major public claim to a public evidence row; separate
  verified-now from manual-gate-deferred; cite no private evidence.
- **gate-record** — record `GATE-MIG-S1..S8` status with public evidence pointers, the GPU
  manual-gate status, drift D1 disposition, and the recommended owner GO/NO-GO verdict +
  the rule that produced it.
- **gpu-beta-limited-disposition** — record every GPU surface as a manual gate with the
  exact deferred command, the pin/revision to match, and the README marking that keeps
  `INV-8` satisfied.
- **doc-reconciliation** — bring `evidence_map.md`, `risk_register.md`,
  `eval_seed_cases.md`, and `release_checklist.md` to a consistent final state with no
  unowned release blocker and no contradiction of README/Docker/setup docs.

### Modified capabilities

- None. This session changes no existing capability's REQUIREMENTS; it verifies and
  reconciles them. Public API shape, schemas, and dependency pins are unchanged (`INV-9`,
  `INV-10`).

## Impact

- **Docs:** `docs/session_8/**` (refining pack + outputs + review artifacts),
  `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
  `docs/handoff.md`, `docs/release_checklist.md`, `docs/eval_corpus/mig_s8_*.md`.
- **Code / schemas / deps:** none.
- **Systems:** the recommendation feeds the owner's `GATE-MIG-S8-BETA` decision; the
  handoff hands the next session (GPU validation / at-publish) the deferred manual gates.
