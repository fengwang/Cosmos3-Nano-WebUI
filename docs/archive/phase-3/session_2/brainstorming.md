# UX-S2 Brainstorming — Generation Defaults: Negative-Prompt Preset + 720p Video

Date: 2026-07-15
Session: UX-S2 (risk: medium; routing: worker + sharded review + adversarial verifier)
Inputs: `docs/prd.md`, `docs/session_2.md`, `docs/session_2_contract.yaml`,
`docs/project_contract.md`, `docs/evidence_map.md`, `docs/risk_register.md`,
`docs/handoff.md` (UX-S1).

## 1. Problem / Motivation

The model ships a curated negative prompt (`assets/negative_prompt.json`, a
~15 KB structured object) and generates cleanly at 720p on the quantized path,
but the API applies **neither** by default: `negative_prompt` has no default and
nothing loads the file (`E-04`), and the server default resolution is 480
(`E-07`). A new user must discover and set both to get the model's intended
output quality. UX-S2 presets both so good output is the zero-configuration
default, while keeping every preset an **overridable** default (INV-5).

## 2. Project Context Explored

- **Deployed generation path is `COSMOS3_GEN_ENGINE=vllm_omni`** (default) — the
  API POSTs to a separate vLLM-Omni container. The `diffusers_oracle`/
  `gen_worker` path is the dormant alternate (`COSMOS3_GEN_ENGINE=diffusers`).
  Both read `record.params` / `record.mode`.
- **Model-directory variable is `COSMOS3_MODEL_DIR`** (in-container
  `/models/checkpoint`), read by both engine loaders. Per `E-06` the curated
  file lives at `${COSMOS3_MODEL_DIR}/assets/negative_prompt.json`. The
  quantized checkpoints are present locally under
  `models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise/` (gitignored — NFR-1 safe), each
  carrying the real `negative_prompt.json` plus bundled 720p examples + logs.
- **Transport evidence (R-04):** the real 720p server log
  (`…/EV-P5-S2-FP8-720-189-EXPLORE/server_log.txt`) shows the pipeline logging
  `Final prompt: '{ "subjects": [...] }'` — it consumes the prompt as a
  **serialized JSON string** over the multipart wire. Both the API field
  (`negative_prompt: str | None`) and the vLLM-Omni form field are already
  strings; the diffusers path also passes a string to the pipeline.
- **`resolved_params()` is documented pure** ("reads only `record.params`, no
  env, no clock") and is the **single source** feeding both the request form and
  the recorded job metadata (INV-P5-1, "so the two can never desync"). A file
  read cannot live inside it.
- **Resolution default lives twice**: `resolved_params()`
  (`api/engines/vllm_omni/client.py:78`) and `_to_generation_request()`
  (`api/orchestrator/gen_worker.py:34`), both `resolution→480` with width/height
  falling back to that square value.
- **WebUI**: `DEFAULT_PRESET = "standard-480"` (`draft.ts:18`); `initialDraft()`
  starts in `t2v`. The `hi-720` preset already exists (1280×720, 49 frames,
  `presets.ts:22-27`). The negative-prompt input (`ComposePanel.tsx:68-72`) has
  no placeholder; a blank value is omitted from the request (`request.ts:19`).
- **INV-8 advisory**: there is no dynamic 720p warning in `modes.ts`; the 720p
  advisory lives in the `hi-720` preset description ("higher VRAM/latency — see
  advisory"). Making `hi-720` the default surfaces that advisory by default.

## 3. Decisions Fixed With the Owner (interview, 2026-07-15)

1. **Transport (R-04 human gate): serialized JSON string in the existing
   `negative_prompt: str` field** — verbatim file text. No schema-shape change
   (INV-6). Ratified by owner.
2. **720p 5090 smoke: run live this session** (not deferred) — bring up the
   Docker/vLLM-Omni stack, generate 720p `t2v` on FP8 **and** NVFP4 with the
   negative-prompt default engaged, record peak VRAM + server-log evidence.
3. **Ambiguous `rg -n "/data/models" api/` check**: scope it to the new loader
   (`api/preprocessing/negative_prompt.py`, must be clean) and separately assert
   the 6 pre-existing `COSMOS3_MODEL_DIR` fallbacks elsewhere in `api/` are
   unchanged (not newly introduced). The literal whole-`api/` sweep is *not*
   zero today; the check's real intent is `EV-UX-NEGPROMPT-NO-ABS-PATH`.
4. **Commits**: checkpoint commits on `phase3-session-2` at clean task
   boundaries; no PR/push (mirrors UX-S1).

## 4. Approaches Considered

The two defaults have different natures: resolution is a **pure rule** that needs
the mode; the negative prompt is an **enrichment from a config asset** that needs
**file I/O**.

- **Approach 1 — Edge-unified.** Apply both defaults at the route into `params`;
  the engine `480` default becomes vestigial. *Pro:* one seam. *Con:* diverges
  from the contract's engine-layer pointer for resolution; dead code; moves the
  API-server-default guarantee away from the layer the contract names.
- **Approach 2 — Layer-matched (CHOSEN).** Resolution mode-aware default in the
  engine server-default path (`resolved_params` + `_to_generation_request`,
  reading `mode`) — exactly where the contract points and the authoritative last
  line, so API-only clients also get 720p. Negative-prompt default as a new
  `api/preprocessing/negative_prompt.py` Action injected once at the route.
  *Pro:* honors the contract; each default in the layer matching its nature;
  preserves INV-P5-1 single-source and INV-6. *Con:* two defaulting sites (for
  two genuinely different concerns).
- **Approach 3 — Engine-unified.** Load the file inside each backend's Action
  shell alongside resolution. *Pro:* all defaults near the engine. *Con:*
  duplicates the file-load across two backends, breaks `_to_generation_request`
  purity, drags in the dormant diffusers path — messiest.

**Chosen: Approach 2**, approved by the owner.

## 5. Validated Design Shape

- **A. Loader — `api/preprocessing/negative_prompt.py`**
  - `negative_prompt_path(model_dir: str) -> str` — pure:
    `join(model_dir, "assets", "negative_prompt.json")`.
  - `load_default_negative_prompt() -> str | None` — Action: read
    `COSMOS3_MODEL_DIR`; if unset → `None` (no absolute-path fallback, so the
    loader carries zero `/data/models` literals); read file text, sanity-parse
    with `json.loads`, return the **raw verbatim text** on success; on
    missing/unreadable/malformed → **log once, return `None`** (graceful
    degradation, never crash). Cached (read once per process; test-resettable).
- **B. Route — `api/app/routes/generation.py`**: `_params(...)` gains
  `negative_prompt_default: str | None`; each handler passes
  `load_default_negative_prompt()`. Precedence: **user value → else default →
  else omit** (INV-5 overridable).
- **C. Resolution rule — `resolved_params()` + `_to_generation_request()`**:
  explicit `width`/`height` win → else explicit `resolution` (square) wins →
  else **mode-aware default**: video (`t2v`/`i2v`/`t2v_audio`) → `1280×720`;
  `t2i` → `480`. `resolved_params` reads `record.mode` (already receives the
  record) and remains the single form+metadata source.
- **D. Schema — `api/app/schemas.py:96`**: description-only update (no shape
  change, INV-6): note video-omitted → 1280×720, `t2i` → 480.
- **E. WebUI**: `draft.ts` `DEFAULT_PRESET → "hi-720"` (initial `t2v` draft →
  720p video default); `ComposePanel.tsx` add
  `placeholder="Using recommended default"` on the negative-prompt input.
  `request.ts`/`presets.ts`/`types.ts` need **no change**.
- **F. INV-8 posture**: 720p served only by the quantized path (deployment
  fact); the existing 720p preset advisory now shows by default; the 49-frame /
  guardrails-off headroom is the mitigation; the R-05 residual VRAM caveat is
  recorded in `evidence_map.md` and flagged for UX-S4's README. No new server
  advisory logic (out of scope).
- **G. Testing (spec-derived)**: loader (present/missing/unset/malformed/cached +
  no-abs-path); route precedence (default applied / user overrides / graceful
  none); resolution mode-aware (t2v→1280×720, t2i→480, explicit wins,
  resolution-square wins); WebUI (`initialDraft()`→hi-720/1280×720/49;
  blank-negative omit; placeholder present).

## 6. Out of Scope (session boundary)

Auth (UX-S1), WebUI declutter/media viewport (UX-S3), README/CONTRIBUTING
(UX-S4); any change to `t2i` resolution default; checkpoint-revision or
vLLM-Omni pin changes; guardrails-on GPU validation; `num_frames` defaulting
(the 49-frame count ships via the preset; the engine `num_frames` default is
untouched).
