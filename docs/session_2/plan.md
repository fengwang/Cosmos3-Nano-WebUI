# UX-S2 Plan (TDD micro-steps)

Test-first per task. Commands: `uv run pytest -m "not gpu" <path>` (backend),
`cd webui && pnpm test` (frontend). Commit at each ✅ checkpoint.

## Task 1 — Negative-prompt default (server)

**1a (RED)** `tests/api/test_negative_prompt_default.py`:
- `negative_prompt_path("/models/checkpoint") == "/models/checkpoint/assets/negative_prompt.json"`
- present file (tmp_path + monkeypatch `COSMOS3_MODEL_DIR`) → returns verbatim text; `json.loads` of it round-trips
- missing file → `None`; unset var → `None`; malformed JSON → `None`
- caching: patch reader / count opens → file read once (clear cache in fixture)
- `"/data/models" not in inspect.getsource(module)`

**1b (GREEN)** `api/preprocessing/negative_prompt.py`:
```python
from functools import lru_cache
import json, logging, os
_LOG = logging.getLogger("cosmos3.preprocessing.negative_prompt")
_ASSET_RELPATH = ("assets", "negative_prompt.json")

def negative_prompt_path(model_dir: str) -> str:
    return os.path.join(model_dir, *_ASSET_RELPATH)

@lru_cache(maxsize=8)
def _read_default(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        json.loads(text)  # validity gate only; bytes stay verbatim
    except (OSError, ValueError) as exc:
        _LOG.warning("negative-prompt default unavailable at %s (%s); proceeding without it", path, exc)
        return None
    return text

def load_default_negative_prompt() -> str | None:
    model_dir = os.environ.get("COSMOS3_MODEL_DIR")
    return _read_default(negative_prompt_path(model_dir)) if model_dir else None
```
(cache-hit skips the body → logs once per path.)

**1c (RED)** extend `tests/api/test_routes_generation.py`: omit → params carry the
default; supply → user value; default `None` → key absent.

**1d (GREEN)** `api/app/routes/generation.py`:
```python
from preprocessing.negative_prompt import load_default_negative_prompt
def _params(body, *, num_frames, generate_sound=False, negative_prompt_default=None):
    ...
    if params.get("negative_prompt") is None and negative_prompt_default is not None:
        params["negative_prompt"] = negative_prompt_default
    ...
# each handler: _params(body, num_frames=…, negative_prompt_default=load_default_negative_prompt())
```
✅ commit: `feat(ux-s2): curated negative-prompt overridable default (loader + route)`

## Task 2 — Video resolution mode-aware default (server)

**2a (RED)** extend `tests/test_vllm_omni_client.py`: `resolved_params(_rec(mode="t2v"))`
→ 1280×720; `mode="i2v"/"t2v_audio"` → 1280×720; `mode="t2i"` → 480×480; explicit
width/height win; explicit `resolution=480` on t2v → 480×480. New gen_worker test:
`_to_generation_request({"mode":"t2v","params":{}})` → 1280×720; `"t2i"` → 480.

**2b (GREEN)** `api/engines/base.py` (shared torch-free helper):
```python
VIDEO_MODES = frozenset({"t2v", "i2v", "t2v_audio"})
def default_dimensions(mode: str, resolution: int | None) -> tuple[int, int]:
    if resolution is not None:
        return int(resolution), int(resolution)
    return (1280, 720) if mode in VIDEO_MODES else (480, 480)
```
`api/engines/vllm_omni/client.py` `resolved_params`:
```python
from engines.base import default_dimensions
mode = str(getattr(record, "mode", "") or "")
dw, dh = default_dimensions(mode, p.get("resolution"))
# "width": int(p.get("width", dw)), "height": int(p.get("height", dh)),
```
`api/orchestrator/gen_worker.py` `_to_generation_request` (deferred import already
pulls engines.base): `dw, dh = default_dimensions(request.get("mode",""), params.get("resolution"))`
then `height=int(params.get("height", dh)), width=int(params.get("width", dw))`.

**2c** `api/app/schemas.py:96` description → "Square resolution ∈ {256,480,720}. When
width/height are omitted, video modes (t2v/i2v/t2v_audio) default to 1280×720; t2i
defaults to 480."

**2d** regen OpenAPI + `schema.d.ts`; `uv run pytest tests/test_openapi.py`.
✅ commit: `feat(ux-s2): mode-aware 720p video resolution default (server + schema desc)`

## Task 3 — WebUI defaults + affordance

**3a (RED)** extend the studio draft test: `initialDraft().preset === "hi-720"` and
params `{height:720,width:1280,num_frames:49}`; `standard-480` still applies 640×480/33;
`buildRequest` omits `negative_prompt` when blank; supplies it when typed. Component
test / assertion: negative-prompt input renders placeholder "Using recommended default".

**3b (GREEN)** `webui/lib/studio/draft.ts`: `const DEFAULT_PRESET: PresetId = "hi-720";`
`webui/components/studio/ComposePanel.tsx`: add
`placeholder="Using recommended default"` to the negative-prompt `<Input>` (verify the
design-system `Input` forwards `placeholder`; `Textarea` already does).

**3c** `cd webui && pnpm build && pnpm lint && pnpm typecheck && pnpm test`.
✅ commit: `feat(ux-s2): webui hi-720 default preset + negative-prompt placeholder`

## Task 4 — Deterministic verification

`uv run pytest -m "not gpu"`; webui suite; scoped
`rg -n "/data/models" api/preprocessing/negative_prompt.py` (clean) + confirm the 6
pre-existing `api/` fallbacks unchanged.
✅ commit (if not already): `test(ux-s2): spec-derived tests green`

## Task 5 — Live 5090 720p smoke

Bring up FP8 stack (`make up-fp8` or `docker compose -f deploy/docker-compose.fp8.yml`),
confirm the resolved model-assets mount, `POST /v1/generation/t2v` 1280×720 @49f with
`negative_prompt` omitted; capture peak VRAM (nvidia-smi / vram trace), artifact
metadata (`ffprobe`), and the server-log `Final prompt` / negative line. Repeat NVFP4.
Record `EV-UX-GPU-720-{FP8,NVFP4}-T2V`, `EV-UX-GPU-NEGPROMPT-APPLIED` into
`docs/evidence_map.md`. On env friction: classify ENVIRONMENT, record owner-visible
deferral with what was attempted.

## Task 6 — Review + close

Sharded review (5 axes) → fix High/Critical → re-check → adversarial verifier → verify
`GATE-UX-S2-DEFAULTS` → update evidence/risk/eval + handoff + eval_corpus.
✅ docs commit: `docs(ux-s2): review + adversarial + handoff + eval harvest`
