# P2 — Action e2e via the real api wiring + t2i non-regression (FP8, GPU)

Date: 2026-07-25 · Session AM-S3 · RTX 5090 (sm_120), 32607 MiB, driver 610.43.03.
Omni image: `cosmos3-nano-vllm-omni:local` (fork `@6970350`), deployed FP8 command
(`--omni --no-guardrails --vae-use-tiling --enable-layerwise-offload`). Checkpoint:
`/data/models/Cosmos3-Nano-FP8-Blockwise` (deployed rev `4e181f9`), quantized-only.

Unlike P1 (raw HTTP probes), P2 drives the **actual production code** — `engines.vllm_omni.work.vllm_omni_work`
→ `run_action_job`/`run_forward_dynamics_job` → the stdlib `UrllibVideoTransport` → the live omni server —
with the checkpoint's shipped example assets, writing artifacts through the real `jobs.artifacts` helpers.
This verifies MY wiring (request build + response parse + artifact contract), not just the server.

## GPU-AM-ACTION-FP8 — all three v1-scope modes, real wiring, PASS

| Mode | Embodiment | Path | Artifact (real `WorkResult`) | Contract |
|---|---|---|---|---|
| `forward_dynamics` | agibotworld (29-D) | `vllm_omni_work` → `/v1/videos/sync` | `verify-fd.mp4` 614 KB (ftyp), `num_frames=17` | rollout MP4 (anchor) |
| `inverse_dynamics` | av (9-D) | `vllm_omni_work` → `run_action_job` → `/v1/videos` | `verify-inverse_dynamics.json` `[60,9]` (7355 B), `meta.action_mode=inverse_dynamics`, **no** sidecar | artifact IS the trajectory |
| `policy` | agibotworld (29-D) | `vllm_omni_work` → `run_action_job` → `/v1/videos` | `verify-policy.mp4` 629 KB (ftyp) + `[16,29]` trajectory JSON **sidecar** (`meta.trajectory_path`), `meta.action_mode=policy` | rollout MP4 + trajectory sidecar |

The ID/policy artifact contract matches the `(c)` `gen_worker._encode_action_reply` shape the WebUI action
tab targets (ID → trajectory JSON artifact; policy → MP4 + trajectory sidecar via `/v1/jobs/{id}/trajectory`),
so the public API surface is unchanged (INV-8; `openapi.json` diff clean).

## GPU-AM-T2I-NOREGRESS — PASS

`vllm_omni_work` t2i (480×480) through the same live omni image → `verify-t2i.png` 691 KB, valid PNG magic.
INV-2 held: the t2i path (images API) is byte-unchanged by AM-S3 — the change is additive to the action
predict modes. (P1 also produced a valid 480×480 PNG in the earlier spike run.)

## Residency (INV-5) & zero-BF16 (INV-4)

Peak **14.3 GiB / 32** with omni resident during action inference — action rides the **same resident omni
model** (no separate action plane, no swap → Studio+Action plane-merge). Clean **18 MiB** idle after
`docker rm -f` (no leak). All inputs/weights are the quantized-only FP8 checkpoint; **no BF16 base**
anywhere on the path (`docker compose -f deploy/docker-compose.fp8.yml config` shows only `/models/checkpoint`).

## Owner quality gate (OWNER-AM-ACTION-QUALITY) — PASS

✅ **Feng, 2026-07-25.** The owner ran all three v1-scope modes through the WebUI Action tab — agibotworld
`policy` and `forward_dynamics` (3D URDF viewer + rollout) and av `inverse_dynamics` (authoritative 2D
trajectory plots) — using the checkpoint's shipped example inputs, and judged the output quality good
across all options. INV-6 satisfied (recorded GPU run **and** owner quality PASS) → **action is
GPU-verified on FP8**. Supporting evidence: ID(av) matches the shipped
`example_action_id_av_0_output.json` within mean|Δ|=0.015 / max|Δ|=0.198 (P1); FD/policy produce valid
rollouts + trajectories. Default-on remains the AM-S4 gate (INV-7).
