# UX-S3 Adversarial Verification

Date: 2026-07-15
Verifier: fresh-context agent; inputs limited to `docs/session_3_contract.yaml`,
`docs/project_contract.md`, the diff (`7bf5388..HEAD`), and
`docs/session_3/webui_smoke.md`. Mandate: falsify that `GATE-UX-S3-WEBUI` is
satisfied.

## Verdict: PASS

The verifier independently re-ran every deterministic check and reproduced every
runtime behavior; it could not disprove the functional done condition.

### Reproduced (by the verifier, not trusted from the claim)
- `pnpm build` exit 0 — route table has **no `/gallery`**, `/` = 128 B redirect
  route, `/studio` present; `pnpm lint` / `pnpm typecheck` exit 0;
  `pnpm test` = **42 files / 214 passed**.
- Runtime (dev server + curl): `GET /` → **307** `location: /studio`;
  `GET /studio` → 200 ("Generation Studio"); **`GET /gallery` → 404** (route
  genuinely gone by URL).
- Shipped **production** CSS (`.next/static/css`): `.media { max-height: 80vh }`,
  `.studio { max-width: 80rem }`, compare-grid `1fr 1fr` intact, **no `60vh`/
  `60rem` anywhere**.
- Tests are non-tautological: replayed the three specs' assertions against base
  `7bf5388` — each would FAIL on the old code (old nav had a 5th `/gallery`
  item; old page returned a Card with the `/gallery` link and never redirected;
  old CSS was `60vh`/`60rem`). Confirmed the 3 new files actually run (not
  silently skipped): +3 files / +6 tests with no confounder.
- Blast radius: no forbidden file touched (no `api/**`, auth, proxy, openapi,
  README/SECURITY/CONTRIBUTING, Reasoning/Action/History, `docs/archive/**`).
  INV-7 (same-origin BFF) intact — no proxy/API/fetch change. Adversarial case
  #4 refuted: all 7 `@/design-system` components the gallery imported remain
  exported.

### Per acceptance criterion: PASS (all four)
gallery gone (404 + clean sweep + no dangling import) · `/`→`/studio` (307) ·
both media bounds raised + responsive + compare-grid intact · build/lint/
typecheck/test green.

## Residual doubt raised (documentary) — CLOSED

The verifier flagged two **documentation** gaps (explicitly "does not affect any
shipped code behavior", not gate-blocking), which were the session-end docs not
yet written when it ran:

1. `execution_contract.md` claimed the UX-S3-A1 blast-radius amendment was
   recorded "and in `docs/evidence_map.md`", but that file had not been updated.
   → **Closed:** UX-S3-A1 is now recorded in `docs/evidence_map.md` (note under
   the UX-S3 section) and as a `docs/risk_register.md` row, mirroring the
   UX-S1-A1 precedent the verifier itself confirmed.
2. The contract's `handoff_requirements` (final media dimensions + landing
   behavior for UX-S4) lived in `webui_smoke.md`, not the canonical
   `docs/handoff.md`. → **Closed:** `docs/handoff.md` rewritten for UX-S3 with
   the 80rem/80vh dimensions and the `/`→`/studio` landing in the "Handoff to
   UX-S4" section.

No code change resulted from the verification; the two closures are additive doc
updates within the blast radius.
