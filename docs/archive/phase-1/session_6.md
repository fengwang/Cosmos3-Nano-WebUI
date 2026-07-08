# Session 6 - Local-Build Docker and Compose Migration

Contract: `docs/session_6_contract.yaml`
Risk: high
Routing: worker_plus_reviewers

## Objective

Provide local-build Dockerfiles and Compose files that use the pinned public
vLLM-Omni fork commit and externally mounted FP8/NVFP4 checkpoints.

## Why This Session Exists

Public users need a repeatable local deployment path, but the first milestone
does not publish Docker images and must not bake model weights into images. Docker
and Compose must therefore be buildable from public code and configurable model
mounts.

## In Scope

1. Create or migrate Dockerfiles for API, WebUI, and vLLM-Omni runtime layers.
2. Consume the pinned public vLLM-Omni commit from `MIG-S2`.
3. Create local-build Compose files for FP8 and NVFP4 stacks.
4. Use environment variables for checkpoint paths.
5. Ensure Compose renders without private paths or image-published assumptions.
6. Add local commands for build, up, down, health, and smoke where feasible.
7. Run CPU/render checks and, when available, manual GPU smoke using `MIG-S4`
   checkpoint setup.

## Out of Scope

- No registry push.
- No runtime auto-download of model weights.
- No GPU GitHub Actions.
- No README rewrite beyond handoff notes.

## Deliverables

- Dockerfiles and Compose files for local build.
- `.env.example` or equivalent public config template.
- Build/render evidence.
- Manual GPU smoke notes if hardware and checkpoints are available.

## Deterministic Checks

```bash
rtk docker compose -f deploy/docker-compose.fp8.yml config
rtk docker compose -f deploy/docker-compose.nvfp4.yml config
rtk rg -n "$PRIVATE_REF_PATTERN" deploy .github README.md docs
rtk rg -n "COPY .*\\.(safetensors|pt|pth|ckpt)|ADD .*\\.(safetensors|pt|pth|ckpt)" deploy
rtk docker build -f deploy/api.Dockerfile -t cosmos3-nano-api:local .
rtk docker build -f deploy/webui.Dockerfile -t cosmos3-nano-webui:local .
```

Adapt filenames to the imported deploy tree and record checks that are not
available.

## Exit Criteria

- `GATE-MIG-S6-DOCKER` passes.
- Compose renders with public, configurable model mounts.
- Docker builds do not copy weights or private source.
- The README session has exact setup commands to document.

## Handoff

Hand off Docker build commands, Compose files, env variables, vLLM-Omni pin, and
known runtime caveats to `MIG-S7` and `MIG-S8`.
