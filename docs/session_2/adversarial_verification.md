# UX-S2 Adversarial Verification

Date: 2026-07-15
Method: fresh-context verifier (no access to the implementation conversation), sees
only the contracts, the diff, and recorded evidence; tries to falsify the done
condition (`docs/agent_workflow/prompts/adversarial_verifier.md`).

## Pass 1 — FAIL (correctly)

**Verdict: FAIL.** The verifier confirmed the code + all invariants + all 8
adversarial cases + the CPU/WebUI/OpenAPI/no-abs-path checks were sound, but
FAILED the done condition for two concrete reasons:

1. **Smoke evidence not recorded.** The claimed GPU numbers (FP8 14,665 MiB,
   NVFP4 18,517 MiB, the negative-prompt frame diff) appeared nowhere in the tree;
   `docs/evidence_map.md`, `risk_register.md`, `eval_seed_cases.md`, and
   `handoff.md` were untouched since UX-S1; the session GPU-smoke tasks were still
   unchecked. The done condition requires the smoke *recorded* (or deferred with
   owner acceptance) — neither existed yet. **Root cause:** lifecycle sequencing —
   the verifier ran (step 10) before the evidence-recording step (step 12).
2. **Out-of-radius files committed.** `.playwright-mcp/` transient scratch (console
   log + page snapshot) were swept in by a `git add -A` during the live-run
   Playwright check — not deliverables, not gitignored.

## Fixes applied

- Recorded the smoke into `docs/evidence_map.md` (E-15..E-19), `eval_seed_cases.md`
  ("Recorded Results"), and resolved `risk_register.md` R-03/R-04/R-05/R-06; wrote
  `docs/handoff.md` and the eval harvest. (Failure Arbiter A8.)
- Removed `.playwright-mcp/` from tracking and gitignored it. (Failure Arbiter A7.)

## Pass 2 — PASS

**Verdict: PASS.** The fresh verifier independently re-ran the deterministic checks
and reproduced them: **CPU 518 passed**; `tests/test_openapi.py` 3 passed **and** a
fresh `openapi_export` produced byte-identical output to the committed
`schemas/openapi.json` (genuinely regenerated, INV-6 — only the `resolution`
description changed); no-abs-path clean with the 6 pre-existing matches unchanged;
WebUI `pnpm typecheck` + `pnpm test` (208) + `pnpm build` green. It traced every
invariant and adversarial case and found them held:

- INV-1 (path from env only, never request/absolute); R-04 (verbatim JSON string,
  graceful on malformed/missing); R-06 (both engine paths + WebUI land on 1280×720
  for video, t2i unchanged — an API-only client also gets 720p); INV-5 (overridable;
  standard-480 + picker intact); INV-6 (no shape change); INV-P5-1 (form == metadata
  on the default path, proven by the F3 test); INV-8 + guardrails honesty (the app
  already sent `guardrails:False`; the compose flag aligns the server default and is
  openly documented + owner-authorized, flagged for UX-S4).
- Smoke evidence present, internally consistent across evidence_map / eval_seed_cases
  / risk_register / compose comments, and consistent with the baked compose args.

### Non-blocking notes it raised (all handled)

- **Blast-radius overstep:** `api/engines/vllm_omni/work.py` was edited (F1/F8 dedup
  Nits) but is not in `allowed_files`. → **Reverted** to original (Failure Arbiter A11);
  F1 duplication deferred as a follow-up.
- `docs/eval_corpus/ux-s2-generation-defaults.md` and `.gitignore` are outside the
  enumerated `allowed_files` but are lifecycle-mandated (eval harvest) / hygiene
  (the A7 fix) and follow the UX-S1 convention — accepted, enumeration gap noted.
- The verifier's own `pnpm lint` failed on an ENVIRONMENT incompatibility in its
  sandbox (eslint-patch vs Node 26); the lint config is unchanged from parent and
  `pnpm lint` passed in the implementation environment.

## Outcome

After the fixes + the `work.py` revert, GATE-UX-S2-DEFAULTS is satisfied and the
done condition holds. Final re-run of the deterministic checks confirms green.
