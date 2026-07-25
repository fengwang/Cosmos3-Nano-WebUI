# syntax=docker/dockerfile:1
# API local-build image (MIG-S6; AM-S4). LEAN and torch-free: the FastAPI server plus a
# Docker CLI so the confined DockerCliController can start/stop the generation and reasoner
# containers. Reasoning runs in the separate vllm-reasoner container (AM-S2, zero BF16), so
# the api image needs no torch/vLLM and no CUDA base — the old reasoning-build split (the
# torch/vLLM build variant) is retired. Build from repo root:
#   docker build -f deploy/api.Dockerfile -t cosmos3-nano-api:local .

# Lean, torch-free base (system python 3.12 matches requires-python).
FROM python:3.12-slim AS runtime
# UV_NO_CACHE keeps uv's wheel cache out of the committed layer. Pinned helper images
# (not `latest`) for reproducibility.
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 UV_NO_CACHE=1
# Static Docker client only (no daemon) — confined use via DockerCliController (R-06).
COPY --from=docker:28-cli /usr/local/bin/docker /usr/local/bin/docker
# uv for a frozen, lockfile-exact install (no host Python assumptions).
COPY --from=ghcr.io/astral-sh/uv:0.11.25 /uv /usr/local/bin/uv
WORKDIR /app
# Manifests first for layer caching. package=false → uv installs deps only, not the app.
COPY pyproject.toml uv.lock ./
# Server core only (torch-free): generation, reasoning, and action are all served by the
# vllm containers, which the api controls over the docker socket — never in-process here.
RUN uv sync --frozen --no-dev
# Only the API source — never the repo root, weights, or tests (INV-2; narrow COPY).
COPY api/ ./api/
ENV PYTHONPATH=/app/api
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
