# P2 — NVFP4 reasoner (W4A16 text serve) = **zero-BF16 NVFP4 reasoning PROVEN (technical)**

Date: 2026-07-26 · Session AM-S5 · Hardware: RTX 5090 (sm_120), 32607 MiB · GPU idle 18 MiB before/after.
Image: deployed `cosmos3-nano-vllm-omni:local` (vLLM v0.24.0 + `vllm-omni@6970350`) with **three
bind-mounted edited Python files** (prototype, no rebuild — ported to a reproducible image in the impl).
Checkpoint: `/data/models/Cosmos3-Nano-NVFP4-Blockwise` (rev `5514c42b…`), read-only, **NO BF16 mount**.

## The change (prototype — mirrors AM-S2's FP8 patch; files in `fork_prototype_nvfp4/`)
1. **Register `--quantization nvfp4_blockwise_w4a16`** (`nvfp4_blockwise_w4a16_vllm.py`): a
   `Nvfp4BlockwiseW4A16Config(QuantizationConfig)` whose `get_quant_method` returns vLLM's
   `ModelOptNvFp4W4A16LinearMethod` (Marlin FP4 W4A16, weight-only) for the **FUSED** LM MLP targets
   `language_model.model.layers.N.mlp.{gate_up_proj,down_proj}` and `UnquantizedLinearMethod` (BF16)
   elsewhere. Heavy imports (`modelopt`, `linear`) are deferred into `get_quant_method`/`_base_config`
   (only `base_config` at module top) so registering at `quantization/__init__` time cannot trigger a
   `vllm.config` circular import (the first prototype hit exactly that — fixed).
2. **NVFP4 scale mapping** (`cosmos3.py`): map the on-disk ModelOpt-NVFP4 sidecars to the method's param
   names — `.weight_packed→.weight`, `.weight_block_scale→.weight_scale`,
   `.weight_global_scale→.weight_scale_2` (the AM-S5 analog of AM-S2's `.weight_quantizer._scale→
   .weight_scale`). Everything else (flat→nested layout, drop the `_moe_gen` gen tower, attn renames,
   `lm_head`, `secondary_weights`) is byte-identical to the FP8 reasoner's `cosmos3.py`.
3. Registered inline in a stock-`__init__`+append (`nvfp4_reg_block.py`).

Serve (no `--omni`): `vllm serve /models/checkpoint --served-model-name cosmos3-reasoner
--max-model-len 8192 --gpu-memory-utilization 0.85 --quantization nvfp4_blockwise_w4a16`.

## Load evidence (W4A16 FP4-resident on the understanding tower)
- `AM-S5: registered --quantization nvfp4_blockwise_w4a16` ✓
- `modelopt.py: Detected ModelOpt NVFP4 checkpoint (quant_algo=W4A16_NVFP4)` → `AM-S5: built ...
  method=ModelOptNvFp4W4A16LinearMethod` ✓ (the 108 UND MLP targets loaded FP4-packed; forbidden set —
  attn/lm_head/norm/embed — stayed BF16).
- `marlin.py: Your GPU does not have native support for FP4 ... Weight-only FP4 ... Marlin kernel` —
  sm_120 serves via Marlin FP4 weight-only (as NVFP4 t2i does). Ready on `/v1/models` in ~96s.
- Peak VRAM **26.9 GiB / 32** at `--gpu-memory-utilization 0.85` (KV-cache-dominated; the FP4 weights are
  far smaller — same profile as the FP8 reasoner's 26.1 GiB). No offload.
- **⚠ Accuracy note (owner gate):** `modelopt.py:1362 In W4A16_NVFP4 linear, the global weight scale
  (weight_scale_2) differs across fused parallel layers` — vLLM merges the fused gate/up global scales by
  MAX (a warning, not a failure). A possible 4-bit quality factor; `OWNER-AM-REASON-QUALITY` (NVFP4) judges it.

## Coherence probes (pre-registered rubric — all TEXT, temperature 0)
| prompt | finish | output |
|---|---|---|
| "What is 2+2? Reply with just the number." | stop | `4` |
| "In one sentence, what color is a clear daytime sky?" | stop | `A clear daytime sky is blue.` |
| "List three primary colors, comma-separated." | stop | `Red, Blue, Yellow` |
| "train 60 km in 45 min, avg speed km/h? show calc" | (len) | correct multi-step: formula → `45 min = 0.75 h` → (80 km/h) |
| shipped `example_reasoning_prompt.json` (subtask plan) | (len) | coherent structured plan |

Streaming (`stream:true`, SSE): proper `data: {…delta.content…}` chunks (`"Hello"`, `"!"`) →
WebUI/`VllmReasonerStream`-compatible.

## Verdict (against the pre-registered rubric)
- **Loads** ✓ (arch `Cosmos3ForConditionalGeneration`; NVFP4 W4A16 FP4-resident; **no BF16 mount**).
- **Emits text** ✓ (token stream, `finish_reason=stop`, not an image).
- **Coherent** ✓ (on-topic incl. correct multi-step arithmetic — matches AM-S2's FP8 result shape).
- ⇒ **TECHNICAL PASS — zero-BF16 NVFP4 reasoning is achievable** via the bounded fork patch (mirror AM-S2).
  Risk **R-04 (reasoning) / S-D → resolved-feasible**; the bounded-effort ceiling was not hit.

## Honesty / caveats (loaded+coherent ≠ owner-quality-verified)
- **Prototype on the deployed omni image** (bind-mounted edits). Impl ports these to a reproducible
  `deploy/vllm-reasoner-nvfp4.Dockerfile` + `deploy/vllm-reasoner/patch-nvfp4/` (NFR-5), mirroring the
  FP8 reasoner image.
- **Output quality is the owner's manual gate** (`OWNER-AM-REASON-QUALITY`, NVFP4, INV-6 / S-B) — coherence
  here is the feasibility bar, not the quality verdict. The fused-scale MAX-merge (above) is the specific
  4-bit thing to eyeball. Default-on for NVFP4 reasoning waits on that PASS (INV-7).

## Owner quality gate — OWNER-AM-REASON-QUALITY (NVFP4) = **PASS** (2026-07-26)
The owner (Feng) ran the live `make up-nvfp4` container and exercised the WebUI **Reasoning** tab — the
text-inference quality was judged **very good**, and the 4-bit fused-scale MAX-merge (the flagged watch item)
did **not** degrade it perceptibly. With the recorded end-to-end run above, INV-6 is satisfied (recorded run
**and** owner quality PASS) → **NVFP4 reasoning is GPU-verified**; default-on holds (INV-7). Both FP8 (AM-S2)
and NVFP4 (AM-S5) zero-BF16 reasoning are now owner-PASSed.
