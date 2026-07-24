# P3 Evidence — Reasoning via `vllm-omni` `/v1/chat/completions` (result: **image-gen, not text**)

Date: 2026-07-24. Probe: standalone omni server, faithful option-(a) test.

## Setup (throwaway/dev wiring)
- Image `cosmos3-nano-vllm-omni:local` (fork `github.com/fengwang/vllm-omni@6970350`,
  base `vllm/vllm-openai:v0.24.0`).
- `docker run -d --gpus all -p 127.0.0.1:8000:8000 --shm-size 16gb -e
  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True -v
  /data/models/Cosmos3-Nano-FP8-Blockwise:/models/checkpoint:ro … vllm serve
  /models/checkpoint --omni --host 0.0.0.0 --port 8000 --init-timeout 1800
  --no-guardrails --vae-use-tiling --enable-layerwise-offload` (identical to the
  deployed FP8 stack command). Checkpoint on disk = rev `4e181f9`.
- Ready on `/v1/models` in **~45 s**; resident **~13.2–13.5 GiB** (of 32).

## Route surface exposed by the ONE `--omni` server (from launcher logs)
`/v1/chat/completions` (+ `/batch`,`/render`,`/derender`), `/v1/completions`,
`/v1/responses`, `/v1/messages`, `/v1/images/generations`, `/v1/images/edits`,
`/v1/videos`(+`/sync`,`/{id}`…), `/v1/audio/speech`(+`/generate`,`/voices`),
`/generative_scoring`, `/inference/v1/generate`, **`/v1/omni/sleep`**,
**`/v1/omni/wakeup`** (residency control), and WebSocket endpoints
`/v1/video/chat/stream`, `/v1/realtime`, `/v1/realtime/video`, and
**`/v1/realtime/robot/openpi`** (endpoint `realtime_robot_openpi` — the action
surface; see P5). `/v1/models` id = `/models/checkpoint`.

## Reasoning coherence probes (pre-registered prompts)
| prompt | finish_reason | completion_tokens | content |
|---|---|---|---|
| "What is 2+2? Reply with just the number." | stop | 1 | **IMAGE** (base64 PNG, ~1.46 M chars) |
| "…what color is a clear daytime sky?" | stop | 1 | **IMAGE** |
| "List three primary colors…" | stop | 1 | **IMAGE** |

Every text prompt yields a **single image**, not text. `completion_tokens=1` = one
image artifact, not a token stream.

## Text-elicitation attempts (fair effort to find a text path)
- `response_format: {"type":"text"}` → still an **IMAGE** (~1.46 M b64 chars).
- `modalities: ["text"]` → **HTTP 500** `"Image generation failed: 'numpy.ndarray'
  object has no attribute 'save'"` (the server attempted image gen regardless).
- The checkpoint **does** ship a Qwen3-style text `chat_template.json` + tokenizer
  (text tower present), and the chat request schema exposes **no** output-modality
  selector (only TTS `task_type`). So the image binding is a serving/model default,
  not request-controllable via the standard API.

## Verdict (rubric)
- **Reasoning option (a) — omni serves text reasoning via `/v1/chat/completions` —
  is NOT satisfied.** The endpoint exists but is bound to **image generation**; no
  request-level way to get text. This reproduces/explains E-05 ("reasoning not
  working"): pointing `/v1/reason` at the omni server returns images.
- ⇒ **Reasoning mechanism = (c)** (a side-by-side reasoner, as today via the BF16
  base — E-04). **Zero-BF16 reasoning has no proven path** from this spike: the
  omni serving does not expose the quantized understanding/text tower as text.
  Achieving zero-BF16 reasoning is an **AM-S2 investigation** (elicit text from the
  omni/understanding tower via a fork modality flag, or serve the quantized text
  tower on a separate engine) — currently **unproven** ⇒ explicit owner decision
  (accept a BF16 reasoner side-car, which violates the zero-BF16 hard goal INV-4,
  or fund the AM-S2 investigation).

## VRAM (P7 partial)
idle **18 MiB** → omni generation server resident **~13.2–13.5 GiB** (FP8 +
layerwise offload; stayed ~13.5 GiB while producing an image). Well within 32 GiB.

## Receipts (commands + trimmed raw output)
```
$ docker run -d --name amrs1-omni --gpus all -p 127.0.0.1:8000:8000 --shm-size 16gb \
    -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    -v /data/models/Cosmos3-Nano-FP8-Blockwise:/models/checkpoint:ro \
    cosmos3-nano-vllm-omni:local vllm serve /models/checkpoint --omni --host 0.0.0.0 \
    --port 8000 --init-timeout 1800 --no-guardrails --vae-use-tiling --enable-layerwise-offload
# ready on /v1/models in ~45s; id = /models/checkpoint
$ curl .../v1/chat/completions -d '{"model":"/models/checkpoint","messages":[{"role":"user",
    "content":"What is 2+2? Reply with just the number."}],"max_tokens":96,"temperature":0}'
  finish_reason=stop  usage={prompt_tokens:8, total_tokens:9, completion_tokens:1}
  content=[{'type':'image_url','image_url':{'url':'data:image/png;base64,iVBORw0KGgo...'}}]  # ~1.46M b64 chars
# elicitation attempts:
  response_format={"type":"text"}  ->  IMAGE[1459846 b64 chars]
  modalities=["text"]              ->  HTTP 500 {"error":{"message":"Image generation failed:
                                        'numpy.ndarray' object has no attribute 'save'", ...}}
```
Observed: `completion_tokens=1`, `content` is an `image_url` block (all 3 prompts).
Interpretation: the emitted unit is one image artifact, not a text token stream.
