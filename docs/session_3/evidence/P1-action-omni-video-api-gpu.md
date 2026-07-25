# P1 — Action via omni video-API `action_mode` (a2): GPU-PROVEN (FP8, zero-BF16)

Date: 2026-07-25 · Session AM-S3 · Hardware: RTX 5090 (sm_120), 32607 MiB, driver 610.43.03.
Image: `cosmos3-nano-vllm-omni:local` (fork `fengwang/vllm-omni@6970350`, base `vllm/vllm-openai:v0.24.0`).
Launch: `vllm serve /models/checkpoint --omni --host 0.0.0.0 --port 8000 --init-timeout 1800
--no-guardrails --vae-use-tiling --enable-layerwise-offload` (the deployed FP8 command).
Checkpoint: `/data/models/Cosmos3-Nano-FP8-Blockwise` (deployed rev `4e181f9`). Guardrails off (local, E-15).
Method: direct HTTP to the omni container (bypassing the api), **shipped example assets** as inputs.

## Rubric outcome (pre-registered in brainstorming.md §5)

- **(a1) openpi WS `/v1/realtime/robot/openpi` — NO-GO for the base checkpoint.** At the pinned commit,
  `ServingRealtimeRobotOpenPI.create_policy_server` returns `None` unless the model config declares a
  `policy_server_config` ("model-specific, provided by the loaded policy model"). The recipe
  (`recipes/cosmos3/Cosmos3-Nano.md`) confirms openpi serves the **separate**
  `nvidia/Cosmos3-Nano-Policy-DROID` checkpoint, not the base Cosmos3-Nano. Reproduces AM-S1's
  "Robot policy not available" — and explains it: wrong abstraction for the base checkpoint.
- **(a2) omni video-API `action_mode` — GO, GPU-PROVEN.** The recipe documents it
  (`forward_dynamics`=sync `POST /v1/videos/sync`; `policy`/`inverse_dynamics`=async `POST /v1/videos`,
  read the top-level `action`); the pipeline (`vllm_omni/diffusion/models/cosmos3/pipeline_cosmos3.py`)
  implements all three modes; serving (`entrypoints/openai/serving_video.py`) returns the predicted
  action as JSON (`VideoAction{data,shape,dtype,raw_action_dim,action_mode,domain_id}`) + optional rollout.
- **(c) in-process `diffusers_action` plane — NOT NEEDED.** (a2) serves all three modes off the resident
  omni model. The `(c)` graft stays dormant (R-11: not a required deletion).

## GPU evidence — all three v1-scope modes, off the quantized-only FP8 checkpoint

| Mode | Embodiment | Endpoint | Input (shipped asset) | Output | Time |
|---|---|---|---|---|---|
| `inverse_dynamics` | av (9-D) | `POST /v1/videos` (async) | `example_action_id_av_0_input.mp4` (61f@10fps), `action_chunk_size=60` | action `[60,9]` bf16; **mean\|Δ\|=0.0154, max\|Δ\|=0.1976** vs `example_action_id_av_0_output.json` | ~27s |
| `forward_dynamics` | agibotworld (29-D) | `POST /v1/videos/sync` | `example_action_fd_agibotworld_first_frame.png` + `action_chunks[0]` (16×29) | valid **621 KB MP4** rollout (ftyp box) | ~5.7s |
| `policy` | agibotworld (29-D) | `POST /v1/videos` (async) | `first_frame.png` + instruction | action `[16,29]` bf16 predicted | ~6s |

**Residency (INV-5):** peak **14396 MiB / 32607** with omni+action resident → action shares the omni
footprint; **no separate action model/plane, no swap** → Studio+Action plane-merge confirmed. Zero BF16
on the path (the checkpoint is quantized-only; `COSMOS3_BASE_ACTION_DIR` graft is unused/dormant).

**Request wrinkles found (for the api wiring):** `prompt` is required non-empty; action modes need
`action_chunk_size` (> 0) — for ID it must match `num_frames-1` (61 frames → chunk 60); `raw_action_dim`
is required for policy/ID; the video input rides `input_reference` (multipart file). All are set by the
api-side adapter, never a request field on our REST surface (INV-8).

## Implication for AM-S3 (supersedes the blueprint + AM-S1's action framing)

Action is served by the **resident omni model** via the video API's `action_mode`:
- **FD** already wired (`vllm_omni_work` → `/v1/videos/sync`); GPU-proven here.
- **policy/ID** need `vllm_omni_work` extended to submit them (async `/v1/videos`) and map the returned
  `action` to the trajectory artifact (`result_meta.trajectory_path` → the existing
  `/v1/jobs/{id}/trajectory` sidecar).
- **No new plane, no diffusers in-process, no loader fix, no fork change, no INV-8 shape change.**
- Retire/redirect `COSMOS3_BASE_ACTION_DIR` (only the dormant `(c)` path referenced it).
