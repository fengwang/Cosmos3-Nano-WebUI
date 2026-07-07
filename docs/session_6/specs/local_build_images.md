# Specification - Local Build Images

Session: MIG-S6
Capability: Local Build Images

## ADDED Requirements

### Requirement: Buildable API and WebUI images from public inputs

The repository MUST provide `deploy/api.Dockerfile` and `deploy/webui.Dockerfile`
that build local images from public inputs only. The default `api` build MUST be
torch-free (server core), MUST include a Docker CLI (to drive the generation
container), and MUST NOT require CUDA, model weights, secrets, or private network
access. The `webui` build MUST produce a Next.js standalone runner.

#### Scenario: API image builds lean by default

WHEN `docker build -f deploy/api.Dockerfile -t cosmos3-nano-api:local .` runs
THEN it SHALL complete using public base images and the frozen `uv.lock`
AND SHALL NOT install torch/CUDA or copy any checkpoint file
AND the resulting image SHALL contain a `docker` client binary and start
`uvicorn app.main:app`.

#### Scenario: WebUI image builds a standalone server

WHEN `docker build -f deploy/webui.Dockerfile -t cosmos3-nano-webui:local .` runs
THEN it SHALL install dependencies with a frozen lockfile, run `next build`, and
copy the `.next/standalone` output into a slim runtime image
AND the runtime image SHALL launch the standalone `server.js`.

### Requirement: Optional reasoning build variant

`deploy/api.Dockerfile` MUST support an opt-in `WITH_REASONING` build argument that
adds the torch + vLLM reasoning layer, without changing the default lean build.

#### Scenario: Reasoning layer is opt-in

WHEN `docker build -f deploy/api.Dockerfile` runs without `--build-arg WITH_REASONING=1`
THEN the produced image SHALL be torch-free.

#### Scenario: Reasoning layer available on request

WHEN `docker build -f deploy/api.Dockerfile --build-arg WITH_REASONING=1` is invoked
THEN the Dockerfile SHALL select a CUDA-capable base, install the `oracle` extra
(torch), and install vLLM (pinned `0.23.0`, the version the reasoner code references)
so the in-container `vllm serve` subprocess can run. The GPU build and torch/vLLM/CUDA
compatibility are validated at `MIG-S8` (vLLM is a build-time install, not in `uv.lock`).

### Requirement: vLLM-Omni image renders but its build is a release gate

The repository MUST provide `deploy/vllm-omni.Dockerfile` for the generation engine.
Because it is GPU/heavy, its full build and run are the `MIG-S8` manual gate and MUST
NOT be a `MIG-S6` deterministic build check; the file MUST still be referenced by the
Compose stacks and MUST bake no weights.

#### Scenario: Generation image is wired but deferred

WHEN the FP8/NVFP4 Compose stacks are rendered
THEN they SHALL reference `deploy/vllm-omni.Dockerfile` as the `vllm-omni` service build
AND the S6 deterministic checks SHALL NOT require building that image
AND the Dockerfile SHALL contain no `COPY`/`ADD` of a checkpoint file.
