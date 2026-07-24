# UX-S4 Tasks — README / Docs Friendliness

Source: `docs/session_4/specs/*.md`, `docs/session_4/design.md`. Ordered by
dependency. Each task is verifiable. Spec-derived checks in `plan.md`.

## 1. Verification harness (do first)

- [ ] 1.1 Build a reusable relative-link resolver over `README.md`,
  `SECURITY.md`, `CONTRIBUTING.md` (parses Markdown/HTML links + image `src`,
  resolves each relative target against the repo root, reports unresolved).
- [ ] 1.2 Capture the baseline: run the resolver + `rg -n
  "release_checklist|R-16" README.md SECURITY.md` + `rg -n
  "COSMOS3_API_KEY|X-API-Key" README.md SECURITY.md`. Record the two known
  dangling references (`docs-integrity` scenarios).

## 2. CONTRIBUTING owns dev/CI (before deleting the README copy)

- [ ] 2.1 Fold the README-unique dev bits (`uv python install 3.12`, the "mirrors
  the CPU-only CI in `.github/workflows/ci.yml`" framing) into `CONTRIBUTING.md`
  so it is the complete, sole owner (`readme-friendliness`: dev/CI owned by
  CONTRIBUTING). Tidy the loose "the release checklist" prose.

## 3. README restructure (Approach A)

- [ ] 3.1 Header + tone: soften the status badge; replace the top `[!WARNING]`
  with a light trusted-LAN `[!NOTE]` pointer (`readme-friendliness`: relaxed tone).
- [ ] 3.2 What it does + Features table (honest per-mode status matching
  `evidence_map.md`) placed before the quickstart (`readme-friendliness`:
  features-first).
- [ ] 3.3 Quickstart (~5 min) with every essential step + the no-auth / 720p /
  curated-negative-prompt callouts (`readme-friendliness`: runnable quickstart).
- [ ] 3.4 Requirements + tightened Checkpoint setup pointing at
  `docs/model_setup.md` (in-scope item 4).
- [ ] 3.5 Slim Troubleshooting.
- [ ] 3.6 One slim **Status & security** section: no-auth/trusted-LAN/loopback/
  socket + guardrails-off + 720p FP8/NVFP4 advisory; per-mode status honest
  (`docs-integrity`: honest callout + 720p advisory).
- [ ] 3.7 Project & contributing links; **drop** "Release readiness"; **delete**
  the README "Development" command block (relocated) leaving a pointer
  (`readme-friendliness`: no dev/CI block in README).

## 4. SECURITY.md + layout.tsx

- [ ] 4.1 `SECURITY.md`: repoint `(R-16)` → live **R-01**; add one honest
  guardrails-off line; keep it slim (`docs-integrity`: no live R-16).
- [ ] 4.2 `webui/app/layout.tsx`: fix `metadata.description` (mirror the
  subtitle, drop "Session 8") and the "S9" comment (design D4).

## 5. Deterministic verification

- [ ] 5.1 Re-run the link resolver + both `rg` sweeps → all clean
  (`docs-integrity` scenarios; `EV-UX-DOCS-LINKS-RESOLVE`).
- [ ] 5.2 From `webui/`: `pnpm build && pnpm lint && pnpm typecheck && pnpm test`
  green (proves the `layout.tsx` copy edit is safe).
- [ ] 5.3 Spec-derived assertions: features precede quickstart; each quickstart
  essential present; dev commands live only in CONTRIBUTING; Status & security
  states the four posture facts + guardrails-off; per-mode claims match
  `evidence_map.md`.

## 6. Review + verification (full treatment)

- [ ] 6.1 6-axis sharded review (correctness/security/tests/architecture/
  performance/readability); dedupe; fix only High/Critical; re-check.
- [ ] 6.2 Fresh-context adversarial verifier vs `GATE-UX-S4-DOCS`; classify any
  failure with the Failure Arbiter.

## 7. Close-out

- [ ] 7.1 Update `docs/evidence_map.md` (UX-S4 recorded evidence),
  `docs/risk_register.md` (R-08/R-09 resolved), `docs/eval_seed_cases.md`
  (`EV-UX-DOCS-LINKS-RESOLVE` result).
- [ ] 7.2 Write `docs/handoff.md`; add an eval seed to `docs/eval_corpus/`; state
  residual risks (R-05 VRAM caveat, deferred R-16).
