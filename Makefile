# Local-build Docker/Compose commands (MIG-S6). Run from the repo root.
# Compose project dir = deploy/ (so `..` == repo root, `../models` == <repo>/models).
# vLLM-Omni image build and all GPU inference are the MIG-S8 manual gate.
.RECIPEPREFIX = >
.PHONY: help build build-api build-webui config config-fp8 config-nvfp4 \
        up-fp8 up-nvfp4 up-fp8-reasoning down health smoke scan

COMPOSE ?= docker compose
FP8    := -f deploy/docker-compose.fp8.yml
NVFP4  := -f deploy/docker-compose.nvfp4.yml
REASON := -f deploy/docker-compose.reasoning.yml
API_PORT ?= 8000

help:
> @echo "build | build-api | build-webui | config-fp8 | config-nvfp4 | up-fp8 | up-nvfp4 | up-fp8-reasoning | down | health | smoke | scan"

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

# ── Up / down (one stack at a time — shared fixed container name) ──
up-fp8:
> $(COMPOSE) $(FP8) up -d
up-nvfp4:
> $(COMPOSE) $(NVFP4) up -d
up-fp8-reasoning:
> $(COMPOSE) $(FP8) $(REASON) up -d
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
