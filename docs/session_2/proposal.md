# UX-S2 Proposal — Generation Defaults

Date: 2026-07-15
Source: `docs/session_2/brainstorming.md` (owner-approved Approach 2).

## Motivation

Preset the model's intended output quality as the zero-configuration default,
without removing user choice: apply the curated negative prompt as an
overridable server-side default, and make 1280×720 the default resolution for
video modes at both the API server layer and the WebUI default preset —
leaving `t2i` defaults and the resolution picker intact.

## Specific Changes Agreed

1. New loader `api/preprocessing/negative_prompt.py`: derive
   `${COSMOS3_MODEL_DIR}/assets/negative_prompt.json`, load its **verbatim text**
   (cached), graceful `None` on unset-var/missing/unreadable/malformed.
2. `api/app/routes/generation.py`: inject the loaded default into `params` when
   the request omits `negative_prompt` (user value overrides; no default → omit).
3. `api/engines/vllm_omni/client.py` `resolved_params()` and
   `api/orchestrator/gen_worker.py` `_to_generation_request()`: mode-aware
   dimension default — video → 1280×720, `t2i` → 480; explicit `width`/`height`
   or explicit square `resolution` still win.
4. `api/app/schemas.py`: update the `resolution` field **description** only
   (no schema-shape change).
5. `webui/lib/studio/draft.ts`: `DEFAULT_PRESET → "hi-720"`.
6. `webui/components/studio/ComposePanel.tsx`: add a
   `placeholder="Using recommended default"` to the negative-prompt input.
7. Tests under `tests/**` (backend) and `webui/**` (frontend) for every scenario.
8. Live 5090 FP8+NVFP4 720p smoke recorded into `docs/evidence_map.md`
   (+ eval seeds), with the transport decision and measured peak VRAM.

## Transport Decision (R-04) — Recorded

The curated structured negative prompt reaches the engine as a **serialized JSON
string** carried by the existing `negative_prompt: str` field — the loader passes
the file's verbatim JSON text. Evidence: the pipeline logs
`Final prompt: '{ … }'` (it consumes a serialized-JSON prompt string); the API
field, the vLLM-Omni multipart field, and the diffusers pipeline argument are all
strings. **No public schema shape changes** (INV-6).

## Capabilities

### New capabilities

- **`negative-prompt-default`** — the API applies the curated negative prompt
  from the configurable model-assets path as an overridable default when a
  request omits `negative_prompt`, with graceful degradation when the file is
  absent. Spec: `specs/negative-prompt-default.md`.

### Modified capabilities

- **`video-resolution-default`** — the server default resolution becomes
  mode-aware: video modes default to 1280×720 when dimensions are omitted, while
  `t2i` is unchanged; explicit dimensions still override. Spec:
  `specs/video-resolution-default.md`.
- **`webui-generation-defaults`** — the WebUI default-selected preset for the
  (video) initial draft becomes `hi-720`, and the negative-prompt field shows a
  "using recommended default" affordance; `standard-480` and the full picker
  remain. Spec: `specs/webui-generation-defaults.md`.

## Impact

- **Code**: `api/preprocessing/negative_prompt.py` (new); `api/app/routes/
  generation.py`, `api/engines/vllm_omni/client.py`,
  `api/orchestrator/gen_worker.py`, `api/app/schemas.py` (edits);
  `webui/lib/studio/draft.ts`, `webui/components/studio/ComposePanel.tsx` (edits).
- **APIs**: no request/response **shape** change; only default values and one
  field description change. `schemas/openapi.json` is regenerated from code if
  the description change alters it, and `tests/test_openapi.py` guards sync.
- **Dependencies**: none added (stdlib `json`, `os`, `logging` only; INV-3).
- **Config**: the loader reads the existing `COSMOS3_MODEL_DIR`. No new env var
  is required; `.env.example`/compose mounts are only touched if the API service
  cannot already read the model-assets file at runtime (verified during the
  smoke).
- **Runtime behavior**: video requests that omit dimensions now render 1280×720;
  requests that omit `negative_prompt` now carry the curated default. Both are
  overridable (INV-5).
- **Evidence/docs**: `docs/evidence_map.md`, `docs/risk_register.md`,
  `docs/eval_seed_cases.md`, `docs/eval_corpus/`, `docs/handoff.md`.
