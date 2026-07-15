# Session Handoff

## State Snapshot
- **Session:** UX-S2 — Generation Defaults: Negative-Prompt Preset + 720p Video (risk: medium)
- **Branch:** `phase3-session-2`
- **Last commit:** the docs/handoff commit on `phase3-session-2` (see `git log --oneline abdf65f..HEAD`)
- **Changed files (code):** NEW `api/preprocessing/negative_prompt.py`; edited
  `api/app/routes/generation.py`, `api/engines/base.py`, `api/engines/vllm_omni/client.py`,
  `api/engines/vllm_omni/work.py`, `api/orchestrator/gen_worker.py`, `api/app/schemas.py`;
  regenerated `schemas/openapi.json`, `webui/lib/api/schema.d.ts`; edited
  `webui/lib/studio/draft.ts`, `webui/components/studio/ComposePanel.tsx`;
  edited `deploy/docker-compose.{base,fp8,nvfp4}.yml`; NEW/edited tests
  (`tests/api/test_negative_prompt_default.py`, `tests/test_gen_worker_mapping.py`,
  `tests/api/test_routes_generation.py`, `tests/api/conftest.py`, `tests/test_vllm_omni_client.py`,
  `tests/test_vllm_omni_work.py`, `webui/lib/studio/draft.test.ts`); `.gitignore`; docs.
- **Checks run:** CPU `uv run pytest -m "not gpu"` (**518 passed**); WebUI `pnpm build && lint &&
  typecheck && test` (**208 passed**); OpenAPI regen + `tests/test_openapi.py` (in sync,
  description-only diff); `ruff check api tests` (clean); scoped no-abs-path check
  (`EV-UX-NEGPROMPT-NO-ABS-PATH` clean; 6 pre-existing fallbacks unchanged); `make scan` (clean);
  `make config-fp8`/`config-nvfp4` (render clean); **live 5090 720p smoke FP8 + NVFP4 PASS**;
  Playwright DOM check of the WebUI placeholder + 720p default; 6-axis sharded review; adversarial
  verifier (**PASS**, second pass).
- **Checks not run:** guardrails-ON GPU validation (out of scope); i2v/t2v_audio/t2i GPU runs
  (only the recommended t2v 720p smoke was in scope); no PR/push (owner integrates separately).
- **Current status:** GATE-UX-S2-DEFAULTS **PASS**. Deterministic criteria green; the recommended
  FP8/NVFP4 720p smoke is **recorded green** (both produce a valid 1280×720/49f artifact out-of-box);
  the negative default is confirmed **applied** (same-seed output differs with vs without). All work
  committed on `phase3-session-2`.

## Narrative Context
UX-S2 makes good output the zero-configuration default: the API applies the curated
`negative_prompt.json` (from `${COSMOS3_MODEL_DIR}/assets/`, verbatim JSON string, overridable,
graceful fallback) when a request omits `negative_prompt`, and video modes default to 1280×720 via a
pure mode-aware `default_dimensions` used by both engine paths (`t2i` unchanged; explicit values still
win). The WebUI defaults to the `hi-720` preset and shows a "Using recommended default" placeholder.
No public schema **shape** changed (INV-6) — only defaults + one description. The owner elected to run
the recommended 5090 smoke **live**, which proved the defaults generate correctly **and** surfaced that
the shipped stack could not serve 720p out-of-box; the proven serving config was then baked into the
compose stacks so it now works via `make up-fp8` / `make up-nvfp4`.

## Decision Log
| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| Negative-prompt transport (R-04 human gate) | Serialized JSON string, verbatim, existing `str` field | Structured API field; prose flattening | Server-log precedent; no shape change (INV-6); works for both backends | Interview Q1; E-15 |
| Defaulting architecture | Approach 2 (layer-matched): resolution in engine layer, negative at route | Edge-unified; engine-unified | Two different concerns (pure rule vs file-I/O); honors contract's engine-layer pointer; preserves INV-P5-1 | brainstorming; design D1 |
| Loader fallback when `COSMOS3_MODEL_DIR` unset | Return `None` (no abs-path fallback) | Reuse a `/data/models` default | Keeps the loader free of any absolute literal → INV-1 clean by construction | design D3; E-15 |
| 720p GPU smoke (human gate) | Run live now | Documented deferral | Owner elected; 5090 + local checkpoints available | Interview Q2 |
| Make 720p serve out-of-box | Bake full serving config (shm/tiling/offload-fp8/guardrails-off) into compose | Memory-only; code-only + doc prerequisite | Owner chose "get a green artifact"; a default that OOMs is a broken deliverable | Interview Q(deploy); E-17/E-18/E-19 |
| FP8 vs NVFP4 offload | FP8 uses `--enable-layerwise-offload`; NVFP4 does NOT | Uniform config | NVFP4 Marlin FP4 repack is CUDA-only → offload breaks it at startup | A5; E-18 |

## Next Priority Queue
1. **UX-S3 (WebUI declutter):** may proceed; the studio request path is unchanged by UX-S2 except
   the `hi-720` default + placeholder. No blockers.
2. **UX-S4 (README/docs) — inherits two flags from UX-S2:** (a) the **guardrails-off** deployment
   posture (the compose now runs `--no-guardrails`) MUST get an honest `SECURITY.md`/`README` callout;
   (b) the **R-05 720p VRAM caveat** (FP8 peak 14,665 MiB / NVFP4 18,517 MiB; requires offload/tiling/
   shm; guardrails-off) belongs in the status callout. Also still-pending from UX-S1: the dangling
   `release_checklist.md` link + live `R-16` reference.
3. **Optional follow-up (out of UX-S2 scope):** resolve the guardrails deployment gap properly for
   operators who want guardrails ON (bundle/install `cosmos_guardrail` + gated model + `HF_TOKEN`) —
   this is the archived MIG-S8 manual GPU gate.

## Warnings And Gotchas
- **Environment:** the shipped generation stack requires (now baked) `--no-guardrails` +
  `--vae-use-tiling` + `shm_size 16gb`; FP8 also `--enable-layerwise-offload` (NVFP4 must not).
  Pyright "Import could not be resolved" warnings are the `pythonpath=["api"]` static gap — not real.
- **Known failing tests:** none.
- **Deferred risks:** guardrails-off posture (documented, flagged for UX-S4); R-05 residual (720p is
  best-effort within ~32 GB — comfortable with the baked config but the operator must keep it);
  `negative_prompt` has no length cap (pre-existing, trusted-LAN, out of scope).
- **Files future sessions must not casually edit:** `schemas/openapi.json`,
  `webui/lib/api/schema.d.ts` (regenerate, never hand-edit); the per-stack vllm-omni `command:` blocks
  (the offload/tiling/guardrails posture is load-bearing for 720p — change with a re-smoke).
- **A local untracked `.env`** pins `COSMOS3_{FP8,NVFP4}_DIR=/data/models/...` (owner host); the
  committed compose uses repo-relative `${VAR:-../models/...}` defaults (no absolute path committed).

## Handoff to UX-S4 (contract handoff_requirements)
- **Transport decision recorded:** serialized JSON string, verbatim (E-15; `negative_prompt.py` docstring).
- **Measured 720p peak VRAM + guardrails posture** recorded in `docs/evidence_map.md` (E-17/E-18/E-19)
  and `docs/eval_seed_cases.md` (Recorded Results): FP8 14,665 MiB, NVFP4 18,517 MiB, guardrails off.
- **R-05 residual VRAM caveat + guardrails-off posture** flagged for the UX-S4 README/SECURITY callout.

## Eval Seeds
- **Missed check:** a "preset a default" session's blast radius must include the deployment config that
  makes the default *serve*; the api had no checkpoint mount (default silently no-op) — caught only by
  the live smoke. → project-contract template (`docs/eval_corpus/ux-s2-generation-defaults.md` §1).
- **New regression test candidates (added):** `default_dimensions` direct unit (incl. t2i explicit 720);
  INV-P5-1 metadata==form on the default path; malformed-JSON log-once.
- **Instruction update candidates:** (a) the sharded-review *prompt* (6 axes) is authoritative over a
  contract's `review_axes` — run the superset (owner-caught, §5); (b) never `git add -A`; gitignore
  `.playwright-mcp/` (§6); (c) grep archived phase docs for a GPU symptom before trial-and-error (§4).
