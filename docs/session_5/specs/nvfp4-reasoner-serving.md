# Capability: nvfp4-reasoner-serving

Zero-BF16 NVFP4 W4A16 text reasoning served off the quantized-only NVFP4 checkpoint's understanding
tower, mirroring the AM-S2 FP8 reasoner. GPU-proven `docs/session_5/evidence/P2`.

## ADDED Requirements

### Requirement: NVFP4 W4A16 reasoner image is reproducible from the repo
The repo SHALL build an NVFP4 reasoner image from a repo Dockerfile + a vendored vLLM patch (no manual
step, no committed weights), distinct from the frozen FP8 reasoner image so the FP8 path is untouched
(NFR-5, INV-1, blast radius).

#### Scenario: NVFP4 reasoner Dockerfile + patch exist and are self-contained
- **WHEN** `deploy/vllm-reasoner-nvfp4.Dockerfile` is inspected
- **THEN** it builds on the same pinned `vllm-omni` fork ref as the FP8 reasoner, COPYs the three
  repo-root-relative patch files under `deploy/vllm-reasoner/patch-nvfp4/`, and its default `CMD`/serve
  uses `--quantization nvfp4_blockwise_w4a16` with **no** `--omni` and **no** `--enable-layerwise-offload`.

#### Scenario: no weight/secret/private-path committed
- **WHEN** the `make scan` weight-copy + private-ref scan runs over `deploy/`
- **THEN** it reports clean (the patch is Python only; the checkpoint is an operator-supplied read-only mount).

### Requirement: the reasoner serves TEXT off the FP4 understanding tower with zero BF16
`vllm serve <nvfp4-ckpt> --quantization nvfp4_blockwise_w4a16` (no `--omni`) SHALL load the LM MLP
projections FP4-resident via `ModelOptNvFp4W4A16LinearMethod` and answer `/v1/chat/completions` with
coherent, streaming text, with no BF16 base mounted.

#### Scenario: registers and loads W4A16 (GPU, recorded)
- **WHEN** the NVFP4 reasoner serves the quantized-only checkpoint
- **THEN** the log shows the `nvfp4_blockwise_w4a16` registration and `method=ModelOptNvFp4W4A16LinearMethod`
  on the fused `language_model.model.layers.*.mlp.{gate_up_proj,down_proj}` targets, no BF16 mount, peak
  VRAM ≤ 32 GiB with no layerwise offload (evidence P2).

#### Scenario: emits coherent text (pre-registered rubric)
- **WHEN** the fixed prompts (`2+2`, sky color, primary colors, the 60 km/45 min word problem) are sent
- **THEN** each returns on-topic text with `finish_reason=stop` (not an image, not repetition/garbage),
  and streaming yields proper SSE `delta.content` chunks (evidence P2).

### Requirement: the reasoner's serving path carries no BF16 and is a separate residency plane
The NVFP4 reasoner SHALL serve off the SAME quantized checkpoint as generation (one download) and be a
separate container plane the orchestrator evict-before-loads vs generation (INV-4, INV-5).

#### Scenario: never co-resident with omni
- **WHEN** a reasoning request follows a generation request on NVFP4
- **THEN** the single-slot FSM evicts generation before loading the reasoner (peaks stay ≤ 32 GiB; the two
  heavy planes never co-reside), exactly as on FP8.

## Notes (owner gate — not a deterministic scenario)

Promotion of NVFP4 reasoning to default-on requires the owner's manual quality PASS
(`OWNER-AM-REASON-QUALITY`, NVFP4, INV-6 / S-B); the fused-global-scale MAX-merge (P2) is the 4-bit
quality factor to judge. Technical coherence ≠ the quality verdict.
