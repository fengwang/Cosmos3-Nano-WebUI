# Session 6 Proposal - Local-Build Docker and Compose Migration

Date: 2026-07-07
Session: MIG-S6
Risk: high · Gate: `GATE-MIG-S6-DOCKER`
Derived from: `docs/session_6/brainstorming.md` (approved 2026-07-07)

## Motivation

Give public beta users a repeatable, weight-free local deployment: build the API,
WebUI, and vLLM-Omni layers from public code, wire them with Compose, mount
checkpoints they download themselves, and consume the `MIG-S2` vLLM-Omni pin — all
rendering and scanning clean, with GPU inference left to the `MIG-S8` manual gate.
Application code is honored as-imported (out of blast radius); the deployment adapts
to the code, never the reverse.

## Specific changes agreed

1. **Three Dockerfiles** under `deploy/`:
   - `webui.Dockerfile` — `node:22` multi-stage → Next.js `standalone` runner (CPU).
   - `api.Dockerfile` — multi-stage; **default lean** (`python:3.12-slim`, torch-free
     FastAPI + Docker CLI); `--build-arg WITH_REASONING=1` adds the CUDA + vLLM layer.
   - `vllm-omni.Dockerfile` — CUDA 12.8 base + the pinned fork; serves the mounted
     checkpoint on `:8000`. Build/run is the S8 gate (not a deterministic build check).
2. **Compose stacks**: `docker-compose.base.yml` + `docker-compose.fp8.yml` /
   `.nvfp4.yml` (via Compose `include:`), each rendering standalone; plus an optional
   `docker-compose.reasoning.yml` overlay.
3. **Config**: `.dockerignore`, `.env.example`, `Makefile` (build/up/down/health/
   smoke/scan). Checkpoint mounts are env-driven with repo-relative `./models/<Repo>`
   defaults.
4. **Docker-socket privilege**: the api service bind-mounts `/var/run/docker.sock`
   and ships the Docker CLI (confined `DockerCliController`); recorded as a risk.
5. **Docs**: refining pack under `docs/session_6/**`; updates to
   `docs/{evidence_map,risk_register,eval_seed_cases}.md`, `docs/eval_corpus/`, and
   `docs/handoff.md`.

## Capabilities (contract with the specification phase)

### New capabilities (one spec file each)

- **`local_build_images`** — the three Dockerfiles build local images from public
  inputs, bake no weights, and pin base images; api lean/`WITH_REASONING` targets;
  vLLM-Omni build deferred to S8.
- **`compose_stacks_and_render`** — FP8 and NVFP4 stacks render under a single `-f`
  via a shared base; service wiring (`webui`→`api`→`vllm-omni`), ports, gen-container
  lifecycle, and the optional reasoning overlay.
- **`external_checkpoint_mounts`** — checkpoint locations are operator env inputs
  with repo-relative example defaults and no private/absolute paths; the env surface
  matches `docs/model_setup.md`.
- **`vllm_omni_pin_consumption`** — the generation image installs the vLLM-Omni fork
  from the immutable `MIG-S2` tag/commit, never a mutable branch alone.
- **`image_weight_and_path_safety`** — `.dockerignore` + build patterns make baking
  weights impossible, and the private-reference + weight-copy scans pass over
  `deploy/`, `.env.example`, and the session docs.

### Modified capabilities

- None. No existing capability's requirements change; `api/**` and `webui/**` are
  untouched, so `INV-9` (public API shape) is preserved by construction.

## Impact

- **Affected files**: new `deploy/**`, `.dockerignore`, `.env.example`, `Makefile`;
  updated migration docs. No source, schema, or workflow-secret changes.
- **APIs**: none changed. New *deployment* surface only.
- **Dependencies**: no new **repo** production dependency (INV-10). Images install
  pinned public artifacts (base images, the vLLM-Omni fork tag, `uv`/`pnpm` frozen
  installs) at build time; none is added to `pyproject.toml`/`package.json`.
- **Systems**: introduces a documented docker-socket privilege on the api container
  (tracked as risk **R-16**) and a single-GPU serialized reasoning⊕generation runtime
  whose GPU behavior is the S8 gate.
