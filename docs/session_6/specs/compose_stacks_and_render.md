# Specification - Compose Stacks and Render

Session: MIG-S6
Capability: Compose Stacks and Render

## ADDED Requirements

### Requirement: FP8 and NVFP4 stacks render standalone

The repository MUST provide `deploy/docker-compose.fp8.yml` and
`deploy/docker-compose.nvfp4.yml`. Each MUST render a complete, valid configuration
under a single `-f` (via a shared `deploy/docker-compose.base.yml` included by
Compose), with no error and no unset-variable warning.

#### Scenario: FP8 stack renders

WHEN `docker compose -f deploy/docker-compose.fp8.yml config` runs
THEN it SHALL exit 0 and emit a valid merged configuration containing the `webui`,
`api`, and `vllm-omni` services
AND `COSMOS3_CHECKPOINT_LABEL` SHALL render as `fp8`.

#### Scenario: NVFP4 stack renders

WHEN `docker compose -f deploy/docker-compose.nvfp4.yml config` runs
THEN it SHALL exit 0 and emit a valid merged configuration
AND `COSMOS3_CHECKPOINT_LABEL` SHALL render as `nvfp4`.

#### Scenario: Render is self-contained

WHEN either stack is rendered with no shell-exported environment
THEN every interpolated variable SHALL resolve from an inline `${VAR:-default}` or an
`.env` default, so the output contains no empty-value or "variable is not set"
warning.

### Requirement: Service wiring matches the imported code contract

The rendered configuration MUST wire the services exactly as the imported code
expects: the WebUI reaches the API at `http://api:8000`, and the API reaches the
generation engine at the `vllm-omni` service on port 8000 with container name
`cosmos3-nano-webui-vllm-omni`.

#### Scenario: WebUI proxies to the API service

WHEN the FP8 or NVFP4 stack is rendered
THEN the `webui` service SHALL set `API_INTERNAL_URL` to `http://api:8000`.

#### Scenario: API targets the vLLM-Omni service and container name

WHEN the stack is rendered
THEN the `api` service SHALL set `COSMOS3_VLLM_OMNI_URL` to `http://vllm-omni:8000`
AND `COSMOS3_GEN_CONTAINER` to `cosmos3-nano-webui-vllm-omni`
AND the `vllm-omni` service SHALL declare `container_name: cosmos3-nano-webui-vllm-omni`.

### Requirement: API can drive the generation container

The `api` service MUST be granted Docker daemon access so the confined
`DockerCliController` can start/stop the generation container. The generation
container MUST NOT be force-started-and-locked such that the orchestrator cannot own
its lifecycle.

#### Scenario: API mounts the Docker socket

WHEN the stack is rendered
THEN the `api` service SHALL bind-mount `/var/run/docker.sock` into the container.

#### Scenario: Generation container lifecycle is orchestrator-owned

WHEN the stack is rendered
THEN the `vllm-omni` service SHALL use `restart: "no"`
AND the `api` service SHALL NOT declare a `depends_on` health condition on
`vllm-omni` (readiness is governed by `COSMOS3_PLANE_READY_TIMEOUT`).

### Requirement: Optional reasoning overlay

The repository MUST provide `deploy/docker-compose.reasoning.yml` that adds the api
GPU reservation, the BF16 base mount, and the reasoning binary env, composable as an
additional `-f` overlay. It MUST render together with a stack and MUST NOT be
required for the default generation stacks.

#### Scenario: Reasoning overlay renders on top of a stack

WHEN `docker compose -f deploy/docker-compose.base.yml -f deploy/docker-compose.fp8.yml -f deploy/docker-compose.reasoning.yml config` runs
THEN it SHALL exit 0
AND the `api` service SHALL then declare a GPU reservation and a BF16 base mount.

### Requirement: Local operation commands

The repository MUST provide a `Makefile` exposing local build/up/down/health/smoke
and scan commands over the FP8 and NVFP4 stacks.

#### Scenario: Make targets exist and select a stack

WHEN `make config-fp8` (and `config-nvfp4`) runs
THEN it SHALL invoke `docker compose -f deploy/docker-compose.fp8.yml config`
AND targets for build, up, down, health, smoke, and scan SHALL be present.
