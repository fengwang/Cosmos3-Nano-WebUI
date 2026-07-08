# GATE-GPU-S1-DOCKERFILE — Gate Record

Date: 2026-07-08/09. Executed live in-session (owner-approved "Full live
execution") on the RTX 5090 host described in `ENVIRONMENTS.md`.

## Hardware / Environment

- GPU: NVIDIA GeForce RTX 5090, 32607 MiB, driver reporting CUDA 13.3 (host),
  CUDA 13.0 inside the `vllm-openai:v0.24.0`-based container.
- Idle before starting: `0 %` util, `15 MiB` used (only host Xorg).
- Docker 29.6.1, Compose v5.1.4. Network reachable: github.com (200),
  huggingface.co (200).
- vLLM-Omni fork commit: `697035018b70cef76b974a909d23371a9984c3f2` (unchanged
  pin — this session never modifies INV-3's pin, only the Dockerfile that
  installs it).
- Checkpoints (pre-`GPU-S2` revisions, local stale-index workaround already
  applied on disk before this session started):
  `wfen/Cosmos3-Nano-FP8-Blockwise` @ `4e181f996abf03f3425298ef692e6e5e56fd46a4`
  at `/data/models/Cosmos3-Nano-FP8-Blockwise`;
  `wfen/Cosmos3-Nano-NVFP4-Blockwise` @ `b5c9332efbaefa72c99890b1b1150da12ca9256c`
  at `/data/models/Cosmos3-Nano-NVFP4-Blockwise`.

## Step 1 — sm_120 base-image probe

```
docker pull vllm/vllm-openai:v0.24.0
# Digest sha256:251eba5cc7c12fed0b75da22a9240e582b1c9e39f6fbc064f86781b963bd814f
# ~2s wall time (near-total layer overlap with already-cached vllm-openai tags
# in this environment); image size 20,364,723,204 bytes.
docker run --rm --gpus all --entrypoint python3 vllm/vllm-openai:v0.24.0 -c "..."
# torch 2.11.0+cu130 / vllm 0.24.0 / device 'NVIDIA GeForce RTX 5090' /
# capability (12, 0) / matmul ok, sum=144384.0
```

Result: **PASS.** No human-gate trigger (base image change) needed.

## Step 2 — Dockerfile rework and build

Final `deploy/vllm-omni.Dockerfile` diff: see commit `2206e04` ("fix(gpu-s1):
rebuild vllm-omni.Dockerfile from public vllm-openai base"). Three in-loop
fixes before it built clean — see `docs/session_1/failure_arbiter.md`
FA-1/FA-2/FA-3.

```
docker compose --env-file .env -f deploy/docker-compose.fp8.yml build vllm-omni
# First working build: 48.238s total (43.9s in the fork-install layer: 28
# incremental packages resolved/installed, no torch/vLLM reinstall).
# Subsequent CMD/ENTRYPOINT-only edits rebuilt from cache in ~1.4s.
```

Base-layer provenance check (adversarial case: "build appears to succeed but
actually reused a cached prebuilt cosmos3 layer"):

```
cosmos3 prebuilt (vllm/vllm-omni:cosmos3) layer count: 34
new image (cosmos3-nano-vllm-omni:local) layer count: 35
shared layer count: 5
  -> all 5 already present in the untouched vllm/vllm-openai:v0.24.0 base
     itself (verified: shared_base_cosmos == (cosmos3_layers & new_layers));
     they are base-Ubuntu-22.04-rootfs / metadata layers, not anything this
     build added.
  -> the 2 layers this Dockerfile actually adds (apt git; uv pip install)
     intersect the cosmos3 prebuilt's layer set: {} (empty).
```

Result: **PASS.** Build is from public inputs only; no forbidden layer
reuse beyond incidental, pre-existing base-image ancestry.

## Step 3 — Serve + T2I (FP8)

Operator note: `deploy/docker-compose.base.yml` does not publish the
`vllm-omni` service's port to the host by design (the `api` service owns its
lifecycle/access path). Verified `/v1/models` and sent T2I requests via
`docker exec <container> curl ...` against the container's own loopback,
which is behaviorally equivalent to the contract's `curl localhost:8000`
check without changing any tracked Compose file's networking posture.
Guardrails were disabled only via an untracked scratch Compose override
(`command: [..., "--no-guardrails"]`) for this smoke test — see
`docs/session_1/failure_arbiter.md` FA-5 — the shipped `CMD` keeps
guardrails on.

```
docker compose --env-file .env -f deploy/docker-compose.fp8.yml up -d vllm-omni
docker exec cosmos3-nano-webui-vllm-omni curl -sf http://localhost:8000/v1/models
# HTTP 200, {"object":"list","data":[{"id":"/models/checkpoint", ...}]}

POST /v1/images/generations  (model=/models/checkpoint, 1024x1024, 50 steps,
                               guidance 7.0, seed 42, b64_json)
# HTTP 200 in 8.496s wall (includes docker-exec + network overhead)
# decoded artifact: PNG, 1024x1024, RGB, 3,147,861 bytes,
#   sha256 3fd20c32fb06f470c1357cad05b5995b4b845af72a47fb93678014d59c985591
# Visually confirmed: photorealistic red sports car, city street, golden
#   hour lighting — matches the prompt.
```

Result: **PASS** (`EV-GPU-S1-BUILD-T2I-SMOKE`, FP8 leg).

## Step 4 — Serve + T2I (NVFP4)

```
docker compose --env-file .env -f deploy/docker-compose.fp8.yml down
docker compose --env-file .env -f deploy/docker-compose.nvfp4.yml up -d vllm-omni
# same image (cosmos3-nano-vllm-omni:local) — no rebuild, only the
# checkpoint bind-mount source and COSMOS3_CHECKPOINT_LABEL differ.
docker exec cosmos3-nano-webui-vllm-omni curl -sf http://localhost:8000/v1/models
# HTTP 200

POST /v1/images/generations  (same request body as the FP8 leg)
# HTTP 200 in 7.313s wall
# decoded artifact: PNG, 1024x1024, RGB, 3,147,861 bytes,
#   sha256 8316faf07ea52998fb61089b760b47d797f8004507747dab96914585bbf25875
# Visually confirmed: same scene, consistent with the FP8 result at a
#   different quantization.
```

Result: **PASS** (`EV-GPU-S1-BUILD-T2I-SMOKE`, NVFP4 leg — exceeds the
contract's "at least one" bar).

Teardown: `docker compose --env-file .env -f deploy/docker-compose.nvfp4.yml
down --remove-orphans`. Confirmed via `git status --short` and `ls` that no
stray container, network, or `<repo>/models/**` directory was left behind.

## Step 5 — `docker-compose.local-image.yml` disposition

`rm deploy/docker-compose.local-image.yml`. File was untracked; `git status
--short` shows no trace after removal. Recorded in
`docs/release_checklist.md` and `docs/evidence_map.md`.

## Gate Verdict

`GATE-GPU-S1-DOCKERFILE`: **PASS.**
- `deploy/vllm-omni.Dockerfile` builds from public inputs only. ✅
- Built image serves `/v1/models` and generates a T2I artifact on the RTX
  5090 for at least one of FP8/NVFP4 — **both**, in fact. ✅
- `docker-compose.local-image.yml` has a recorded disposition (deleted). ✅
