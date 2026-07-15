# UX-S2 Execution Contract

Date: 2026-07-15
Authority: `docs/session_2_contract.yaml` (UX-S2), `docs/project_contract.md`.
Approach: Approach 2 (layer-matched), owner-approved.

## Planned File Changes

| File | Change |
|---|---|
| `api/preprocessing/negative_prompt.py` | **new** — pure path + cached loader Action (verbatim text, graceful `None`) |
| `api/app/routes/generation.py` | inject the loaded default into `_params` (user → default → omit) |
| `api/engines/base.py` | add pure `default_dimensions(mode, resolution)` + `VIDEO_MODES` |
| `api/engines/vllm_omni/client.py` | `resolved_params` uses mode-aware `default_dimensions` |
| `api/orchestrator/gen_worker.py` | `_to_generation_request` uses mode-aware `default_dimensions` |
| `api/app/schemas.py` | `resolution` field **description** only (no shape change) |
| `webui/lib/studio/draft.ts` | `DEFAULT_PRESET → "hi-720"` |
| `webui/components/studio/ComposePanel.tsx` | negative-prompt placeholder |
| `schemas/openapi.json`, `webui/lib/api/schema.d.ts` | **regenerated** (never hand-edited) if the description change alters them |
| `tests/api/test_negative_prompt_default.py` | **new** |
| `tests/api/test_routes_generation.py`, `tests/test_vllm_omni_client.py`, gen_worker test | extended |
| `webui/lib/studio/*.test.ts` (+ ComposePanel assertion) | extended |
| `docs/session_2/**`, `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/eval_corpus/`, `docs/handoff.md` | updated |

## Allowed Blast Radius (from contract)

Allowed: the files above (all within `session_2_contract.yaml.blast_radius.allowed_files`;
`api/engines/base.py` and `tests/**` and the docs are explicitly allowed).
`deploy/docker-compose.*.yml` / `.env.example` are touched **only if** the smoke shows
the API service cannot read the model-assets file at runtime.

Forbidden (stop if needed): auth plumbing (removed in UX-S1); `webui/app/gallery/**`,
`webui/app/page.tsx`, `PrimaryNav.tsx`, media CSS (UX-S3); `README.md` restructure,
`CONTRIBUTING.md` (UX-S4); any checkpoint-revision or vLLM-Omni pin; `docs/archive/**`;
model weights / generated media.

## First Test To Write

`tests/api/test_negative_prompt_default.py::test_negative_prompt_path_derives_from_model_dir`
— asserts `negative_prompt_path("/models/checkpoint")` ==
`/models/checkpoint/assets/negative_prompt.json` and that the module source contains no
`/data/models` literal (INV-1, `EV-UX-NEGPROMPT-NO-ABS-PATH`).

## Checks After Each Task

- After a backend task: `uv run pytest -m "not gpu" <touched test files>`, then the
  full `uv run pytest -m "not gpu"` before the task's commit.
- After the schema description change: regenerate OpenAPI + `schema.d.ts`;
  `uv run pytest tests/test_openapi.py`.
- After the WebUI task: `cd webui && pnpm build && pnpm lint && pnpm typecheck && pnpm test`.
- Path check: `rg -n "/data/models" api/preprocessing/negative_prompt.py` (expect clean);
  confirm the pre-existing 6 `/data/models` matches elsewhere in `api/` are unchanged.
- Classify any failure (BUG / SPEC_GAP / AMBIGUITY / ENVIRONMENT / TEST_BUG) before fixing.

## Review Axes (end of session)

correctness · security · tests · architecture · performance (sharded, read-only).

## Adversarial Verifier Brief

Fresh context; sees only `docs/session_2_contract.yaml`, the diff, and recorded
evidence. Try to falsify that `GATE-UX-S2-DEFAULTS` is satisfied. Specifically attack:
1. negative-prompt path hardcoded / only works on the owner host (INV-1);
2. structured JSON stuffed into the string field → malformed / ignored (R-04);
3. flipping the video default also changed `t2i` (mode-awareness missing);
4. WebUI defaults to hi-720 but the API server default stayed 480 for API-only clients;
5. 720p FP8 OOMs with guardrails on / higher frame count (R-05);
6. a missing `negative_prompt.json` crashes generation instead of degrading;
7. schema shape changed (INV-6) or OpenAPI drifted;
8. preset change broke unrelated draft/request unit tests silently.

## Concrete Done Condition

`GATE-UX-S2-DEFAULTS` passes:
- curated negative prompt loads from the configurable path, applies as an overridable
  default, and degrades gracefully (`EV-UX-NEGPROMPT-DEFAULT-APPLIED`,
  `EV-UX-NEGPROMPT-NO-ABS-PATH`);
- 1280×720 is the video default at server + UI, `t2i` unchanged, picker intact
  (`EV-UX-RESOLUTION-DEFAULT-VIDEO-720`);
- CPU suite + WebUI build/lint/typecheck/test green; OpenAPI in sync;
- the live FP8+NVFP4 720p smoke is recorded green (neg-prompt engaged, peak VRAM
  < 32 GB, server-log evidence) — the owner elected to run it live; an ENVIRONMENT
  deferral is recorded honestly only if the stack cannot be brought up.

Invariants held: INV-1, INV-5, INV-6, INV-8, INV-P5-1.
