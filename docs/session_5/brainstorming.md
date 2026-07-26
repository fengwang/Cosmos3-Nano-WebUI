# AM-S5 Brainstorming — Extend + GPU-Verify on NVFP4

Date: 2026-07-26
Risk: high · Routing: branch-and-compare per mode (a/c; kernel fallback) + adversarial verifier + owner per-mode quality gate.
Inputs: `docs/prd.md`, `docs/project_contract.md`, `docs/session_5.md` + `_contract.yaml`, `docs/evidence_map.md` (S-B/S-D, R-03/R-04), `docs/handoff.md` (AM-S4).

## Confirmed intent (interview, owner-approved 2026-07-26)

- **Outcome:** Extend the verified FP8 all-modes design to NVFP4 — add an NVFP4 reasoner (bounded fork, mirroring AM-S2) + action wiring; each mode default-on **only** if its NVFP4 GPU probe *and* the owner's manual quality gate pass, else a recorded **INV-7 limitation**.
- **Shape (owner choice):** **Spike-led** — GPU-probe each mode first, pre-register the rubric, then implement wiring only for modes that clear the technical probe. Agent drives probes; owner runs the final quality gate.
- **Reasoner effort (owner choice):** **Bounded / mirror AM-S2** — reuse the vllm-omni fork's existing NVFP4 blockwise W4A16 method; if no reusable method serves coherent text on sm_120, **stop and record an INV-7 limitation** (NVFP4 = Studio + Action). No new-kernel-from-scratch.
- **Constraint:** Zero-BF16 is absolute (no fallback, ever); FP8 stack untouched (frozen-verified); NVFP4 stays offload-free (Marlin FP4 kernel forbids layerwise offload).
- **Out of scope:** README/`walkthrough.md` (AM-S6); FP8 behavior; schema shape changes (INV-8); diffusers `t2v` (INV-3); checkpoint re-export (NVFP4 already bundles the `action_*` adapters, E-06 refuted); any from-scratch 4-bit kernel.

## Design-space findings (direct inspection)

1. **NVFP4 checkpoint** `Cosmos3-Nano-NVFP4-Blockwise`: `transformer/config.json` → `"quant_algo":"NVFP4"`, `"quant_recipe":"nvfp4_blockwise_mixed_v1"`; `transformer/nvfp4_blockwise_mixed_v1.json` → 216 quantized tensors, `block_scale_dtype: float8_e4m3fn`, `global_scale_dtype: float32`. Ships the LM-serving assets (`transformer/`, `text_tokenizer/`, `chat_template.json`, `tokenizer.json`) like FP8 (E-03 holds for NVFP4).
2. **The fork already has the NVFP4 method:** `vllm_omni/quantization/nvfp4_blockwise.py` — `RECIPE="nvfp4_blockwise_mixed_v1"`, `build_nvfp4_blockwise_w4a16_config()` builds a `ModelOptNvFp4Config` subclass pinned to **`ModelOptNvFp4W4A16LinearMethod`** (Marlin FP4, weight-only, no activation `input_scale`) with **target-inclusion** on MLP projections; fails fast if the build resolves a different method. This is the template AM-S2's FP8 W8A16 method was modeled on.
3. **Fused-vs-unfused target subtlety (decisive):** the fork module targets the **unfused** `.mlp.{gate_proj,up_proj,down_proj}` (omni/diffusion construction path via `transformer_cosmos3.py`). Reasoning needs the **plain-text LM path** (`vllm serve`, no `--omni` — omni serves images, not text, per AM-S1 P3), which **fuses** gate+up → `gate_up_proj`. So — exactly as AM-S2's FP8 patch targeted the fused name — the NVFP4 reasoner needs a deploy patch that **reuses the fork's NVFP4 W4A16 method but targets the fused text-path name** (`language_model.model.layers.N.mlp.{gate_up_proj,down_proj}`), plus any NVFP4 scale/param mapping.
4. **The S-D risk (why we probe):** FP8's reasoner used a JIT-dequant `F.linear` path ("guaranteed-correct on sm_120"); NVFP4 rides the **Marlin FP4 kernel** in the plain-text path — unproven for LM text decode — and 4-bit is the riskier quality case (S-B).
5. **Action / t2i:** no new mechanism. Action = omni video-API `action_mode` `(a2)` (proven on FP8, AM-S3); on NVFP4 it is a *serving probe* on the resident omni model. `t2i` is a mandatory INV-2 non-regress re-check. Both use the **unchanged** NVFP4 omni image.

## Chosen approach — A: separate NVFP4 reasoner image + patch (mirror AM-S2)

- New `deploy/vllm-reasoner-nvfp4.Dockerfile` + `deploy/vllm-reasoner/patch-nvfp4/` registering `--quantization nvfp4_blockwise_w4a16`: a config that reuses the fork's `ModelOptNvFp4W4A16LinearMethod` (via the fork's `Nvfp4BlockwiseW4A16Config` / `build_nvfp4_blockwise_w4a16_config`) but with **fused text-path MLP targeting**, + a `cosmos3.py` twin if NVFP4 tensor→param mapping needs it.
- Wire a `vllm-reasoner` service into `docker-compose.nvfp4.yml` (`--quantization nvfp4_blockwise_w4a16`, no offload, mem-util/max-model-len set); update `Makefile up-nvfp4` to also `stop vllm-reasoner`; set the api `COSMOS3_REASONER_MAX_CONTEXT/OUTPUT` for the nvfp4 reasoner's `--max-model-len`.
- **Only if the reasoner probe PASSes.** If it fails at the bounded ceiling → INV-7 limitation; NVFP4 stack ships Studio + Action, `/v1/reason` errors honestly (no silent BF16), documented for AM-S6.

**Rejected:** *B — parametrize the existing `vllm-reasoner.Dockerfile`* (touches the FP8-frozen reasoner path — blast-radius risk against a frozen stack). *C — INV-7 upfront* (only a probe-failure outcome, not a starting choice).

## Pre-registered probe rubric (technical go/no-go; owner quality gate is separate, INV-6)

- **Reasoning PASS:** non-omni `vllm serve --quantization nvfp4_blockwise_w4a16` starts; MLP projections resolve to `ModelOptNvFp4W4A16LinearMethod` (FP4-resident — log marker + VRAM, no BF16 fallback); `/v1/chat/completions` streams coherent, on-topic text for the fixed prompts; ≤32 GiB, no offload. FAIL → bounded fixes → else INV-7.
- **Action PASS:** resident NVFP4 omni serves all 3 v1 action modes via video-API `action_mode` off quantized-only NVFP4; well-formed trajectories/rollout; no offload. FAIL → INV-7 (NVFP4 action).
- **t2i (INV-2) PASS:** unchanged NVFP4 omni yields a valid PNG off the NVFP4 checkpoint; peak ≈ prior ~18.5 GiB. FAIL → blocks the gate.
- **Fixed reasoning prompts:** `"What is 2+2?"`; `"The sky is typically what color?"`; `"Name three primary colors."`; one multi-step word problem. Coherent = correct/on-topic, not repetition/garbage. Technical PASS ≠ promotion.

**Probe order:** (1) t2i non-regress + action serving (cheap, unchanged omni image); (2) reasoner (the S-D crux).
