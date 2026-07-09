# Session 6 Implementation Plan - Local-Build Docker and Compose

Session: MIG-S6
Input: `docs/session_6/tasks.md`; references `specs/*.md` + `design.md`.
Style: infra-TDD — the deterministic **check** is the failing test written first;
the file is the smallest change that makes it pass. Commit at each clean checkpoint.

Pre-flight (baseline): `git status --short` clean; `docker version`, `docker compose
version`; record that `deploy/` does not exist so the render checks fail for
"no configuration file" (baseline). See `docs/session_6/execution_contract.md`.

## Task 1 — Context hygiene + env surface

1. Write `.dockerignore` (repo root):
   ```
   .git
   .venv
   **/__pycache__
   **/*.pyc
   node_modules
   webui/.next
   webui/node_modules
   models/
   docs
   references
   .github
   tests
   *.safetensors
   *.pt
   *.pth
   *.ckpt
   *.mp4
   *.webm
   *.png
   *.jpg
   ```
   (Keep `misc/logo.png` out of images via `docs`/root globs; images need no media.)
2. Write `.env.example` documenting the full surface (repo-relative defaults):
   ```
   # WebUI ↔ API
   API_INTERNAL_URL=http://api:8000
   COSMOS3_API_KEY=
   WEBUI_PORT=3000
   API_PORT=8000
   # Generation engine wiring (defaults baked in code; shown for clarity)
   COSMOS3_GEN_ENGINE=vllm_omni
   COSMOS3_VLLM_OMNI_URL=http://vllm-omni:8000
   COSMOS3_GEN_CONTAINER=cosmos3-nano-webui-vllm-omni
   COSMOS3_DEVICE=cuda
   # Checkpoint (see docs/model_setup.md — pinned public HF revisions)
   COSMOS3_CHECKPOINT_LABEL=fp8
   COSMOS3_FP8_DIR=./models/Cosmos3-Nano-FP8-Blockwise
   COSMOS3_NVFP4_DIR=./models/Cosmos3-Nano-NVFP4-Blockwise
   COSMOS3_MODEL_DIR=/models/checkpoint          # in-container mount target
   # Reasoning / action (BF16 base nvidia/Cosmos3-Nano) — reasoning overlay only
   COSMOS3_REASONER_MODEL_DIR=/models/base
   COSMOS3_BASE_ACTION_DIR=/models/base/transformer
   COSMOS3_BASE_DIR=./models/Cosmos3-Nano
   # vLLM-Omni pin (MIG-S2): tag cosmos3-nano-webui-mig-s2 (697035018b70…)
   ```
   Check: `rg -n "$PRIVATE_REF_PATTERN" .env.example` → no match; no `/home/` path.
   Commit: `feat(s6): .dockerignore + .env.example (context hygiene + env surface)`.

## Task 2 — WebUI image

1. Write `deploy/webui.Dockerfile`:
   ```dockerfile
   # syntax=docker/dockerfile:1
   FROM node:22-slim AS build
   ENV NEXT_TELEMETRY_DISABLED=1
   WORKDIR /app
   RUN corepack enable && corepack prepare pnpm@11.3.0 --activate
   COPY webui/package.json webui/pnpm-lock.yaml webui/pnpm-workspace.yaml ./
   RUN pnpm install --frozen-lockfile
   COPY webui/ ./
   RUN pnpm build

   FROM node:22-slim AS run
   ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
   WORKDIR /app
   COPY --from=build /app/.next/standalone ./
   COPY --from=build /app/.next/static ./.next/static
   COPY --from=build /app/public ./public
   EXPOSE 3000
   CMD ["node", "server.js"]
   ```
2. Check (spec `local_build_images`):
   `docker build -f deploy/webui.Dockerfile -t cosmos3-nano-webui:local .` → success.
   Commit: `feat(s6): webui local-build Dockerfile (standalone runner)`.

## Task 3 — API image (lean default + WITH_REASONING)

1. Write `deploy/api.Dockerfile`:
   ```dockerfile
   # syntax=docker/dockerfile:1
   ARG WITH_REASONING=0
   ARG LEAN_BASE=python:3.12-slim
   ARG CUDA_BASE=nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

   FROM ${LEAN_BASE} AS base-0          # torch-free default
   FROM ${CUDA_BASE} AS base-1          # reasoning variant (adds python)
   RUN apt-get update && apt-get install -y --no-install-recommends python3.12 python3-pip \
     && rm -rf /var/lib/apt/lists/*

   FROM base-${WITH_REASONING} AS runtime
   ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
   # Docker CLI so DockerCliController can start/stop the gen container
   RUN apt-get update && apt-get install -y --no-install-recommends docker.io ca-certificates \
     && rm -rf /var/lib/apt/lists/*
   COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
   WORKDIR /app
   COPY pyproject.toml uv.lock ./
   ARG WITH_REASONING
   RUN if [ "$WITH_REASONING" = "1" ]; then uv sync --frozen --extra oracle; \
       else uv sync --frozen; fi
   COPY api/ ./api/
   COPY schemas/ ./schemas/
   ENV PYTHONPATH=/app/api
   EXPOSE 8000
   CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
   Note: `uv sync --frozen` (no extra) installs the torch-free server core; vLLM is
   part of `oracle` only if the lock resolves it — reasoning parity is an S8 verify
   item (the reasoner subprocess also needs `COSMOS3_VLLM_BIN` on PATH). Confirm the
   exact lean install command against `pyproject.toml`/`uv.lock` during the step.
2. Check: `docker build -f deploy/api.Dockerfile -t cosmos3-nano-api:local .` → lean
   success; `docker run --rm cosmos3-nano-api:local python -c "import app.main"` (or
   equivalent import smoke). Confirm `docker` client present:
   `docker run --rm cosmos3-nano-api:local docker --version`.
   Commit: `feat(s6): api local-build Dockerfile (lean default + WITH_REASONING arg)`.

## Task 4 — vLLM-Omni image (render-only, pinned)

1. Write `deploy/vllm-omni.Dockerfile`:
   ```dockerfile
   # syntax=docker/dockerfile:1
   FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04
   ARG VLLM_OMNI_REF=cosmos3-nano-webui-mig-s2   # MIG-S2 immutable tag (697035018b70…)
   ENV PYTHONUNBUFFERED=1
   RUN apt-get update && apt-get install -y --no-install-recommends \
       python3.12 python3-pip git ca-certificates && rm -rf /var/lib/apt/lists/*
   RUN pip install --no-cache-dir \
       "git+https://github.com/fengwang/vllm-omni.git@${VLLM_OMNI_REF}"
   EXPOSE 8000
   # Serve the operator-mounted checkpoint; exact CLI verified in MIG-S8.
   CMD ["python3", "-m", "vllm_omni.entrypoints.openai.api_server", \
        "--model", "/models/checkpoint", "--host", "0.0.0.0", "--port", "8000"]
   ```
   (The `CMD` is overridable via Compose `command:`; S8 confirms the fork's real
   entrypoint. Readiness probe is `/v1/models`.)
2. Check (spec `vllm_omni_pin_consumption`, `image_weight_and_path_safety`):
   `rg -n "COPY .*\.(safetensors|pt|pth|ckpt)|ADD .*\.(safetensors|pt|pth|ckpt)" deploy`
   → no match; grep confirms the immutable tag. **No build** (S8 gate).
   Commit: `feat(s6): vllm-omni Dockerfile consuming the MIG-S2 pin (render-only)`.

## Task 5 — Compose stacks

1. `deploy/docker-compose.base.yml` (skeleton):
   ```yaml
   services:
     webui:
       build: { context: .., dockerfile: deploy/webui.Dockerfile }
       image: cosmos3-nano-webui:local
       environment:
         API_INTERNAL_URL: http://api:8000
         COSMOS3_API_KEY: ${COSMOS3_API_KEY:-}
       ports: ["${WEBUI_PORT:-3000}:3000"]
       depends_on: [api]
       restart: unless-stopped
     api:
       build: { context: .., dockerfile: deploy/api.Dockerfile }
       image: cosmos3-nano-api:local
       environment:
         COSMOS3_GEN_ENGINE: ${COSMOS3_GEN_ENGINE:-vllm_omni}
         COSMOS3_VLLM_OMNI_URL: http://vllm-omni:8000
         COSMOS3_GEN_CONTAINER: cosmos3-nano-webui-vllm-omni
         COSMOS3_CHECKPOINT_LABEL: ${COSMOS3_CHECKPOINT_LABEL:-fp8}
         COSMOS3_API_KEY: ${COSMOS3_API_KEY:-}
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock
       ports: ["${API_PORT:-8000}:8000"]
       restart: unless-stopped
     vllm-omni:
       build: { context: .., dockerfile: deploy/vllm-omni.Dockerfile }
       image: cosmos3-nano-vllm-omni:local
       container_name: cosmos3-nano-webui-vllm-omni
       environment:
         COSMOS3_MODEL_DIR: ${COSMOS3_MODEL_DIR:-/models/checkpoint}
       volumes:
         - ${COSMOS3_CKPT_DIR:-./models/Cosmos3-Nano-FP8-Blockwise}:/models/checkpoint:ro
       restart: "no"
       deploy:
         resources:
           reservations:
             devices: [{ driver: nvidia, count: all, capabilities: [gpu] }]
   ```
   (Note: `api` has no `depends_on` health condition on `vllm-omni` — D-7.)
2. `deploy/docker-compose.fp8.yml`:
   ```yaml
   include: [docker-compose.base.yml]
   services:
     api:
       environment: { COSMOS3_CHECKPOINT_LABEL: fp8 }
     vllm-omni:
       volumes:
         - ${COSMOS3_FP8_DIR:-./models/Cosmos3-Nano-FP8-Blockwise}:/models/checkpoint:ro
   ```
   `deploy/docker-compose.nvfp4.yml`: same with `nvfp4` +
   `${COSMOS3_NVFP4_DIR:-./models/Cosmos3-Nano-NVFP4-Blockwise}`.
3. `deploy/docker-compose.reasoning.yml` (overlay):
   ```yaml
   services:
     api:
       environment:
         COSMOS3_VLLM_BIN: ${COSMOS3_VLLM_BIN:-vllm}
         COSMOS3_REASONER_MODEL_DIR: ${COSMOS3_REASONER_MODEL_DIR:-/models/base}
       volumes:
         - ${COSMOS3_BASE_DIR:-./models/Cosmos3-Nano}:/models/base:ro
       deploy:
         resources:
           reservations:
             devices: [{ driver: nvidia, count: all, capabilities: [gpu] }]
   ```
4. Checks (spec `compose_stacks_and_render`):
   - `docker compose -f deploy/docker-compose.fp8.yml config` → exit 0, label `fp8`,
     no unset-var warning.
   - `docker compose -f deploy/docker-compose.nvfp4.yml config` → exit 0, label `nvfp4`.
   - `docker compose -f deploy/docker-compose.base.yml -f deploy/docker-compose.fp8.yml
     -f deploy/docker-compose.reasoning.yml config` → exit 0; api has GPU + base mount.
   - Assert wiring values (`API_INTERNAL_URL`, `COSMOS3_VLLM_OMNI_URL`,
     `COSMOS3_GEN_CONTAINER`, `container_name`, socket mount, `restart:"no"`).
   Commit: `feat(s6): fp8/nvfp4 compose stacks + reasoning overlay (include base)`.

## Task 6 — Makefile

1. `Makefile` targets:
   ```make
   COMPOSE ?= docker compose
   FP8  := -f deploy/docker-compose.fp8.yml
   NVFP4:= -f deploy/docker-compose.nvfp4.yml
   config-fp8:   ; $(COMPOSE) $(FP8) config
   config-nvfp4: ; $(COMPOSE) $(NVFP4) config
   build-webui:  ; docker build -f deploy/webui.Dockerfile -t cosmos3-nano-webui:local .
   build-api:    ; docker build -f deploy/api.Dockerfile -t cosmos3-nano-api:local .
   build: build-webui build-api
   up-fp8:   ; $(COMPOSE) $(FP8) up -d
   up-nvfp4: ; $(COMPOSE) $(NVFP4) up -d
   down:     ; $(COMPOSE) $(FP8) down --remove-orphans
   health:   ; curl -fsS localhost:$${API_PORT:-8000}/v1/health/ready
   smoke:    ; curl -fsS localhost:$${API_PORT:-8000}/v1/health/live
   scan:     ; rg -n "COPY .*\.(safetensors|pt|pth|ckpt)|ADD .*\.(safetensors|pt|pth|ckpt)" deploy; \
               uv run python tests/test_private_ref_scan.py
   ```
   Check: `make config-fp8` and `make config-nvfp4` render; `make -n build` lists the
   build commands. Commit: `feat(s6): Makefile (build/up/down/health/smoke/scan)`.

## Task 7 — Verification, review, adversarial

Run every contract deterministic check; classify failures (Failure Arbiter →
`failure_arbiter.md` if any); sharded review over the 5 axes
(`sharded_review.md`, fix only High/Critical, re-check); fresh-context adversarial
verifier (`adversarial_verification.md`).

## Task 8 — Close

Update `docs/evidence_map.md`, `docs/risk_register.md` (R-06 + docker-socket row),
`docs/eval_seed_cases.md`, `docs/eval_corpus/mig_s6_*.md`; amend
`docs/session_6_contract.yaml` `allowed_files` if needed (flag for owner); write
`docs/handoff.md`; verify `GATE-MIG-S6-DOCKER`.
