# syntax=docker/dockerfile:1
# vLLM NVFP4 reasoner image (AM-S5). Serves TEXT reasoning off the quantized-only
# NVFP4-blockwise Cosmos3 checkpoint via `--quantization nvfp4_blockwise_w4a16`
# (NO --omni), zero BF16. Same base + vllm-omni pin as deploy/vllm-reasoner.Dockerfile
# (the FP8 reasoner), plus a 3-file vLLM patch (the Cosmos3 NVFP4 W4A16 text path)
# staged under deploy/vllm-reasoner/patch-nvfp4/. GPU-verified end to end on an RTX
# 5090 (sm_120): see docs/session_5/evidence/P2-reasoner-nvfp4-w4a16-text-serve-PASS.md.
#
# A SEPARATE image from the FP8 reasoner (not a build-arg on it) so the frozen-verified
# FP8 reasoner path is untouched (AM-S5 design D1 / blast radius). The patch reuses
# vLLM's ModelOptNvFp4W4A16LinearMethod (Marlin FP4, weight-only); NVFP4 4-bit weights
# are FP4-resident (~26.9 GiB incl. KV at 0.85 util) with NO layerwise offload (the
# Marlin FP4 kernel repacks on CUDA after load and forbids offload).

ARG BASE_IMAGE=vllm/vllm-openai:v0.24.0
FROM ${BASE_IMAGE}

# Same immutable vllm-omni pin as the generation + FP8-reasoner images (its
# ModelOptNvFp4W4A16LinearMethod / Marlin FP4 kernel is reused by the patch).
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

# AM-S5 vLLM patch: register `--quantization nvfp4_blockwise_w4a16` + map the modelopt
# NVFP4 sidecars (weight_packed/weight_block_scale/weight_global_scale) into vLLM's
# ModelOptNvFp4W4A16 param names for the Cosmos3 understanding tower's FUSED MLP.
# The compose build context is the REPO ROOT (`build.context: ..`), so these COPY
# sources are repo-root-relative (`deploy/vllm-reasoner/patch-nvfp4/...`), matching
# deploy/vllm-reasoner.Dockerfile's lineage.
ARG VLLM_SITE=/usr/local/lib/python3.12/dist-packages/vllm
COPY deploy/vllm-reasoner/patch-nvfp4/nvfp4_blockwise_w4a16_vllm.py ${VLLM_SITE}/model_executor/layers/quantization/nvfp4_blockwise_w4a16_vllm.py
COPY deploy/vllm-reasoner/patch-nvfp4/quantization__init__.py       ${VLLM_SITE}/model_executor/layers/quantization/__init__.py
COPY deploy/vllm-reasoner/patch-nvfp4/cosmos3.py                    ${VLLM_SITE}/model_executor/models/cosmos3.py

EXPOSE 8000
# vllm-openai's base sets ENTRYPOINT ["vllm","serve"]; clear it so CMD is the whole command.
ENTRYPOINT []
# Reasoning-only: NO --omni (text, not image); --quantization nvfp4_blockwise_w4a16 selects the
# weight-only NVFP4 W4A16 understanding tower (Marlin FP4). NO --enable-layerwise-offload (Marlin
# forbids it). Context/mem caps are operator-set (compose command:).
CMD ["vllm", "serve", "/models/checkpoint", "--host", "0.0.0.0", "--port", "8000", \
     "--served-model-name", "cosmos3-reasoner", \
     "--max-model-len", "8192", "--gpu-memory-utilization", "0.85", \
     "--quantization", "nvfp4_blockwise_w4a16"]
