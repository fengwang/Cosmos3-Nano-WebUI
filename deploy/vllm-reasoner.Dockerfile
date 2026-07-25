# syntax=docker/dockerfile:1
# vLLM reasoner image (AM-S2). Serves TEXT reasoning off the quantized-only
# FP8-blockwise Cosmos3 checkpoint via `--quantization fp8_blockwise_w8a16`
# (NO --omni), zero BF16. Same base + vllm-omni pin as deploy/vllm-omni.Dockerfile,
# plus a 3-file vLLM patch (the Cosmos3 text-path blockwise-FP8 W8A16 quant) staged
# under deploy/vllm-reasoner/patch/. GPU-verified end to end on an RTX 5090 (sm_120):
# see docs/session_2/evidence/P2-fork-w8a16-text-serve-PASS.md.
#
# The patch mirrors the change in the fengwang/vllm fork (uncommitted at AM-S2
# authoring time); AM-S4 may switch this COPY-patch to a pinned public fork install
# once that commit is pushed (NFR-5).

ARG BASE_IMAGE=vllm/vllm-openai:v0.24.0
FROM ${BASE_IMAGE}

# Same immutable vllm-omni pin as the generation image (its Cosmos3
# Fp8BlockwiseW8A16LinearMethod is reused by the patch).
ARG VLLM_OMNI_REF=697035018b70cef76b974a909d23371a9984c3f2
ENV PYTHONUNBUFFERED=1
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
RUN if command -v uv >/dev/null 2>&1; then \
      uv pip install --system --no-cache-dir "git+https://github.com/fengwang/vllm-omni.git@${VLLM_OMNI_REF}"; \
    else \
      pip install --no-cache-dir "git+https://github.com/fengwang/vllm-omni.git@${VLLM_OMNI_REF}"; \
    fi

# AM-S2 vLLM patch: register `--quantization fp8_blockwise_w8a16` + map the modelopt
# blockwise-FP8 scale into vLLM's weight_scale param for the Cosmos3 understanding tower.
# The compose build context is the REPO ROOT (`build.context: ..`), so these COPY sources are
# repo-root-relative (`deploy/vllm-reasoner/patch/...`), like deploy/vllm-omni.Dockerfile's lineage.
# (AM-S3 fix: they previously omitted the `deploy/` prefix, so a compose-driven rebuild — triggered
# whenever the `:local` image is absent — failed with "…/patch/cosmos3.py: not found".)
ARG VLLM_SITE=/usr/local/lib/python3.12/dist-packages/vllm
COPY deploy/vllm-reasoner/patch/fp8_blockwise_w8a16_vllm.py ${VLLM_SITE}/model_executor/layers/quantization/fp8_blockwise_w8a16_vllm.py
COPY deploy/vllm-reasoner/patch/quantization__init__.py     ${VLLM_SITE}/model_executor/layers/quantization/__init__.py
COPY deploy/vllm-reasoner/patch/cosmos3.py                  ${VLLM_SITE}/model_executor/models/cosmos3.py

EXPOSE 8000
# vllm-openai's base sets ENTRYPOINT ["vllm","serve"]; clear it so CMD is the whole command.
ENTRYPOINT []
# Reasoning-only: NO --omni (text, not image); --quantization fp8_blockwise_w8a16 selects the
# weight-only FP8 understanding tower. Context/mem caps are operator-set (compose command:).
CMD ["vllm", "serve", "/models/checkpoint", "--host", "0.0.0.0", "--port", "8000", \
     "--served-model-name", "cosmos3-reasoner", \
     "--max-model-len", "8192", "--gpu-memory-utilization", "0.85", \
     "--quantization", "fp8_blockwise_w8a16"]
