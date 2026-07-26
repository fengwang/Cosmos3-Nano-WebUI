# P1 — NVFP4 t2i non-regress (INV-2) + action (all 3 modes) = PASS

Date: 2026-07-26 · Session AM-S5 · Hardware: RTX 5090 (sm_120), 32607 MiB, driver 610.43.03.
Image: **unchanged** `cosmos3-nano-vllm-omni:local` (fork `fengwang/vllm-omni@6970350`), NVFP4 command
(`--omni --no-guardrails --vae-use-tiling`, **NO `--enable-layerwise-offload`** — Marlin FP4 kernel
forbids it). Checkpoint: `/data/models/Cosmos3-Nano-NVFP4-Blockwise` (public `wfen/…` rev
`5514c42b…`, quantized-only). Guardrails off (local, E-15). GPU idle 18 MiB before/after.

Container: `docker run -d --gpus all --name ams5-omni -p127.0.0.1:8020:8000 --shm-size 16gb
-e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True -v <nvfp4>:/models/checkpoint:ro
cosmos3-nano-vllm-omni:local vllm serve /models/checkpoint --omni --host 0.0.0.0 --port 8000
--init-timeout 1800 --no-guardrails --vae-use-tiling`. Ready on `/v1/models` in ~50s; resident ~17.1 GiB.

## t2i (Studio) — GPU-AM-T2I-NOREGRESS (NVFP4) = PASS
`POST /v1/images/generations {"prompt":"a red apple on a wooden table, studio photo","size":"480x480"}`
→ HTTP 200, valid **PNG** 691,968 bytes (magic `89504e470d0a1a0a`). Peak VRAM ~17.1 GiB / 32607.
The generation path is byte-unchanged from the GPU-S3/UX-S2-proven NVFP4 t2i (INV-2 held); the AM-S5
change is a *separate* reasoner image, never the omni/generation path.

## Action (all 3 v1-scope modes) — GPU-AM-ACTION-NVFP4 = PASS
Driven through the **real production wiring** (`engines.vllm_omni.work.vllm_omni_work` →
`run_action_job`/`run_forward_dynamics_job` → `UrllibVideoTransport` → the live NVFP4 omni server),
`base_url=http://127.0.0.1:8020`, `COSMOS3_CHECKPOINT_LABEL=nvfp4`. Harness:
`docs/session_5/evidence/fork_prototype_nvfp4/probe_action_nvfp4.py`.

| Mode | Embodiment | Path | Artifact (real WorkResult) | meta |
|---|---|---|---|---|
| `forward_dynamics` | agibotworld (29-D) | `/v1/videos/sync` (sync) | MP4 **628,103 B** (ftyp `00000020 66747970`) | precision=nvfp4 |
| `policy` | agibotworld (29-D) | `/v1/videos` (async) | MP4 **659,538 B** + trajectory sidecar **[16,29]** | precision=nvfp4, action_mode=policy |
| `inverse_dynamics` | av (9-D) | `/v1/videos` (async) | trajectory JSON **[60,9]** (7,510 B) | precision=nvfp4, action_mode=inverse_dynamics |

Peak VRAM **18,190 MiB / 32607** with omni+action resident — action rides the **same resident omni
model** (Studio+Action plane-merge, `Plane.GENERATION`), no extra plane, no swap, no offload. Zero BF16
(the checkpoint is quantized-only). Matches the FP8 AM-S3 result shape exactly; only the format differs.

## Finding — NVFP4 checkpoint `assets/` lacks the action conditioning inputs (demo-UX gap)
The NVFP4 checkpoint ships action **outputs** (`nvfp4-forward_dynamics.mp4`, …) + `example_action_*.json`
but **not** the conditioning **inputs** FP8 ships and the WebUI "Run demo" references at
`/models/checkpoint/assets/…` (`webui/components/action-viewer/demoBody.ts`):
`example_action_fd_agibotworld_first_frame.png` (policy/FD) and `example_action_id_av_0_input.mp4` (ID).
So on the NVFP4 stack the Action tab's **"Run demo"** would 422 (missing conditioning). For this
technical probe the conditioning was taken from the FP8 `assets/` (same physical media). This is an
external-checkpoint data asymmetry (not a repo code bug); recorded as an owner decision / AM-S6 doc note
(the operator can add those two inputs to the NVFP4 `assets/`, or the demo is FP8-only). No binary is
committed by this session (INV-1).

**Update (2026-07-26): gap resolved.** The owner added the 3 missing action inputs
(`example_action_fd_agibotworld_first_frame.png`, `example_action_id_av_0_input.mp4`,
`example_action_id_av_1_input.mp4`, byte-identical from FP8) to `wfen/Cosmos3-Nano-NVFP4-Blockwise` in
commit `e59dcff…` (assets-only; weights unchanged). The NVFP4 Action "Run demo" now works with shipped inputs.

## Owner quality gate — OWNER-AM-ACTION-QUALITY (NVFP4) = **PASS** (2026-07-26)
The owner (Feng) ran the live `make up-nvfp4` container and exercised the WebUI **Action** tab across all
options — all functions worked as expected and output quality was judged **very good**. With the recorded
GPU run above, INV-6 is satisfied (recorded run **and** owner quality PASS) → **action is GPU-verified on
NVFP4**; default-on holds (INV-7).
