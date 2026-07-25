# Local-build Docker/Compose commands (MIG-S6; AM-S4). Run from the repo root.
# Compose project dir = deploy/ (so `..` == repo root, `../models` == <repo>/models).
# vLLM-Omni image build and all GPU inference are the MIG-S8 manual gate.
.RECIPEPREFIX = >
.PHONY: help build build-api build-webui config config-fp8 config-nvfp4 \
        up-fp8 up-nvfp4 down health smoke scan

# Compose's project dir is deploy/ (first -f), so it would look for deploy/.env and
# ignore a repo-root .env. Auto-pass a repo-root .env when present (no-op when absent —
# the inline ${VAR:-default} defaults then apply, so `make config-*` still renders).
ENV_FILE := $(wildcard .env)
COMPOSE ?= docker compose $(if $(ENV_FILE),--env-file $(ENV_FILE),)
FP8    := -f deploy/docker-compose.fp8.yml
NVFP4  := -f deploy/docker-compose.nvfp4.yml
API_PORT ?= 8000

help:
> @echo "build | build-api | build-webui | config-fp8 | config-nvfp4 | up-fp8 | up-nvfp4 | down | health | smoke | scan"

# ── Build (CPU-buildable images; vLLM-Omni build is the MIG-S8 GPU gate) ──
build-webui:
> docker build -f deploy/webui.Dockerfile -t cosmos3-nano-webui:local .
build-api:
> docker build -f deploy/api.Dockerfile -t cosmos3-nano-api:local .
build: build-webui build-api

# ── Render stacks (deterministic gate) ──
config: config-fp8
config-fp8:
> $(COMPOSE) $(FP8) config
config-nvfp4:
> $(COMPOSE) $(NVFP4) config

# ── Up / down (one stack at a time — shared fixed container names) ──
# Cold-start (AM-S4): `up -d --no-start` creates every container but starts none; then start
# ONLY the lightweight api+webui and stop the heavy GPU planes. The api orchestrator owns the
# heavy containers' start/stop on demand and evicts-before-loads, so the two heavy planes
# (vllm-omni ~14.7 GiB + vllm-reasoner ~26 GiB) never co-load in the 32 GiB budget (INV-5).
# The `stop` line is an idempotency guard for a re-run that left a heavy container running.
up-fp8:
> $(COMPOSE) $(FP8) up -d --no-start
> $(COMPOSE) $(FP8) stop vllm-omni vllm-reasoner
> $(COMPOSE) $(FP8) start api webui
up-nvfp4:
> $(COMPOSE) $(NVFP4) up -d --no-start
> $(COMPOSE) $(NVFP4) stop vllm-omni
> $(COMPOSE) $(NVFP4) start api webui
# Tears down BOTH stacks: fp8/nvfp4 share one compose project (deploy/) + fixed container names.
down:
> $(COMPOSE) $(FP8) down --remove-orphans

# ── Health + smoke (against the running API) ──
health:
> curl -fsS localhost:$(API_PORT)/v1/health/ready && echo
smoke:
> curl -fsS localhost:$(API_PORT)/v1/health/live && echo

# ── Safety scans (weight-copy + committed private-reference scan) ──
scan:
> @if rg -q "COPY .*\.(safetensors|pt|pth|ckpt)|ADD .*\.(safetensors|pt|pth|ckpt)" deploy; then \
>   echo "weight-copy: FOUND"; exit 1; else echo "weight-copy: clean"; fi
> uv run python tests/test_private_ref_scan.py
