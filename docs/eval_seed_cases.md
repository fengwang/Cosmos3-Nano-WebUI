# Eval Seed Cases - UX Simplification and Trusted-LAN Appliance Posture

Date: 2026-07-15

These cases seed the deterministic checks and the recommended manual GPU
smokes for `UX-S1`..`UX-S4`. Deterministic checks are blocking; GPU smokes are
recommended, non-blocking, and human-gated (PRD Owner Decision 8).

## Public Checkpoint IDs (unchanged this phase)

- FP8 (generation): `wfen/Cosmos3-Nano-FP8-Blockwise` @
  `9bf5d6ae164688487bdb71947ccc6ebe70d12900`.
- NVFP4 (generation): `wfen/Cosmos3-Nano-NVFP4-Blockwise` @
  `5514c42b9759739f545e0d0dee453db8d8525fbc`.
- BF16 base (reasoner + action; **not** the 720p video path):
  `nvidia/Cosmos3-Nano` @ `fea6e03ac3d7884b4105ed8ee79fc480fca70965`.
- vLLM-Omni fork commit: `697035018b70cef76b974a909d23371a9984c3f2`.

This phase does not change any checkpoint revision or the fork pin.

## Deterministic Checks (blocking)

| ID | Purpose | Inputs | Expected properties | Gate |
|---|---|---|---|---|
| EV-UX-AUTH-SWEEP-CLEAN | No auth reference survives removal. | `rg --hidden -n "COSMOS3_API_KEY\|X-API-Key\|x_api_key\|api_key\|apiKey\|require_api_key\|UnauthorizedError" -g '!docs/archive/**'` over the tracked tree. | Zero matches outside `docs/archive/**` and this pack's own descriptive prose. | UX-S1 |
| EV-UX-OPENAPI-INSYNC | The regenerated OpenAPI has no auth surface and matches the committed file. | Regenerate `schemas/openapi.json` from the app (`api/app/openapi_export.py`); run `tests/test_openapi.py`. | No `x-api-key` parameter or security scheme anywhere; `tests/test_openapi.py` passes. | UX-S1 |
| EV-UX-HEALTH-OPEN-NOAUTH | Health/metrics and the formerly-gated routers all respond without a key. | With no key configured and the dependency removed: request `/v1/health/ready`, `/v1/metrics`, and a formerly-protected route (e.g. `POST /v1/jobs`). | None returns 401; health/metrics behavior is unchanged; the protected route reaches its normal (non-auth) response. | UX-S1 |
| EV-UX-CPU-SUITE-GREEN | The CPU + WebUI suites stay green after each code session. | `uv run pytest -m "not gpu"`; from `webui/`, `pnpm build && pnpm lint && pnpm typecheck && pnpm test`. | All green; no skipped-because-broken auth tests left behind. | UX-S1, UX-S2, UX-S3 |
| EV-UX-NEGPROMPT-DEFAULT-APPLIED | The curated negative prompt applies as an overridable default. | Unit/integration with the engine mocked: (a) request omitting `negative_prompt`; (b) request supplying one; (c) file-missing case. | (a) the file-sourced default reaches the engine call; (b) the user value wins; (c) generation proceeds with no negative prompt and logs once — no crash. | UX-S2 |
| EV-UX-NEGPROMPT-NO-ABS-PATH | The negative-prompt path is configurable, not hardcoded. | `rg -n "/data/models" api/` and inspection of the loader. | No hardcoded absolute path; the path derives from the model-directory environment variable (INV-1). | UX-S2 |
| EV-UX-RESOLUTION-DEFAULT-VIDEO-720 | 720p is the default for video only; images unchanged; UI agrees with server. | A `t2v`/`i2v`/`t2v_audio` request with no dims; a `t2i` request with no dims; the WebUI default preset for video. | Video defaults to 1280×720; `t2i` default is unchanged; the WebUI default-selected video preset is `hi-720`; the resolution picker still offers all families. | UX-S2 |
| EV-UX-GALLERY-GONE | The gallery is fully removed and the landing routes to the Studio. | `rg -i "gallery\|/gallery" webui/app webui/components`; navigate `/`. | No `/gallery` route, nav item, or link (apart from the unrelated `HistoryList` "history/gallery" comment); `/` renders or redirects to the Studio; build/typecheck green. | UX-S3 |
| EV-UX-MEDIA-ENLARGED | The media viewport is larger than baseline. | Compare `MediaPreview.module.css` `max-height` and the studio container `max-width` against the `60vh`/`60rem` baseline; component/visual check. | Both bounds increased; layout stays responsive; the compare-grid still renders side by side. | UX-S3 |
| EV-UX-DOCS-LINKS-RESOLVE | Every internal doc link resolves; no archived/dead references. | Relative-link check over `README.md`, `SECURITY.md`, `CONTRIBUTING.md`; `rg -n "release_checklist\|R-16" README.md SECURITY.md`. | Every relative link points at an existing file; no link to `docs/release_checklist.md`; no live `R-16` reference (repointed or dropped). | UX-S4 |

## Manual GPU Smokes (recommended, non-blocking, human-gated)

Record the evidence fields below when run. A documented, owner-accepted
deferral satisfies the SHOULD if hardware/time is unavailable.

| ID | Purpose | Checkpoint | Request shape | Expected properties | Gate |
|---|---|---|---|---|---|
| EV-UX-GPU-720-FP8-T2V | Confirm the shipped 720p video default fits 32 GB on FP8. | FP8 | `t2v`, 1280×720, the shipped default frame count, documented seed. | Valid video artifact; recorded peak VRAM < 32 GB; guardrails posture noted. Baseline: bundled `assets/FP8-Examples/EV-P5-S2-FP8-720-189-EXPLORE` peaked 31,957 MiB at 189 frames — the 49-frame default should sit lower. | UX-S2 |
| EV-UX-GPU-720-NVFP4-T2V | Same for NVFP4 (more VRAM headroom). | NVFP4 | `t2v`, 1280×720, shipped default frame count, documented seed. | Valid video artifact; recorded peak VRAM < 32 GB. Baseline: bundled `nvfp4-t2v-flagship.mp4` is 1280×720/189-frame. | UX-S2 |
| EV-UX-GPU-NEGPROMPT-APPLIED | Confirm the default negative prompt actually reaches the engine, not just the request. | FP8 or NVFP4 | A 720p `t2v` with `negative_prompt` omitted so the default engages. | Server log shows the negative prompt received by the pipeline; artifact valid. Closes the R-04 end-to-end concern. | UX-S2 |

## Evidence Fields

For every manual GPU smoke, record:

- hardware and driver/CUDA context
- WebUI repo commit
- vLLM-Omni fork commit (`697035018b70cef76b974a909d23371a9984c3f2` unless a
  contract changes it — not this phase)
- checkpoint repo ID and revision
- request mode, prompt/fixture, dimensions, frames, fps, steps, seed
- **peak VRAM (MiB) and the guardrails posture used**
- artifact path, dimensions, streams, duration, and pass/fail result
- known limitation if the case is not passed

## Recorded Results — UX-S2 (2026-07-15, live RTX 5090)

Context: RTX 5090 (32,607 MiB), driver 610.43.03, vLLM-Omni `697035018b70…`.
Request: `t2v`, dims **and** `negative_prompt` omitted (both server defaults
engaged), `num_frames=49`, `seed=42`, `steps=35`, `guidance=6.0`, guardrails off.
Serving config required (baked into `deploy/docker-compose.*.yml`): `shm_size 16gb`
+ `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` + `--vae-use-tiling` +
`--no-guardrails`; FP8 also `--enable-layerwise-offload` (NVFP4 must NOT — Marlin
FP4 repack is CUDA-only).

| ID | Result | Peak VRAM | Artifact |
|---|---|---|---|
| EV-UX-GPU-720-FP8-T2V | **PASS** | 14,665 MiB (< 32 GB) | 1280×720, 24 fps, 49 frames, 2.04 s MP4 |
| EV-UX-GPU-720-NVFP4-T2V | **PASS** | 18,517 MiB (< 32 GB) | 1280×720, 24 fps, 49 frames, 2.04 s MP4 |
| EV-UX-GPU-NEGPROMPT-APPLIED | **PASS** | — | Same-seed output differs with vs without the curated default (frame-24 md5 `e38aa2…` ≠ `c92031…`; 2.4 MB ≠ 2.8 MB) → the default reaches + affects the engine |

Both stacks verified out-of-box via `make up-fp8` / `make up-nvfp4` (no override).
Key correction to the blueprint conjecture (E-08/E-09): the bundled 189-frame
example fit only because it used layer-wise offload and no negative prompt; the
49-frame default does **not** fit with a naive resident/untiled config. The
negative prompt does not change peak VRAM (embeddings pad to `max_sequence_length`).
Artifacts recorded by metadata only (not committed — NFR-1).

## Recorded Results — UX-S3 (2026-07-15, WebUI declutter)

Deterministic (blocking) checks, run and independently reproduced by the
adversarial verifier. No GPU smoke applies (presentation-only).

| ID | Result | Evidence |
|---|---|---|
| EV-UX-GALLERY-GONE | **PASS** | `webui/app/gallery/` deleted; nav rail = Studio/Reasoning/Action/History; home stub → `redirect("/studio")`. `rg -i "gallery\|/gallery" webui/app webui/components` → only the `HistoryList` comment; build route table has no `/gallery`; `GET /gallery`→404; `GET /`→307→`/studio`→200. |
| EV-UX-MEDIA-ENLARGED | **PASS** | `.media max-height` 60vh→**80vh**, `.studio max-width` 60rem→**80rem** (source + shipped `.next/static/css`); `.media` keeps `max-width:100%`, no fixed px; compare-grid `1fr 1fr` intact. Playwright: studio `max-width` computes 1280px @1440; studio section 347px @375 (the enlargement does not overflow). |
| EV-UX-CPU-SUITE-GREEN | **PASS** | `pnpm build && pnpm lint && pnpm typecheck && pnpm test` all exit 0; **42 files / 214 tests** (baseline 39/208 + 3 new UX-S3 specs, run via the broadened vitest `include`, UX-S3-A1). |

Out-of-scope note: a pre-existing app-shell horizontal overflow at ≤~651px
viewport width (`webui/app/globals.css` + `app/layout.tsx`, untouched by this
session) is flagged for a future session — the UX-S3 media enlargement itself is
responsive.
