"""Host-loop conformance tests for the VllmReasonerAdapter + loader (torch-free).

The adapter depends on a small engine-agnostic ``generate_greedy`` surface (the concrete vLLM-backed
impl + its deferred ``vllm`` import live in the loader), so these run in the torch-free host venv with
a spy engine — proving validate-before-dispatch without a GPU. Refs: session_5/specs/reasoner-adapter.md.
"""
from __future__ import annotations

import dataclasses

import pytest


# ---- test doubles (duck-typed to the adapter's small seam) -------------------------------------

class SpyTokenizer:
    def __init__(self, n: int) -> None:
        self.n = n

    def encode(self, text: str) -> list:
        return list(range(self.n))


class SpyEngine:
    def __init__(self) -> None:
        self.calls = 0
        self.last = None
        self.last_image = None
        self.last_video = None

    def generate_greedy(
        self, prompt: str, *, max_tokens: int, seed: int, image_path=None, video_path=None
    ):
        from engines.vllm.adapter import GreedyOutput

        self.calls += 1
        self.last = (prompt, max_tokens, seed)
        self.last_image = image_path
        self.last_video = video_path
        return GreedyOutput(text="a robotic arm", output_tokens=3, vram_peak_bytes=123)


def _adapter(*, prompt_token_count: int, cap_ctx: int = 100, cap_out: int = 50):
    from engines.base import EngineInfo, Precision
    from engines.vllm.adapter import VllmReasonerAdapter
    from engines.vllm.context_cap import ContextCapConfig

    engine = SpyEngine()
    info = EngineInfo(engine="vllm", precision=Precision.BF16, checkpoint_dir="/data/models/Cosmos3-Nano")
    cap = ContextCapConfig(max_context_tokens=cap_ctx, max_output_tokens=cap_out)
    adapter = VllmReasonerAdapter(engine, SpyTokenizer(prompt_token_count), info, cap)
    return adapter, engine


# ---- import / Data conformance -----------------------------------------------------------------

def test_modules_import_torch_free():
    from engines.vllm import adapter, loader

    assert hasattr(adapter, "VllmReasonerAdapter")
    assert hasattr(adapter, "ReasoningRequest") and hasattr(adapter, "ReasoningResult")
    assert hasattr(loader, "ReasonerConfig") and hasattr(loader, "server_launch_argv")
    assert hasattr(loader, "build_reasoner") and hasattr(loader, "verify_reasoner_info")


def test_reasoning_records_are_frozen():
    from engines.vllm.adapter import ReasoningRequest, ReasoningResult

    req = ReasoningRequest(prompt="p")
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.prompt = "q"  # type: ignore[misc]
    res = ReasoningResult(case_id="c", text="t")
    with pytest.raises(dataclasses.FrozenInstanceError):
        res.text = "u"  # type: ignore[misc]


def test_greedy_knobs_pinned_inv10():
    from engines.vllm.adapter import ReasoningRequest

    req = ReasoningRequest(prompt="p")
    assert req.temperature == 0.0 and req.seed == 123


def test_reasoner_config_frozen_and_from_env_defaults(monkeypatch):
    for var in ("COSMOS3_REASONER_MODEL_DIR", "COSMOS3_REASONER_MAX_CONTEXT", "COSMOS3_REASONER_GPU_MEM_UTIL"):
        monkeypatch.delenv(var, raising=False)
    from engines.vllm.loader import ReasonerConfig

    cfg = ReasonerConfig.from_env()
    assert cfg.model_dir == "/data/models/Cosmos3-Nano"   # the bf16 understanding tower (not the quant ckpt)
    assert cfg.max_model_len == 32768
    assert cfg.dtype == "bfloat16"
    assert 0.0 < cfg.gpu_memory_utilization < 1.0
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.model_dir = "/elsewhere"  # type: ignore[misc]


# ---- server launch argv (pure Calculation) -----------------------------------------------------

def test_server_launch_argv_carries_cap_and_memcap():
    from engines.vllm.loader import ReasonerConfig, server_launch_argv

    cfg = ReasonerConfig(
        model_dir="/data/models/Cosmos3-Nano", max_model_len=32768,
        gpu_memory_utilization=0.45, dtype="bfloat16", served_model_name="cosmos3-reasoner",
    )
    argv = server_launch_argv(cfg)
    joined = " ".join(argv)
    assert "/data/models/Cosmos3-Nano" in argv
    assert "--max-model-len" in argv and "32768" in argv
    assert "--gpu-memory-utilization" in argv and "0.45" in argv
    assert "--dtype" in argv and "bfloat16" in argv
    assert "--served-model-name" in argv and "cosmos3-reasoner" in argv
    # the served model dir is the only path; no surprise request-supplied path is embedded
    assert "serve" in joined


# ---- validate-before-dispatch (INV-6) -----------------------------------------------------------

def test_over_cap_request_never_calls_engine():
    from engines.vllm.adapter import ReasoningRequest
    from engines.vllm.context_cap import ReasoningValidationFailed

    adapter, engine = _adapter(prompt_token_count=200, cap_ctx=100, cap_out=50)  # 200 > 100 cap
    with pytest.raises(ReasoningValidationFailed) as ei:
        adapter.reason(ReasoningRequest(prompt="long…", max_output_tokens=10))
    assert ei.value.error.code.value == "context_over_cap"
    assert engine.calls == 0  # the engine was NEVER reached


def test_valid_request_calls_engine_once_and_records_provenance():
    from engines.base import Precision
    from engines.vllm.adapter import ReasoningRequest

    adapter, engine = _adapter(prompt_token_count=5, cap_ctx=32768, cap_out=1024)
    result = adapter.reason(ReasoningRequest(prompt="hi", case_id="EC-R1", max_output_tokens=16, seed=123))
    assert engine.calls == 1
    assert engine.last == ("hi", 16, 123)            # greedy params threaded through
    assert result.text == "a robotic arm"
    assert result.case_id == "EC-R1"
    assert result.prompt_tokens == 5
    assert result.output_tokens == 3
    assert result.vram_peak_bytes == 123
    assert result.info is not None and result.info.engine == "vllm" and result.info.precision is Precision.BF16


# ---- engine identity verification (never serve an unconfirmed engine) ---------------------------

def test_verify_reasoner_info_accepts_cosmos3_bf16():
    from engines.base import Precision
    from engines.vllm.loader import verify_reasoner_info

    info = verify_reasoner_info("Cosmos3ForConditionalGeneration", "torch.bfloat16", "/data/models/Cosmos3-Nano")
    assert info.engine == "vllm" and info.precision is Precision.BF16
    assert info.checkpoint_dir == "/data/models/Cosmos3-Nano"


def test_verify_reasoner_info_rejects_wrong_arch():
    from engines.vllm.loader import ReasonerLoadError, verify_reasoner_info

    with pytest.raises(ReasonerLoadError):
        verify_reasoner_info("Qwen3VLForConditionalGeneration", "torch.bfloat16", "/x")


def test_verify_reasoner_info_rejects_non_bf16():
    from engines.vllm.loader import ReasonerLoadError, verify_reasoner_info

    with pytest.raises(ReasonerLoadError):
        verify_reasoner_info("Cosmos3ForConditionalGeneration", "torch.float16", "/x")


# ---- token counting (Action seam) ---------------------------------------------------------------

def test_count_prompt_tokens_uses_tokenizer():
    from engines.vllm.adapter import ReasoningRequest, count_prompt_tokens

    assert count_prompt_tokens(SpyTokenizer(7), ReasoningRequest(prompt="whatever")) == 7


def test_reason_forwards_multimodal_paths_to_engine():
    # EC-R2/R3: the conditioning image/video path must reach the engine (the multimodal seam).
    from engines.vllm.adapter import ReasoningRequest

    adapter, engine = _adapter(prompt_token_count=5, cap_ctx=32768, cap_out=1024)
    adapter.reason(ReasoningRequest(prompt="describe", image_path="/data/models/x.png", max_output_tokens=8))
    assert engine.last_image == "/data/models/x.png"
    assert engine.last_video is None
