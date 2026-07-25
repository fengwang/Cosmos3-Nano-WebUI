# Capability: cold-start-residency-lifecycle

`make up-fp8` boots with the heavy GPU planes created-but-stopped and orchestrator-owned;
a mode swap evicts-before-loads; the two heavy planes never co-reside. Status: ADDED
(boot lifecycle) + MODIFIED (coresidency footprint).

Refs: PRD FR-4/FR-8, INV-5, R-08, GPU-AM-ALLMODES-FP8.

## ADDED Requirements

### Requirement: Cold-start boot (heavy planes created-but-stopped)

`make up-fp8` SHALL leave only the lightweight `api` and `webui` services running after
bring-up; the heavy `vllm-omni` and `vllm-reasoner` containers SHALL be created but not
running. The bring-up SHALL be idempotent: a re-run with a heavy container left running
SHALL still result in that container stopped.

#### Scenario: Boot leaves only light services running

- WHEN an operator runs `make up-fp8` on a host with no running project containers
- THEN `api` and `webui` are running
- AND `vllm-omni` and `vllm-reasoner` exist but are stopped

#### Scenario: Bring-up is idempotent against a stale running heavy container

- WHEN `vllm-omni` is already running and the operator runs `make up-fp8`
- THEN the `stop vllm-omni vllm-reasoner` step stops it
- AND after bring-up only `api` and `webui` are running

### Requirement: Orchestrator-owned on-demand start with evict-before-load

A request for a mode whose plane is not resident SHALL cause the orchestrator to start
that plane's container on demand; a request for a different residency SHALL evict the
incumbent plane (container stop) and wait for VRAM release before loading the new plane.
No orchestrator FSM code change is introduced by this session.

#### Scenario: First request cold-loads its plane

- WHEN the slot is cold and a generation (Studio/Action) request arrives
- THEN the orchestrator starts `vllm-omni` and marks `Plane.GENERATION` resident
- AND no eviction occurs (nothing was resident)

#### Scenario: Cross-plane request evicts before loading

- WHEN `Plane.GENERATION` is resident and a `/v1/reason` request arrives
- THEN the orchestrator stops `vllm-omni`, waits until VRAM drops below the idle
  threshold, then starts `vllm-reasoner` and marks `Plane.REASONING` resident
- AND if VRAM does not release, the load is refused with `WorkerStartError` (no OOM load)

### Requirement: Heavy planes never co-reside within the VRAM budget

At no point in an all-modes session SHALL both `vllm-omni` and `vllm-reasoner` be
resident simultaneously; peak VRAM SHALL stay within the 32 GiB budget. Studio and
Action MAY share the one resident `vllm-omni` model (plane-merge, `Plane.GENERATION`).

#### Scenario: All-modes smoke stays within budget (GPU)

- WHEN the all-modes smoke runs Studio → Action → Reasoning → Studio on one `make up-fp8`
- THEN each step's peak VRAM is ≤ 32 GiB
- AND `vllm-omni` and `vllm-reasoner` are never running at the same time
- AND `t2i` produces a valid image before and after the reasoning swap (INV-2)

## MODIFIED Requirements

### Requirement: Coresidency footprint reflects the FP8 reasoner (R-08)

The documented coresidency footprint in `api/engines/vllm/coresidency.py` SHALL describe
the reasoner as an FP8 quantized, KV-cache-dominated resident at 0.85 utilization — not
~16 GiB BF16 weights. The `gpu_memory_utilization` contract constant SHALL equal the
value in the live `vllm-reasoner` compose command.

#### Scenario: Contract constant matches the compose reasoner command

- WHEN the `vllm-reasoner` service command in `deploy/docker-compose.fp8.yml` is parsed
- THEN its `--gpu-memory-utilization` value equals
  `CoResidencyContract().gpu_memory_utilization`

#### Scenario: Footprint comment describes FP8, not BF16

- WHEN a reader inspects the coresidency footprint documentation
- THEN it attributes the ~26 GiB resident figure to FP8 weights + KV cache at 0.85
  utilization
- AND it does not claim the reasoner loads ~16 GiB of BF16 base weights
