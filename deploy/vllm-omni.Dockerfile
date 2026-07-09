# syntax=docker/dockerfile:1
# vLLM-Omni generation-engine image (GPU-S1). Installs the pinned public fork from the
# immutable commit (INV-3) and serves an operator-mounted checkpoint on :8000
# (readiness: /v1/models). No weights are ever copied in (INV-2); the checkpoint
# is a runtime mount. Base matches the fork's own docker/Dockerfile.cuda pattern
# (vllm-openai already ships torch + CUDA + vLLM with a build toolchain), confirmed
# on an RTX 5090 (sm_120) — see docs/session_1/ for the build/serve/T2I evidence.

ARG BASE_IMAGE=vllm/vllm-openai:v0.24.0
FROM ${BASE_IMAGE}

# GPU-S1 immutable pin: commit SHA (a tag can be force-moved; the commit cannot).
ARG VLLM_OMNI_REF=697035018b70cef76b974a909d23371a9984c3f2
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Immutable commit — never a bare mutable branch (INV-3). Public HTTPS for reproducibility.
# SETUPTOOLS_SCM_PRETEND_VERSION: the fork's build backend derives its package version from
# the nearest reachable git tag; at this pinned commit that's `cosmos3-nano-webui-mig-s2`
# (an internal tracking tag, not a PEP 440 version), which its own vcs_versioning fallback
# cannot parse either — the install fails before it ever touches our code. Pretending a
# version sidesteps that fork-side build-tooling bug without patching the fork itself.
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0
RUN if command -v uv >/dev/null 2>&1; then \
      uv pip install --system --no-cache-dir "git+https://github.com/fengwang/vllm-omni.git@${VLLM_OMNI_REF}"; \
    else \
      pip install --no-cache-dir "git+https://github.com/fengwang/vllm-omni.git@${VLLM_OMNI_REF}"; \
    fi

EXPOSE 8000
# vllm-openai's own image sets ENTRYPOINT ["vllm", "serve"]; clear it (matching the fork's
# own docker/Dockerfile.cuda) so CMD below is the whole command, not appended args that
# would otherwise double up into "vllm serve vllm serve ...".
ENTRYPOINT []
# Confirmed OpenAI-compatible entrypoint (docs/model_setup.md §9). Guardrails stay ON
# by default here; --no-guardrails is an explicit runtime override (Compose `command:`
# or `docker run` args), never baked into the shipped default.
CMD ["vllm", "serve", "/models/checkpoint", "--omni", \
     "--host", "0.0.0.0", "--port", "8000", "--init-timeout", "1800"]
