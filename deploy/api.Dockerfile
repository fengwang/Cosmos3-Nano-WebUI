# syntax=docker/dockerfile:1
# API local-build image (MIG-S6). Default target is LEAN and torch-free: the FastAPI
# server plus a Docker CLI so the confined DockerCliController can start/stop the
# generation container. `--build-arg WITH_REASONING=1` selects a CUDA base and installs
# the vLLM reasoning stack (the in-container `vllm serve` subprocess); its GPU build/run
# is the MIG-S8 gate. Build from repo root:
#   docker build -f deploy/api.Dockerfile -t cosmos3-nano-api:local .
#   docker build -f deploy/api.Dockerfile --build-arg WITH_REASONING=1 -t cosmos3-nano-api:reasoning .

ARG WITH_REASONING=0

# Lean, torch-free default base (system python 3.12 matches requires-python).
FROM python:3.12-slim AS base-0

# Reasoning base: CUDA 12.8 for the RTX 5090 (sm_120). System python here is not 3.12,
# so uv provisions the pinned interpreter. Exact CUDA tag/python setup verified in MIG-S8.
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04 AS base-1
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git \
    && rm -rf /var/lib/apt/lists/*

FROM base-${WITH_REASONING} AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
# Static Docker client only (no daemon) — confined use via DockerCliController (R-06).
COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker
# uv for a frozen, lockfile-exact install (no host Python assumptions).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
# Manifests first for layer caching. package=false → uv installs deps only, not the app.
COPY pyproject.toml uv.lock ./
ARG WITH_REASONING
# Lean = server core only (torch-free). Reasoning = + the proven `oracle` extra (torch/vLLM).
RUN if [ "$WITH_REASONING" = "1" ]; then \
      uv sync --frozen --no-dev --extra oracle ; \
    else \
      uv sync --frozen --no-dev ; \
    fi
# Only the API source — never the repo root, weights, or tests (INV-2; narrow COPY).
COPY api/ ./api/
ENV PYTHONPATH=/app/api
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
