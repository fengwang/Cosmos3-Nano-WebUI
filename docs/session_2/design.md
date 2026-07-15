# UX-S2 Design — Generation Defaults

Date: 2026-07-15
Source: `docs/session_2/{brainstorming.md, proposal.md}`.

## Context

Generation serves a single quantized checkpoint via `COSMOS3_GEN_ENGINE=vllm_omni`
(HTTP to a separate container); a dormant `diffusers` path exists behind the same
`record.params`/`record.mode`. The negative prompt is plumbed end-to-end as an
optional `str` with no default; nothing loads the curated file. The resolution
default is `480` in two engine-layer functions. The WebUI already has a `hi-720`
preset but defaults to `standard-480`. The curated file
(`${COSMOS3_MODEL_DIR}/assets/negative_prompt.json`) is a ~15 KB structured
object; the pipeline consumes prompts as serialized JSON strings.

Constraints: INV-1 (no hardcoded absolute path), INV-5 (overridable), INV-6 (no
schema-shape change), INV-8 (quantized-only 720p; advisory not silent OOM),
INV-P5-1 (`resolved_params` is the single desync-safe source for form+metadata).

## Goals

- Curated negative prompt applied as an overridable server-side default from a
  configurable path, with graceful fallback.
- 1280×720 the default for video modes at server **and** UI; server default and
  UI default preset agree; `t2i` unchanged; picker intact.
- WebUI "using recommended default" affordance.
- Live FP8+NVFP4 720p smoke recorded (peak VRAM, neg-prompt engaged).

## Non-Goals

- Auth (S1), WebUI declutter/media (S3), README (S4); `t2i` resolution default;
  checkpoint/vLLM-Omni pin changes; guardrails-on GPU; `num_frames` defaulting;
  a structured-object API field; new server advisory logic.

## Decisions

- **D1 — Layer-matched defaulting (Approach 2).** Resolution default in the
  engine server-default path where the contract points; negative-prompt default
  as a `preprocessing/` Action injected at the route. *Why:* the two defaults
  have different natures (pure rule vs file I/O); matching each to its layer
  honors the contract's named location for resolution and keeps the impure load
  isolated in the contract-blessed `preprocessing/` home. *Alternatives:*
  edge-unified (dead engine code, moves the server-default guarantee) and
  engine-unified (duplicated I/O, breaks `_to_generation_request` purity) — both
  rejected in brainstorming.
- **D2 — Transport = serialized JSON string, verbatim (R-04).** Pass the file's
  raw JSON text through the existing `negative_prompt: str`. *Why:* server-log
  evidence shows the pipeline consumes a serialized-JSON prompt string; every
  layer already carries a string; preserves INV-6. *Alternatives:* structured
  API field (breaks INV-6) and prose-flattening (loses curated structure) —
  rejected.
- **D3 — No absolute-path fallback in the loader.** If `COSMOS3_MODEL_DIR` is
  unset, return `None` (no negative prompt), rather than defaulting to a
  `/data/models/...` literal. *Why:* keeps the loader free of any `/data/models`
  literal so `EV-UX-NEGPROMPT-NO-ABS-PATH` is trivially clean and INV-1 holds by
  construction; in deployment the compose stacks always set `COSMOS3_MODEL_DIR`.
  *Alternative:* reuse an engine default constant — rejected (reintroduces an
  absolute-path literal into the loader).
- **D4 — Graceful degradation is uniform.** Unset var, missing file, unreadable
  file, or malformed JSON all resolve to `None` with a **single** WARNING log;
  generation proceeds with no negative prompt. *Why:* the intended UX win must
  never become a crash (adversarial case #6, R-03).
- **D5 — Cache the file read.** `functools.lru_cache` on a path-keyed reader; the
  15 KB file is read at most once per process. Tests reset the cache. *Why:* a
  per-request 15 KB read is wasteful; caching keeps the request path allocation-
  light without a stateful singleton.
- **D6 — Verbatim text, with a `json.loads` validity gate.** The transported
  bytes are the file's exact text (matching the curated asset); `json.loads` is
  used only as a well-formedness gate that routes a corrupt file to graceful
  degradation (its parsed value is discarded). *Why:* honors the owner's
  "verbatim JSON text" choice while still degrading on corruption.
- **D7 — Mode-aware rule precedence.** explicit `width`/`height` → explicit
  square `resolution` → mode-aware default. *Why:* preserves full overridability
  (INV-5); an API client can still request 480 video or 720 image explicitly.
- **D8 — `resolved_params` reads `record.mode`.** It already receives the whole
  record; reading `.mode` for the default keeps it the single form+metadata
  source (INV-P5-1) without threading mode through a new argument.

## Data Flow

```
GenerationBody (route fixes mode)
  └─ _params(body, …, negative_prompt_default = load_default_negative_prompt())
       • negative_prompt: user value → else default → else omit
  └─ JobSubmit(mode, params) → JobRecord(mode, params)
       └─ vllm_omni_work → resolved_params(record)         [DEPLOYED]
            • dims: explicit → resolution-square → mode-aware(mode) default
            • negative_prompt: passed through from params (serialized JSON str)
       └─ gen_worker.dispatch → _to_generation_request(request)  [dormant]
            • same mode-aware dims; negative_prompt passed through
```

## Error Handling

- Loader: catches `OSError`/`FileNotFoundError`/`ValueError`
  (`json.JSONDecodeError`), logs once at WARNING, returns `None`.
- Route: no new failure mode — a `None` default simply means the field is omitted.
- Engine layer: unchanged failure semantics; only the default dimension values
  change.

## Testing Strategy

- **Loader unit** (`tests/api/test_negative_prompt_default.py`, new): present →
  verbatim text; missing/unset/malformed → `None` + one log; caching; path
  derives from `COSMOS3_MODEL_DIR`; no `/data/models` literal in the module.
- **Route unit** (extend `tests/api/test_routes_generation.py`): omit → default
  in params; supply → user wins; default `None` → field absent.
- **Resolution unit** (extend `tests/test_vllm_omni_client.py` and a
  gen_worker test): t2v/i2v/t2v_audio omit dims → 1280×720; t2i omit → 480×480;
  explicit dims win; explicit `resolution` square wins; metadata matches form.
- **WebUI** (`webui/lib/studio/*.test.ts`, `ComposePanel` test): `initialDraft()`
  → `hi-720` + 1280×720/49; blank negative omitted; placeholder rendered.
- **OpenAPI**: regenerate; `tests/test_openapi.py` stays green (description-only).

## Migration Plan

Additive, single branch `phase3-session-2`, checkpoint commits per task. No data
migration. Rollback = revert the branch; defaults return to 480 / no negative
prompt. The live GPU smoke runs after CPU+WebUI green; on environment friction it
is classified ENVIRONMENT and recorded as an owner-visible deferral (the owner
elected to run it live, so a genuine effort is made first).

## Risks / Trade-offs

- **R-03 hardcoded path** → D3 (no absolute literal in loader; derive from env).
- **R-04 malformed transport** → D2/D6 (verbatim serialized-JSON string; log
  precedent) + the smoke confirms the engine actually receives it.
- **R-05 thin FP8 720p headroom** → 49-frame default (< the 189-frame proof),
  guardrails off, NVFP4 recommended for headroom; the live smoke measures the
  shipped config; residual caveat handed to UX-S4.
- **R-06 default divergence** → D1/D7/D8: server and UI both land on 1280×720 for
  video; `t2i` untouched; adversarial cases cover both divergences.
- **Trade-off**: two defaulting sites (accepted — two different concerns).
- **Trade-off**: the engine `480` default remains reachable only for `t2i` and as
  a safety net; not dead code under Approach 2.

## Open Questions

- Does the deployed API service actually mount the model-assets file at runtime?
  Verified during the smoke; if not, add the mount to
  `deploy/docker-compose.*.yml` (allowed by blast radius) — otherwise no compose
  change.
