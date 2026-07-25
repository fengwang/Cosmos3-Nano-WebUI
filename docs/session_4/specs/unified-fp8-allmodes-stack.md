# Capability: unified-fp8-allmodes-stack

The FP8 deploy surface is a single all-modes, zero-BF16 stack brought up by one
`make up-fp8`. Status: MODIFIED (collapses the prior three-posture layout).

Refs: PRD FR-4, GATE-AM-S4-ORCHESTRATION, INV-4, EV-AM-NO-OVERLAY-DEFAULT,
EV-AM-ZERO-BF16-WIRING.

## MODIFIED Requirements

### Requirement: Single all-modes FP8 stack

`make up-fp8` SHALL bring up Studio + Reasoning + Action off the quantized-only FP8
checkpoint from one command, with no reasoning overlay layered and no separate
`--build-arg`. The rendered `docker compose -f deploy/docker-compose.fp8.yml config`
SHALL contain both the `vllm-omni` and `vllm-reasoner` services, each mounting the same
FP8 checkpoint.

#### Scenario: Rendered fp8 config contains all-modes services

- WHEN `docker compose -f deploy/docker-compose.fp8.yml config` is rendered
- THEN it contains a `vllm-omni` service and a `vllm-reasoner` service
- AND both mount the FP8 checkpoint directory (`COSMOS3_FP8_DIR`) at
  `/models/checkpoint`
- AND no service is contributed by `docker-compose.reasoning.yml`

#### Scenario: One command, no overlay and no reasoning build-arg

- WHEN an operator runs `make up-fp8`
- THEN the target composes only `docker-compose.fp8.yml` (which `include:`s
  `docker-compose.base.yml`), with no `-f docker-compose.reasoning.yml`
- AND the api image is built with no `WITH_REASONING=1` argument

### Requirement: No BF16 surface in the default path

The default FP8 path SHALL require no BF16 base: the rendered config SHALL contain no
bind-mount of a BF16 base checkpoint (no `/models/base` target and no
`nvidia/Cosmos3-Nano` source), and the api image default build SHALL NOT install
torch/vLLM.

#### Scenario: Rendered config has no BF16 mount

- WHEN `docker compose -f deploy/docker-compose.fp8.yml config` is rendered
- THEN no volume maps a source containing `Cosmos3-Nano` (the BF16 base) or targets
  `/models/base`
- AND every model mount resolves to the FP8 quantized checkpoint

#### Scenario: api image default is lean/torch-free

- WHEN `docker build -f deploy/api.Dockerfile -t cosmos3-nano-api:local .` runs with no
  build args
- THEN the build performs `uv sync --frozen --no-dev` with no `oracle` extra and no
  `vllm` install
- AND there is no `WITH_REASONING` ARG or CUDA base stage in the Dockerfile

### Requirement: NVFP4 stack remains renderable

`docker compose -f deploy/docker-compose.nvfp4.yml config` SHALL still render
successfully after the FP8 unification. NVFP4 is not GPU-verified in this session.

#### Scenario: nvfp4 renders

- WHEN `docker compose -f deploy/docker-compose.nvfp4.yml config` is rendered
- THEN it succeeds with exit code 0
- AND it contains the `vllm-omni` service mounting the NVFP4 checkpoint

## REMOVED Requirements

### Requirement: BF16 reasoning subprocess overlay

`deploy/docker-compose.reasoning.yml` and the `make up-fp8-reasoning` posture are
removed.

**Reason:** The AM-S2 `vllm-reasoner` container serves reasoning off the quantized-only
FP8 checkpoint (zero BF16), fully superseding the BF16 subprocess overlay.

**Migration:** Reasoning is on by default via `make up-fp8`. Any prior
`make up-fp8-reasoning` invocation is replaced by `make up-fp8`. No BF16 base download
is required.

### Requirement: WITH_REASONING api build split

The `deploy/api.Dockerfile` `WITH_REASONING` ARG, the CUDA `base-1` stage, and the
conditional torch/vLLM install are removed.

**Reason:** Reasoning runs in the `vllm-reasoner` container, not an in-api subprocess;
the api image never needs torch/vLLM.

**Migration:** Build the api image with `make build-api` (no build args); it is lean
and torch-free.

### Requirement: BF16 base environment variables in .env.example

`COSMOS3_BASE_DIR`, `COSMOS3_REASONER_MODEL_DIR`, and `COSMOS3_VLLM_BIN` are removed
from `.env.example`, along with the legacy-overlay section and the BF16 base-download
block.

**Reason:** No default mode requires the BF16 base (reasoning and action serve off the
quantized checkpoint).

**Migration:** Operators download only the quantized checkpoint(s) per
`docs/model_setup.md`; the BF16 base is needed only for the dormant `diffusers_action`
graft, set explicitly if ever used.
