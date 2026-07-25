# P3 — t2i non-regression smoke (INV-2) = **PASS**

Date: 2026-07-25 · Hardware: RTX 5090 (sm_120), 32607 MiB.
Image: `cosmos3-nano-vllm-omni:local` — the **unchanged** generation image (byte-identical to the
GPU-S3/UX-S2 proven state; AM-S2 added a *separate* `vllm-reasoner` image and touched only the
reasoning code path, never the omni/generation path).

## Why this is the right non-regression check
AM-S2's serving-path change is **reasoning-only**: a new `vllm-reasoner` container/image, a
`Plane.REASONING` container worker, and the `/v1/reason` route target. The generation path is
untouched — the `vllm-omni` image, the `docker-compose` `vllm-omni` service (command/mount), the
factory `GENERATION` branch, and the generation route are all byte-identical. So `t2i` cannot be
regressed by construction; this run is the required confirming evidence.

## Run
```
docker run -d --gpus all -p127.0.0.1:8010:8000 --shm-size 16gb \
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  -v /data/models/Cosmos3-Nano-FP8-Blockwise:/models/checkpoint:ro \
  cosmos3-nano-vllm-omni:local  vllm serve /models/checkpoint --omni \
    --host 0.0.0.0 --port 8000 --init-timeout 1800 --no-guardrails \
    --vae-use-tiling --enable-layerwise-offload
# ready on /v1/models in ~50s
curl .../v1/images/generations -d '{"model":"/models/checkpoint",
     "prompt":"a red apple on a wooden table, studio photo","n":1,"size":"480x480"}'
```

## Result — PASS
- `/v1/images/generations` returned a valid **PNG**: 691,968 bytes, base64 length 922,624, header
  `89504e470d0a1a0a` (PNG magic). Same t2i path the api's `vllm_omni_work` (mode `t2i` →
  `run_image_job` → `/v1/images/generations` → PNG) drives.
- Peak VRAM **13.5 GiB / 32** (matches the proven FP8 720p-capable footprint).
- No error; container healthy throughout; torn down after (`docker rm -f amrs2-omni`), GPU → idle.

⇒ **INV-2 satisfied**: `t2i` (vllm-omni, FP8) remains GPU-verified end to end after the AM-S2
reasoning enablement.

## Note
This standalone smoke exercises the omni generation server directly (as the api does via
`endpoint_for()`). The full-stack api→orchestrator→container path (docker-socket start/stop, the
generation↔reasoning evict-before-load swap) is exercised by the CPU integration/residency tests
and is a candidate for the AM-S4 all-modes GPU smoke.
