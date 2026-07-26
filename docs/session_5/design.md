# AM-S5 Design — Extend + GPU-Verify on NVFP4

Date: 2026-07-26 · Refs: `proposal.md`, `brainstorming.md`, `evidence/P1`–`P2`, `docs/project_contract.md`.

## Context

FP8 all-modes is proven + default-on via one `make up-fp8` (AM-S4): omni (Studio+Action, plane-merge)
+ a separate `vllm-reasoner` container the orchestrator evict-before-loads. NVFP4 today = Studio only
(no reasoner service). The AM-S5 probes proved NVFP4 serves all three modes off the quantized-only
checkpoint (zero BF16) on sm_120. The template is the FP8 shape; NVFP4 differs in exactly two ways:
(1) the omni command omits `--enable-layerwise-offload` (Marlin FP4 forbids it), and (2) the reasoner's
quant method is `nvfp4_blockwise_w4a16` (Marlin FP4 W4A16) instead of `fp8_blockwise_w8a16`.

## Goals / Non-Goals

**Goals:** `make up-nvfp4` cold-starts all three NVFP4 modes off the quantized-only checkpoint (zero
BF16); a reproducible NVFP4 reasoner image; `t2i` (NVFP4) non-regressed; CPU suite green; schema stable;
FP8 stack byte-unchanged; a per-mode/per-format matrix staged for the owner's NVFP4 quality gate.

**Non-Goals:** README/`walkthrough.md` (AM-S6); FP8 behavior; schema shape (INV-8); diffusers `t2v`
(INV-3); checkpoint re-export (NVFP4 already bundles `action_*`); a from-scratch 4-bit kernel; `webui/**`
(R-12).

## Decisions

- **D1 — Separate NVFP4 reasoner image, not a parametrized FP8 Dockerfile.** New
  `deploy/vllm-reasoner-nvfp4.Dockerfile` + `deploy/vllm-reasoner/patch-nvfp4/`. *Why:* the FP8 reasoner
  image/path is frozen-verified (AM-S2/S4); a build-arg fork risks a blast-radius regression into it.
  Duplication is a 3-file patch + a near-identical Dockerfile — cheap vs. the risk. (Rejected: parametrize.)
- **D2 — Reasoner quant = fused-target `nvfp4_blockwise_w4a16` reusing `ModelOptNvFp4W4A16LinearMethod`.**
  Mirrors AM-S2: a registerable config targeting the FUSED text-path `language_model.model.layers.N.mlp.
  {gate_up_proj,down_proj}` (the fork's `vllm_omni.quantization.nvfp4_blockwise` targets the *unfused*
  omni names), with a `cosmos3.py` sidecar map (`weight_packed→weight`, `weight_block_scale→weight_scale`,
  `weight_global_scale→weight_scale_2`). Heavy imports deferred (no `vllm.config` circular import). GPU-proven (P2).
- **D3 — Reasoner caps mirror FP8:** `--max-model-len 8192 --gpu-memory-utilization 0.85`; api
  `COSMOS3_REASONER_MAX_CONTEXT=7680` / `COSMOS3_REASONER_MAX_OUTPUT=7680` (8192 − 512 chat-template
  headroom), guarded by the existing `test_reasoner_context_cap_*` extended to the nvfp4 stack.
- **D4 — No offload on NVFP4** (omni + reasoner): Marlin FP4 repacks weights on CUDA after load;
  offloading breaks it. Both resident-fit in 32 GiB (omni ~17–18 GiB; reasoner ~26.9 GiB) but **never
  co-reside** — the single-slot FSM evict-before-loads (INV-5), same as FP8.
- **D5 — `make up-nvfp4` cold-starts + stops the reasoner too:** `up -d --no-start` → `stop vllm-omni
  vllm-reasoner` → `start api webui` (mirrors `up-fp8`), so boot never co-loads the two heavy planes.
- **D6 — NVFP4-assets conditioning gap → documented owner decision.** The NVFP4 checkpoint's `assets/`
  lacks the action demo *inputs* FP8 ships (P1); `webui/**` is out of scope (R-12). Record it honestly
  for AM-S6; the operator may add the two inputs to their NVFP4 `assets/`, else the demo is FP8-only.

## Risks / Trade-offs

- **4-bit reasoning quality (S-B/R-03)** — the fused gate/up global scales are MAX-merged (vLLM warning,
  P2). → *Mitigation:* the owner's manual NVFP4 quality gate is the promotion authority (INV-6); coherence
  is proven, quality is the owner's call; default-on waits on PASS (INV-7).
- **Blast-radius bleed into the frozen FP8 stack** — a shared-base or Makefile edit could regress FP8. →
  *Mitigation:* both-stack compose-render tests + `git diff` on `docker-compose.fp8.yml` (forbidden file);
  the reasoner change is a *new* nvfp4-only service + a *new* image, not a shared-base edit.
- **Marlin FP4 perf** — weight-only FP4 has no native sm_120 FP4 GEMM (warning, P2); acceptable for
  reasoning (as W8A16 was for FP8). Note for a perf follow-up, not a gate.

## Migration Plan

1. Land the patch + Dockerfile + compose/Makefile/env + tests (TDD). 2. `make build` the nvfp4 reasoner
image. 3. `make up-nvfp4`; owner runs the NVFP4 per-mode quality gate. 4. Flip default-on for passing
modes (already default-on by wiring; INV-7 honored by the honest-error path if a mode were absent).
**Rollback:** the NVFP4 reasoner is additive; removing its compose service + reverting `up-nvfp4` returns
NVFP4 to Studio-only. FP8 is untouched throughout.

## Open Questions

- Owner NVFP4 quality verdicts: `OWNER-AM-REASON-QUALITY` (NVFP4), `OWNER-AM-ACTION-QUALITY` (NVFP4). —
  staged, pending the owner's run.
- The NVFP4-assets conditioning-input gap (D6): operator adds inputs vs. FP8-only demo. — owner decision.
