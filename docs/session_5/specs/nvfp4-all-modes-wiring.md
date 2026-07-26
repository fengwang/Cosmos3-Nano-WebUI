# Capability: nvfp4-all-modes-wiring

`make up-nvfp4` brings up Studio + Reasoning + Action off the quantized-only NVFP4 checkpoint (zero BF16,
no offload), extending the AM-S4 FP8 orchestration to NVFP4. The FP8 stack is unchanged.

## MODIFIED Requirements

### Requirement: the NVFP4 stack renders an all-modes, zero-BF16 wiring
`docker compose -f deploy/docker-compose.nvfp4.yml config` SHALL render api + webui + vllm-omni **+
vllm-reasoner**, with the NVFP4 reasoner serving `--quantization nvfp4_blockwise_w4a16` off the same
quantized checkpoint mount, and **no** BF16 base mount anywhere.

#### Scenario: nvfp4 config shows the reasoner and no BF16
- **WHEN** `docker compose -f deploy/docker-compose.nvfp4.yml config` is rendered
- **THEN** it lists a `vllm-reasoner` service whose command contains `nvfp4_blockwise_w4a16` and whose only
  model mount is the NVFP4 checkpoint; no path resembling a BF16 base (`Cosmos3-Nano/transformer`, `/models/base`) is mounted.

#### Scenario: NVFP4 omni stays offload-free
- **WHEN** the rendered nvfp4 `vllm-omni` command is inspected
- **THEN** it does **not** contain `--enable-layerwise-offload` (Marlin FP4 constraint), unlike the FP8 stack.

### Requirement: `make up-nvfp4` cold-starts without co-loading the heavy planes
`up-nvfp4` SHALL create-but-not-start every container, stop the heavy GPU planes (omni **and** reasoner),
then start only api + webui — so boot never co-loads two heavy planes (INV-5), mirroring `up-fp8`.

#### Scenario: up-nvfp4 stops both heavy planes
- **WHEN** the `up-nvfp4` recipe is inspected
- **THEN** it runs `up -d --no-start`, then `stop` including **both** `vllm-omni` and `vllm-reasoner`, then
  `start api webui`.

### Requirement: the api reasoner context caps fit the NVFP4 reasoner's model length
The api's reasoner context/output caps on the NVFP4 stack SHALL be ≤ the reasoner's `--max-model-len`
minus chat-template headroom, so an unbounded `/v1/reason` gets a clean 422 at the edge (never a reasoner 400).

#### Scenario: nvfp4 caps ≤ max-model-len − headroom
- **WHEN** the nvfp4 stack's api `COSMOS3_REASONER_MAX_CONTEXT`/`_MAX_OUTPUT` and the reasoner
  `--max-model-len` are compared
- **THEN** both caps are ≤ (`--max-model-len` − 512), as on FP8 (guarded by `tests/deploy/test_reasoner_context_cap_*`).

## ADDED Requirements

### Requirement: the FP8 stack is not regressed by the NVFP4 changes
The FP8 stack SHALL render byte-identically after the AM-S5 changes (the FP8 compose file is a forbidden
file; shared-base edits, if any, must not alter FP8 rendering).

#### Scenario: FP8 render unchanged + file untouched
- **WHEN** `git diff --exit-code deploy/docker-compose.fp8.yml` runs and the FP8 config is rendered
- **THEN** the FP8 file is unmodified and its render still shows the FP8 all-modes wiring (omni with
  `--enable-layerwise-offload`, the `fp8_blockwise_w8a16` reasoner) with no BF16 mount.

### Requirement: default-on is honest per mode (INV-6/INV-7)
A mode SHALL be enabled by default on NVFP4 only after its recorded NVFP4 run **and** the owner's NVFP4
quality PASS; a mode that could not be served would be a documented owner decision, and `/v1/reason`
would error honestly (never a silent BF16 fallback).

#### Scenario: no silent BF16 fallback path
- **WHEN** the nvfp4 stack is inspected for a BF16 reasoner fallback
- **THEN** none exists — reasoning is served only by the NVFP4 W4A16 reasoner container, or (if it were
  absent) `/v1/reason` fails honestly; no `WITH_REASONING` build or BF16 overlay is on the `up-nvfp4` path.

## Notes

The NVFP4 checkpoint's `assets/` lacks the action demo conditioning *inputs* FP8 ships (evidence P1) — a
documented owner decision (AM-S6), not a `webui/**` change (R-12) and not a committed binary (INV-1).
