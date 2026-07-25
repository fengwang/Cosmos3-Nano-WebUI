"""AM-S4: the legacy BF16 reasoning surface is deleted (REMOVED requirements).

Spec: docs/session_4/specs/unified-fp8-allmodes-stack.md (REMOVED Requirements).
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_reasoning_overlay_file_deleted():
    assert not (ROOT / "deploy/docker-compose.reasoning.yml").exists()


def test_with_reasoning_build_split_removed():
    assert "WITH_REASONING" not in (ROOT / "deploy/api.Dockerfile").read_text()


def test_up_fp8_reasoning_target_retired():
    assert "up-fp8-reasoning" not in (ROOT / "Makefile").read_text()


def test_bf16_env_removed_from_example():
    env = (ROOT / ".env.example").read_text()
    for var in ("COSMOS3_BASE_DIR", "COSMOS3_REASONER_MODEL_DIR", "COSMOS3_VLLM_BIN"):
        assert var not in env, f"legacy BF16 env still present in .env.example: {var}"


def test_api_dockerfile_is_lean_torch_free():
    """The default api image installs no torch/vLLM and uses no CUDA base (AM-S4 §Dockerfile)."""
    df = (ROOT / "deploy/api.Dockerfile").read_text()
    low = df.lower()
    assert "nvidia/cuda" not in low, "api image must not use a CUDA base"
    assert "pip install vllm" not in low, "api image must not install vLLM"
    assert "extra oracle" not in low, "api image must not install the torch (oracle) extra"
    assert "uv sync --frozen --no-dev" in df, "api image should do a lean, frozen uv sync"
