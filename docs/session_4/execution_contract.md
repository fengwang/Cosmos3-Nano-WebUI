# UX-S4 Execution Contract — README / Docs Friendliness

Date: 2026-07-16
Authority: `docs/session_4_contract.yaml` (UX-S4), `docs/project_contract.md`.
Design: `docs/session_4/design.md` (owner-approved 2026-07-16: Approach A README;
relaxed tone with caveats consolidated at the end; drop the README release-checklist
bullet + repoint SECURITY R-16→R-01; full verification treatment).

## Planned File Changes

| File | Change | In blast radius |
|---|---|---|
| `README.md` | Restructure to Approach A: relaxed tone, features-first, ~5-min quickstart, tightened checkpoint setup, slim Status & security, drop "Release readiness", **remove** the Development command block (relocated) | ✅ |
| `CONTRIBUTING.md` | Become the sole owner of dev/CI (fold in `uv python install 3.12` + CI-mirror framing; tidy the archived "release checklist" prose) | ✅ |
| `SECURITY.md` | Repoint `(R-16)` → live **R-01**; add one honest guardrails-off line; keep slim | ✅ |
| `webui/app/layout.tsx` | Copy-only: `metadata.description` mirrors the subtitle (drop "Session 8"); fix the "S9" comment | ✅ (single allowed non-doc file) |
| `docs/session_4/**` | Refining pack + review + adversarial + smoke record | ✅ |
| `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/handoff.md`, `docs/eval_corpus/**` | Close-out updates | ✅ |

## Allowed Blast Radius

From `session_4_contract.yaml.blast_radius.allowed_files`: `README.md`,
`CONTRIBUTING.md`, `SECURITY.md`, `docs/session_4/**`, `docs/evidence_map.md`,
`docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/handoff.md`,
`webui/app/layout.tsx`.

**Forbidden — stop if hit:** any `api/**`, `webui/**` (other than
`webui/app/layout.tsx`), `deploy/**`, `schemas/**`, `tests/**`; `.env`,
`.env.example`; `docs/archive/**`; the *substance* of `docs/model_setup.md`
(link-correctness only, if any); model weights / generated media.

**Note on `layout.tsx`:** the contract's `forbidden_files` says "any … webui/** …
file" but its `allowed_files` explicitly lists `webui/app/layout.tsx`. Allowed is
the more specific rule and the UX-S3 handoff assigns this stale-copy fix to UX-S4;
the edit is metadata/comment copy only (no behavior, no component/render change).

## First Check To Write

`scratchpad/check_docs.py` — a relative-link resolver over `README.md`,
`SECURITY.md`, `CONTRIBUTING.md` (+ the two `rg` sweeps). Run it on the current
tree first (**RED**): it records the two references to fix
(`README.md:202` release_checklist, `SECURITY.md:55` R-16). After the edits it
must be **GREEN** (zero unresolved; `rg "release_checklist|R-16"` clean;
`rg "COSMOS3_API_KEY|X-API-Key"` clean). This is `EV-UX-DOCS-LINKS-RESOLVE`.

## Checks After Each Task

- After every doc edit: `uv run python scratchpad/check_docs.py` (link resolver +
  sweeps) — no new unresolved link introduced.
- After the README restructure: spec-derived asserts — features precede the
  quickstart; each quickstart essential present (`clone`, `hf download`,
  `make build`, `make up-fp8`, `make health`, UI URL); no dev command block in
  `README.md`; the dev commands are present in `CONTRIBUTING.md`.
- After the `layout.tsx` edit: from `webui/`,
  `pnpm build && pnpm lint && pnpm typecheck && pnpm test` green.
- Before the session commit: full resolver + both sweeps clean; Status & security
  per-mode claims cross-checked against `docs/evidence_map.md`.
- Classify any failure (BUG / SPEC_GAP / AMBIGUITY / ENVIRONMENT / TEST_BUG)
  before fixing (`docs/agent_workflow/prompts/failure_arbiter.md`).

## Review Axes (end of session)

correctness · security · tests · architecture · performance · readability
(read-only, deduplicated; 6-axis sharded-review prompt). Full treatment per the
interview (Q1), matching the UX-S3 precedent for a low-risk session.

## Adversarial Verifier Brief

Fresh context; sees only `docs/session_4_contract.yaml`, the diff, and recorded
evidence. Try to falsify that `GATE-UX-S4-DOCS` is satisfied. Attack:
1. the README dropped a must-have setup step, so a new user cannot actually run
   it (checkpoint download / `make build` / `up-fp8` / `health` missing);
2. a relocated dev section was deleted from README but never actually added to
   `CONTRIBUTING.md` (lost, not moved);
3. the rewrite reintroduced auth instructions UX-S1 removed;
4. the slimmed security note became dishonest — implies untested modes work, or
   hides the no-auth / socket / guardrails-off / loopback posture;
5. a "friendly" link points at a file that does not exist (or the archived
   `release_checklist.md` / a live `R-16` survives);
6. per-mode verification claims drifted ahead of `docs/evidence_map.md`;
7. an out-of-radius file was changed, or the `webui` suite is not actually green
   after the `layout.tsx` edit.

## Concrete Done Condition

`GATE-UX-S4-DOCS` passes:
- `README.md` is features-first with a runnable few-minute quickstart; no
  development/CI command block remains in it;
- the development/CI workflow lives in `CONTRIBUTING.md` (present, not duplicated);
- one slim honest Status & security callout is present and accurate (no-auth +
  trusted-LAN + loopback + root-equivalent socket + guardrails-off; per-mode
  status matches `evidence_map.md`);
- `rg -n "release_checklist|R-16" README.md SECURITY.md` clean (SECURITY repointed
  to R-01); `rg -n "COSMOS3_API_KEY|X-API-Key" README.md SECURITY.md` clean;
- every relative link in `README.md`/`SECURITY.md`/`CONTRIBUTING.md` resolves
  (`EV-UX-DOCS-LINKS-RESOLVE`);
- `webui` build/lint/typecheck/test green after the `layout.tsx` copy fix;
- no out-of-radius file changed.

Invariants held: INV-4 (trusted-LAN + socket documented, not silently accepted);
no code/behavior change beyond `layout.tsx` copy; FR-10 (no schema-shape change).

## Recorded amendment — UX-S4-A1 (2026-07-16)

The contract's `blast_radius.allowed_files` lists `docs/session_4/**` and the
evidence/risk/eval-seed/handoff docs but omits `docs/eval_corpus/**`, while the
Session End Protocol (step 4) explicitly directs "Add eval seeds to
`docs/eval_corpus/`" — the location UX-S3 already established
(`docs/eval_corpus/ux-s3-webui-declutter.md`). Accordingly this session adds one
additive file, `docs/eval_corpus/ux-s4-docs-friendliness.md` (eval harvest only;
no product/behavior change). Recorded here (the session-contract YAML is outside
this session's write-radius), mirroring the UX-S1-A1 / UX-S3-A1 precedent.
