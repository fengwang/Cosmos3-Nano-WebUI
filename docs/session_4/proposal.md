# UX-S4 Proposal — README / Docs Friendliness

Date: 2026-07-16
Source: `docs/session_4/brainstorming.md` (owner-approved validated design).

## Motivation

The README reads as a contributor document: it interleaves a user quickstart with
a duplicated dev/CI section and a long limitations block, opens with a prominent
beta WARNING, and links to a doc that moved to the archive (E-12, R-08). The
project's real posture — settled by UX-S1/S2/S3 — is a low-friction trusted-LAN
appliance: no auth to configure, good output out of the box, a decluttered UI
that lands on the Studio. UX-S4 reframes the docs to match: a features-first
README with a runnable few-minute quickstart, dev/CI owned by `CONTRIBUTING.md`,
one slim honest "Status & security" section, and every internal link resolving.
Runs last (R-09), on the settled post-UX-S1/S2/S3 state (FR-9).

## Specific Changes Agreed

1. **Restructure `README.md`** to Approach A (task-first funnel): relaxed tone
   (drop the top `[!WARNING]`; soften the status badge), features-first, a
   ~5-min quickstart (`clone → hf download FP8 → make build → make up-fp8 →
   make health → open Studio`) that reflects the no-auth flow and the UX-S2
   defaults (curated negative prompt + 720p video), a tightened Checkpoint-setup
   pointing at `docs/model_setup.md`, a slim Troubleshooting, and one honest
   **Status & security** section at the end.
2. **Relocate dev/CI into `CONTRIBUTING.md`.** Fold the README's remaining dev
   bits into the already-present CONTRIBUTING workflow (no duplication), then
   delete the README "Development" section (leaving a one-line pointer).
3. **`SECURITY.md`:** repoint `(R-16)` → live **R-01**; keep the honest
   no-auth/loopback/socket notes; add one honest guardrails-off line.
4. **Drop** the README "Release readiness → `docs/release_checklist.md`" bullet
   (archived internal artifact; the honest status now lives in Status & security).
5. **`webui/app/layout.tsx`:** fix the stale "Session 8" `metadata.description`
   (mirror the subtitle) and the "S9" comment.

## Capabilities

### New capabilities

- **`readme-friendliness`** — the README leads with what the project does and a
  runnable few-minute quickstart; the development/CI workflow is owned by
  `CONTRIBUTING.md` (referenced, not restated in README). Spec:
  `specs/readme-friendliness.md`. Refs FR-9.

### Modified capabilities

- **`docs-integrity`** — every internal relative link in `README.md`,
  `SECURITY.md`, and `CONTRIBUTING.md` resolves to a file that exists; there is
  no reference to the archived `docs/release_checklist.md` and no live `R-16`
  reference; no residual auth prose; the security/status callout is slim and
  **honest** (states no-auth + trusted-LAN + loopback + root-equivalent socket +
  guardrails-off; never implies untested modes work). Spec:
  `specs/docs-integrity.md`. Refs FR-9, FR-10, INV-4; eval `EV-UX-DOCS-LINKS-RESOLVE`.

## Impact

- **Docs:** `README.md` (major restructure), `CONTRIBUTING.md` (own dev/CI),
  `SECURITY.md` (R-16→R-01 + guardrails line), `docs/session_4/**`, and the
  closing updates to `docs/evidence_map.md`, `docs/risk_register.md`,
  `docs/eval_seed_cases.md`, `docs/handoff.md`, `docs/eval_corpus/`.
- **Code:** exactly one file — `webui/app/layout.tsx` (metadata/comment copy
  only; no behavior, no rendered UI change beyond the document `<title>`/
  `description` metadata string). Explicitly allowed by the blast radius.
- **APIs / schemas / deploy / tests:** none (FR-10; no schema-shape change; no
  new dependency).
- **Verification:** deterministic link resolver + two `rg` sweeps; `webui` build/
  lint/typecheck/test to prove the `layout.tsx` copy edit is safe; 6-axis sharded
  review; fresh-context adversarial verifier (full treatment, per Q1).

## Non-Goals (from contract)

- Any api/webui/deploy/schema/test change beyond the `layout.tsx` copy fix.
- Reintroducing auth prose (re-verify none remains).
- Editing `docs/archive/**` or the substance of `docs/model_setup.md`.
- Marketing copy, images, or a new site.
