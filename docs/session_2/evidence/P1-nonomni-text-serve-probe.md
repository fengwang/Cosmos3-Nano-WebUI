# P1 — Non-omni text-serve probe (result: zero-change **FAIL**, bounded fork **required**)

Date: 2026-07-25 · Hardware: RTX 5090 (sm_120), 32607 MiB, GPU idle 18 MiB.
Image: `cosmos3-nano-vllm-omni:local` (the deployed image; vLLM v0.24.0 + `vllm-omni@6970350`).
Checkpoint: `/data/models/Cosmos3-Nano-FP8-Blockwise` (deployed rev `4e181f9`), mounted **read-only**, **no BF16 mount**.

## What was tested (throwaway container, no repo/checkpoint edits)
Plain `vllm serve` **without `--omni`** — the truest test of "serve the quantized
understanding tower as text off the fork":
```
docker run -d --gpus all -p127.0.0.1:8009:8000 --shm-size 16gb \
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  -v /data/models/Cosmos3-Nano-FP8-Blockwise:/models/checkpoint:ro \
  --entrypoint bash cosmos3-nano-vllm-omni:local -c \
  'vllm serve /models/checkpoint --host 0.0.0.0 --port 8000 --max-model-len 8192 --gpu-memory-utilization 0.85'
```
(`--init-timeout` is an omni-only arg → rejected by plain serve; dropped.)

## Result (rubric "loads" gate = FAIL)
- **Arch resolved** under plain serve: `Resolved architecture: Cosmos3ForConditionalGeneration` — the text/LLM arch IS recognized without `--omni`.
- Engine config logged **`quantization=None, quantization_config=None, dtype=torch.bfloat16`** — vLLM did **not** detect the checkpoint's blockwise-FP8 quant.
- Weight load crashed: **`KeyError: 'layers.0.mlp.gate_up_proj.weight_quantizer._amax'`** (`qwen2.py:456 param = params_dict[name]`) → `EngineCore failed to start`. Container exited (1); GPU returned to 18 MiB.

## Root cause
The checkpoint carries **no HF-standard `quantization_config`** in `config.json`
(confirmed: top-level + `transformer/config.json` have no quant keys). Its quant
lives in a separate root `quantization_config.json` (`recipe: fp8_blockwise_mixed`,
blockwise-128×128, `n_quantized: 216`, quantized set `mlp.*`/`mlp_moe_gen.*`) plus a
`transformer/modelopt_state.pt` structural sidecar. So vLLM auto-detect finds no
quant → builds a plain BF16 model whose `params_dict` lacks quantizer params → the
modelopt sidecar tensors (`*.weight_quantizer._amax`/`._scale`) in the safetensors
have no home → KeyError.

The checkpoint's own `load_quantized.py` shows the missing step: build model →
**`mto.restore_from_modelopt_state(model, modelopt_state.pt)`** (installs the
quantizer wrappers) → **then** `load_state_dict(strict=True)`. Plain vLLM LLM
loading skips the restore.

## The pieces already exist (why the fork is bounded, not from-scratch)
- `vllm_omni/quantization/fp8_blockwise_w8a16.py` → **`Fp8BlockwiseW8A16LinearMethod(LinearMethodBase)`**, written **for Cosmos3** (P6-S2): keeps weight resident FP8 (e4m3) + a 2D per-block `weight_scale` grid (`[ceil(rows/128), ceil(cols/128)]`), JIT-dequants per block in `apply()`. Consumes the exact on-disk format. Auto-selected by the `fp8_blockwise_mixed` disk recipe via `fp8_w8a16_selected(model_dir)`.
- **But every call site is on the diffusion/image path** (`vllm_omni/diffusion/model_loader/checkpoint_adapters/*`, `diffusion/models/cosmos3/transformer_cosmos3.py:1100-1110`). There is **no** application of this quant on the vLLM **text/LLM** load path — hence the gap.
- Both forks are **locally editable**: `the local vLLM fork (fengwang/vllm)` (Cosmos3 text model `cosmos3.py`) and `the local vLLM-omni fork (fengwang/vllm-omni)` (the W8A16 method).

## Verdict (against the pre-registered rubric)
- **Zero-change (Option A): REFUTED** — plain non-omni serve cannot load the blockwise-FP8 checkpoint.
- **Feasibility of zero-BF16 FP8 text reasoning: STRONG but UNPROVEN** — the text arch + `lm_head` path loads under plain serve, and a Cosmos3-specific blockwise-FP8 W8A16 `LinearMethod` (resident FP8 + JIT dequant) already exists; the missing piece is a **bounded fork change**: apply that quant method on the text/LLM path (recipe-gated) with the weight-name mapping (`weight_quantizer._scale`→`weight_scale`, consume/ignore `._amax`; handle vLLM's fused `gate_up_proj`/`qkv_proj`). *"Loaded" ≠ "works" — text-output + coherence remain to be proven after the fork change (rubric gates 2-3), and quality is the owner gate (`EV-AM-CHAT-IS-IMAGE`).*
- VRAM for the text tower is **unmeasured** (load failed before allocation).

## Cleanup
`docker rm -f amrs2-textprobe`; GPU back to 18 MiB. No persistent change.
