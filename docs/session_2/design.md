# AM-S2 Design — Zero-BF16 FP8 Reasoning (as built)

Date: 2026-07-25. Full exploration + approaches in `brainstorming.md`; this is the as-built
architecture + decisions. Evidence: `evidence/P1–P3`.

## Context
AM-S1 proved omni chat serves images, not text (R-15): zero-BF16 reasoning had no proven path. The
owner hardened INV-4 to absolute (no BF16 at all) and pre-authorized forking vLLM. Byte probes (P1)
showed the quantized checkpoint's only FP8 tensors are the 216 LM MLP projections
(`layers.*.mlp.{gate,up,down}_proj`); attention, `lm_head`, `embed_tokens`, norms, and the whole
visual tower are BF16. The blocker: vLLM doesn't auto-detect the modelopt blockwise-FP8 quant (it's
in a side `quantization_config.json` + `modelopt_state.pt`, not `hf_quant_config.json`).

## Goals / Non-Goals
- **Goals:** `/v1/reason` serves coherent text off the quantized-only FP8 checkpoint (zero BF16),
  GPU-verified + owner quality PASS; `t2i` non-regressed; CPU green; API shape stable.
- **Non-Goals:** NVFP4 reasoning (AM-S5); action (AM-S3); the clean default-on merge + legacy cleanup
  (AM-S4); a fused W8A16 kernel; the full-stack api-orchestrated swap as a single GPU run.

## Decisions
- **D1 — Serve the quantized understanding tower via a registered vLLM quant method.** A small
  `fengwang/vllm` fork registers `--quantization fp8_blockwise_w8a16`, whose `get_quant_method`
  applies the *existing* vllm-omni `Fp8BlockwiseW8A16LinearMethod` (resident FP8 + JIT 128×128
  dequant) to the LM MLP targets and `UnquantizedLinearMethod` (BF16) elsewhere; `cosmos3.py` maps
  `weight_quantizer._scale`→`weight_scale`. Rejected: stock `--quantization modelopt` (config not
  found, P1); a bundled BF16 reasoner (owner: no BF16); a from-scratch kernel (the method existed).
  Key subtlety: vLLM **fuses** gate+up→`gate_up_proj`, so the target regex matches the *fused* name.
- **D2 — Reasoner as its own container residency plane.** `container_reasoning_spec` +
  `ContainerPlaneWorker` (mirrors the omni plane); the factory REASONING branch builds it;
  `VllmReasonerStream` targets the reasoner container URL. The single-slot FSM (`manager.py`) is
  unchanged → evict-before-load vs generation is preserved (INV-5). Rejected: api subprocess (keeps
  torch/vLLM/`WITH_REASONING` in the api image); omni plane-merge (omni chat is image-bound).
- **D3 — Reproducible image via a vendored COPY-patch** (`deploy/vllm-reasoner.Dockerfile` +
  `deploy/vllm-reasoner/patch/`) over the omni-image lineage; the fork commit is pinned in AM-S4.

## Risks / Trade-offs
- [W8A16 dequantizes the full weight per forward — perf] → correct on sm_120; acceptable for
  reasoning; a fused-kernel follow-up is possible. Mitigation: none needed for correctness.
- [Reasoner ~26 GiB (KV at 0.85 util) vs omni ~13.5 GiB — OOM if co-resident] → they never
  co-reside (evict-before-load, INV-5); no plane-merge adopted.
- [api edge context-cap uses the char heuristic (no tokenizer mount)] → conservative-safe fallback
  (D-8); the reasoner's `--max-model-len` is the hard cap. → AM-S4 mount refinement.
- [Dormant subprocess reasoning code (R-11)] → left in place (not a required deletion); AM-S4 cleanup.
- [Fork commit uncommitted → reproducibility (NFR-5)] → vendored COPY-patch now; pin the public fork in AM-S4.

## Migration Plan
Transitional now (AM-S2): fp8 stack gains a `vllm-reasoner` service; `make up-fp8` reasoning works
zero-BF16. AM-S4 finalizes: commit/pin the fork, switch the Dockerfile to a pinned fork install,
remove the legacy BF16 overlay + `WITH_REASONING` + dormant subprocess path, and run the full-stack
all-modes GPU smoke. Rollback: revert the AM-S2 diff; the legacy overlay path is untouched.

## Open Questions
- Pin: which public `fengwang/vllm` commit (after the owner pushes)? → AM-S4.
- NVFP4: does the same pattern (register the `nvfp4_blockwise` W4A16 method for the text path) hold? → AM-S5.
- Should the api mount the checkpoint's tokenizer subset for a token-accurate edge cap? → AM-S4.
