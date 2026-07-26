# AM-S5 Proposal — Extend + GPU-Verify on NVFP4

Date: 2026-07-26 · Extracted from `brainstorming.md` + the GPU probes (`evidence/P1`, `P2`).

## Motivation

NVFP4 was the phase's last residual unknown (R-04/S-D: do the 4-bit Blackwell kernels serve the
reasoning/action inference paths on sm_120?). The FP8 all-modes vertical is proven and default-on
(AM-S4). The spike-led probes resolved S-D **positively for all three modes** off the quantized-only
NVFP4 checkpoint, zero BF16:

- **t2i** (Studio): valid PNG, ~17 GiB, non-regressed (INV-2) on the unchanged omni image (P1).
- **Action** (FD/policy/ID): all three via the omni video-API `action_mode`, ~18.2 GiB, Studio+Action
  plane-merge (P1).
- **Reasoning**: coherent text off the FP4 understanding tower via a **bounded fork patch mirroring
  AM-S2** — a registerable `--quantization nvfp4_blockwise_w4a16` reusing vLLM's
  `ModelOptNvFp4W4A16LinearMethod` (Marlin FP4 W4A16), ~26.9 GiB, streaming (P2).

So no mode requires an INV-7 limitation on the *technical* axis. Promotion to default-on still waits on
the owner's per-mode NVFP4 quality gate (INV-6/S-B) — the fused-global-scale MAX-merge (P2) is the 4-bit
factor to eyeball.

## Specific changes agreed

1. **Add an NVFP4 reasoner** — a *separate* reproducible image + patch (not a parametrization of the
   FP8-frozen reasoner), wired as a `vllm-reasoner` service in `docker-compose.nvfp4.yml`, serving the
   quantized understanding tower via `--quantization nvfp4_blockwise_w4a16` (no `--omni`, no offload).
2. **Extend the AM-S4 all-modes orchestration to NVFP4** — `make up-nvfp4` cold-starts all three modes;
   the Makefile stops the new `vllm-reasoner`; api reasoner context caps set for the NVFP4 reasoner
   (mirror FP8's 7680 ≤ `--max-model-len 8192`).
3. **Guard the frozen FP8 stack** — deterministic both-stack compose-render tests so an NVFP4 (or shared
   base) edit cannot regress FP8.
4. **Record the NVFP4-assets conditioning gap** (P1) as an explicit owner decision (the NVFP4 checkpoint
   ships action outputs but not the demo conditioning inputs FP8 ships) — a doc note for AM-S6, no repo
   binary, `webui/**` untouched (R-12).

## Capabilities

**New:**
- `nvfp4-reasoner-serving` — a zero-BF16 NVFP4 W4A16 text reasoner (image + vLLM patch + compose
  service) serving the quantized understanding tower on sm_120 via the Marlin FP4 weight-only kernel.

**Modified:**
- `nvfp4-all-modes-wiring` — `docker-compose.nvfp4.yml` + `Makefile` `up-nvfp4` + api reasoner caps
  extended from Studio-only to all three modes (default-on for modes that pass the owner gate, INV-7),
  with no BF16 mount and the residency safety net preserved (INV-5); the FP8 stack unchanged.

## Impact

- **Code/config:** `deploy/docker-compose.nvfp4.yml` (add reasoner service + api caps), new
  `deploy/vllm-reasoner-nvfp4.Dockerfile` + `deploy/vllm-reasoner/patch-nvfp4/{nvfp4_blockwise_w4a16_vllm,quantization__init__,cosmos3}.py`,
  `Makefile` (`up-nvfp4` stop reasoner), `.env.example` (NVFP4 all-modes note, still zero-BF16). **No api
  Python change expected** — the reasoner is a container the existing orchestrator already drives (the
  base already carries `COSMOS3_VLLM_REASONER_URL`/`_CONTAINER`).
- **Tests:** `tests/deploy/` NVFP4 all-modes wiring + reasoner-context-cap + FP8-non-regression renders.
- **Docs:** `docs/model_setup.md` (NVFP4 per-mode status + reasoner), `evidence_map.md` (S-B/S-D,
  R-03/R-04), `risk_register.md`, `eval_seed_cases.md`, `handoff.md`.
- **APIs/deps:** `schemas/openapi.json` unchanged (INV-8); no new production dependency (the reasoner
  image reuses the pinned omni fork + a COPY-patch, like AM-S2).
