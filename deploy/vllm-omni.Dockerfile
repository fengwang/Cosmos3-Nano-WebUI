# syntax=docker/dockerfile:1
# vLLM-Omni generation-engine image (MIG-S6). Installs the pinned public fork from the
# immutable MIG-S2 tag (INV-3) and serves an operator-mounted checkpoint on :8000
# (readiness: /v1/models). This image is GPU/heavy: its full build and run are the
# MIG-S8 manual gate — it is intentionally NOT part of the S6 deterministic build
# checks. No weights are ever copied in (INV-2); the checkpoint is a runtime mount.

FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

# MIG-S2 immutable pin: commit SHA (a tag can be force-moved; the commit cannot).
# Commit 697035018b70cef76b974a909d23371a9984c3f2 == tag cosmos3-nano-webui-mig-s2.
ARG VLLM_OMNI_REF=697035018b70cef76b974a909d23371a9984c3f2
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip python3-venv git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Immutable tag/commit — never a bare mutable branch (INV-3). Public HTTPS for reproducibility.
RUN pip install --no-cache-dir --break-system-packages \
      "git+https://github.com/fengwang/vllm-omni.git@${VLLM_OMNI_REF}"

EXPOSE 8000
# NOTE (MIG-S8): confirm the fork's exact OpenAI-compatible serve entrypoint on GPU.
# Overridable via the Compose `command:`; the model path is the in-container mount.
CMD ["python3", "-m", "vllm_omni.entrypoints.openai.api_server", \
     "--model", "/models/checkpoint", "--host", "0.0.0.0", "--port", "8000"]
