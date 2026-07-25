# P2 — Fork W8A16 text serve (result: **zero-BF16 FP8 reasoning PROVEN**)

Date: 2026-07-25 · Hardware: RTX 5090 (sm_120), 32607 MiB · GPU idle 18 MiB before.
Image: deployed `cosmos3-nano-vllm-omni:local` (vLLM v0.24.0 + `vllm-omni@6970350`),
with three **bind-mounted** edited Python files (no rebuild). Checkpoint:
`/data/models/Cosmos3-Nano-FP8-Blockwise` (rev `4e181f9`), read-only, **NO BF16 mount**.

## The change (prototype — bind-mounted over the image; to be ported to the pinned forks)
1. **Register a `--quantization fp8_blockwise_w8a16` method** in vLLM
   (`vllm/model_executor/layers/quantization/`): a new `fp8_blockwise_w8a16_vllm.py`
   defining `Fp8BlockwiseW8A16Config(QuantizationConfig)` whose `get_quant_method`
   returns the (reused) `vllm_omni…Fp8BlockwiseW8A16LinearMethod` for the LM MLP
   targets `language_model.model.layers.N.mlp.{gate_up_proj,down_proj}` (fused +
   standalone) and `UnquantizedLinearMethod` (BF16) for everything else; registered
   inline at the end of `quantization/__init__.py`.
2. **Mapper scale-mapping** in `vllm/model_executor/models/cosmos3.py`: add
   `".weight_quantizer._scale" -> ".weight_scale"` and drop `".weight_quantizer._amax"`.
3. Reused vllm-omni's existing `Fp8BlockwiseW8A16LinearMethod` (resident FP8 + JIT
   128×128 per-block dequant). Copies of all three edited files: `docs/session_2/evidence/fork_prototype/`.

Serve (no `--omni`): `vllm serve /models/checkpoint --host 0.0.0.0 --port 8000
--max-model-len 8192 --gpu-memory-utilization 0.85 --quantization fp8_blockwise_w8a16`.

## Load evidence (W8A16 applied to all 72 LM MLP targets)
`process_weights_after_loading` residency + scale-grid assertions PASSED, e.g.:
- `gate_up_proj`: `dtype=torch.float8_e4m3fn elem=1 shape=(24576, 4096) scale=(192, 32) block=[128,128]` (fused gate+up scale merged correctly: 24576/128=192, 4096/128=32).
- `down_proj`: `shape=(4096, 12288) scale=(32, 96)` (4096/128=32, 12288/128=96).

Ready on `/v1/models` in ~60 s. Peak VRAM **26.1 GiB / 32** at `--gpu-memory-utilization 0.85`
(mostly KV-cache pre-alloc; tunable — model weights are far smaller).

## Coherence probes (pre-registered rubric — all TEXT, not image)
| prompt | finish_reason | output |
|---|---|---|
| "What is 2+2? Reply with just the number." | stop | `4` |
| "In one sentence, what color is a clear daytime sky?" | stop | `A clear daytime sky is typically blue.` |
| "List three primary colors, comma-separated." | stop | `Red, Blue, Yellow` |
| "train 60 km in 45 min, avg speed km/h? show calc" | stop | correct multi-step: `60 km / 0.75 h = 80 km/h` |

Streaming (`stream:true`, SSE): proper `data: {…delta.content…}` chunks →
`finish_reason:stop` → `[DONE]` (WebUI/`VllmReasonerStream`-compatible).

## Verdict (against P1's pre-registered rubric)
- **Loads** ✓ (arch `Cosmos3ForConditionalGeneration`; FP8 blockwise weights resident via W8A16; **no BF16 mount**).
- **Emits text** ✓ (token stream, `finish_reason=stop`, not an `image_url`).
- **Coherent** ✓ (4/4 on-topic, incl. correct multi-step arithmetic).
- ⇒ **FEASIBILITY PASS — zero-BF16 FP8 reasoning is achievable.** Risk **R-15 → GO** (no BF16 exception needed).

## Honesty / caveats (loaded+coherent ≠ owner-quality-verified)
- This is a **prototype on the deployed image** (bind-mounted edits over vLLM v0.24.0 +
  vllm-omni 6970350). It must be **ported to the local forks** (`fengwang/vllm`,
  `fengwang/vllm-omni`) and **pinned** into a reproducible reasoner image (NFR-5).
- Output **quality** remains the owner's manual gate (`OWNER-AM-REASON-QUALITY`, INV-6) —
  coherence here is the feasibility bar, not the quality verdict.
- `t2i` non-regression (INV-2) still to be re-run after the serving-path wiring lands.
- The W8A16 method dequantizes the full weight per forward (no fused kernel) — correct on
  sm_120 but not perf-optimal; acceptable for reasoning, notable for `AM-S3`/perf follow-up.

## Owner quality gate — OWNER-AM-REASON-QUALITY = **PASS** (2026-07-25)
The owner (Feng) ran custom reasoning prompts against this live serving path
(`127.0.0.1:8009`, the exact fork-patched FP8-blockwise reasoner) and judged the
text-inference quality **"pretty good — a big PASS."** With the recorded end-to-end
run above, this satisfies INV-6 (verified = recorded run **and** owner quality PASS)
for **FP8 reasoning**. NVFP4 remains AM-S5.
