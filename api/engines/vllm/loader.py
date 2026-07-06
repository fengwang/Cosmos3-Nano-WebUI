"""Reasoner loading + the out-of-process server spec (ACD: Actions at the edge + pure Calculations).

``build_reasoner`` builds the in-process ``vllm.LLM`` for deterministic greedy goldens (the M4 oracle
path); ``server_launch_argv`` assembles the out-of-process ``vllm serve`` argv that the co-residency
contract's handoff uses (clean process kill). Both load the model ONLY from the trusted, operator-set
mount (INV-8) — never a request- or network-supplied path.

Mirroring the oracle's verify-before-serve discipline, ``verify_reasoner_info`` (a pure Calculation
over the observed arch/dtype) refuses to serve anything that is not the ``Cosmos3ForConditionalGeneration``
reasoner at bf16. Heavy imports (torch/vllm) are deferred into functions; the points confirmed against
the live wheel are marked ``# RUNTIME`` (pinned to vllm 0.23.0). Refs: session_5/specs/reasoner-adapter.md.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from engines.base import EngineInfo, Precision
from engines.vllm.adapter import GreedyOutput, VllmReasonerAdapter
from engines.vllm.context_cap import (
    DEFAULT_MAX_CONTEXT_TOKENS,
    DEFAULT_MAX_OUTPUT_TOKENS,
    ContextCapConfig,
)
# The serve cap == the co-residency contract's hard mem-cap (one shared constant — RK-15).
from engines.vllm.coresidency import DEFAULT_GPU_MEMORY_UTILIZATION

# The reasoner is the bf16 understanding tower of the base omni checkpoint (NOT the quantized
# generation checkpoint COSMOS3_MODEL_DIR) — vLLM's WeightsMapper drops the generation tower.
DEFAULT_REASONER_MODEL_DIR = "/data/models/Cosmos3-Nano"
EXPECTED_ARCH = "Cosmos3ForConditionalGeneration"


class ReasonerLoadError(RuntimeError):
    """Raised when the loaded engine is not the confirmed Cosmos3 reasoner at bf16 (never serve it)."""


@dataclass(frozen=True)
class ReasonerConfig:
    """Where/how to load + serve the reasoner (inert Data)."""

    model_dir: str = DEFAULT_REASONER_MODEL_DIR
    max_model_len: int = DEFAULT_MAX_CONTEXT_TOKENS
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS
    gpu_memory_utilization: float = DEFAULT_GPU_MEMORY_UTILIZATION
    dtype: str = "bfloat16"
    seed: int = 123
    served_model_name: str = "cosmos3-reasoner"
    device: str = "cuda"

    @staticmethod
    def from_env() -> "ReasonerConfig":
        """Action: read the (operator-controlled, trusted) mount + serve settings from the environment."""
        return ReasonerConfig(
            model_dir=os.environ.get("COSMOS3_REASONER_MODEL_DIR", DEFAULT_REASONER_MODEL_DIR),
            max_model_len=int(
                os.environ.get("COSMOS3_REASONER_MAX_CONTEXT", str(DEFAULT_MAX_CONTEXT_TOKENS))
            ),
            max_output_tokens=int(
                os.environ.get("COSMOS3_REASONER_MAX_OUTPUT", str(DEFAULT_MAX_OUTPUT_TOKENS))
            ),
            gpu_memory_utilization=float(
                os.environ.get("COSMOS3_REASONER_GPU_MEM_UTIL", str(DEFAULT_GPU_MEMORY_UTILIZATION))
            ),
            dtype=os.environ.get("COSMOS3_REASONER_DTYPE", "bfloat16"),
            seed=int(os.environ.get("COSMOS3_REASONER_SEED", "123")),
            device=os.environ.get("COSMOS3_DEVICE", "cuda"),
        )

    def cap_config(self) -> ContextCapConfig:
        """Calculation: the single public cap derived from this config (max_model_len == the public cap).

        Honors the operator's ``COSMOS3_REASONER_MAX_OUTPUT`` (carried on ``max_output_tokens``) on the
        served path — one cap-derivation rule, no drift vs ``ContextCapConfig.from_env`` (sharded-review M).
        """
        return ContextCapConfig(
            max_context_tokens=self.max_model_len,
            max_output_tokens=min(self.max_output_tokens, self.max_model_len),
        )


def server_launch_argv(cfg: ReasonerConfig) -> list[str]:
    """Pure Calculation: the ``vllm serve`` argv honoring the co-residency contract.

    Carries the trusted model dir, the public cap (``--max-model-len``), the hard memory cap
    (``--gpu-memory-utilization`` — bounds KV pre-allocation, RK-15), bf16, and the served name. No
    request-supplied path is ever embedded (INV-8).
    """
    return [
        "vllm",
        "serve",
        cfg.model_dir,
        "--served-model-name",
        cfg.served_model_name,
        "--max-model-len",
        str(cfg.max_model_len),
        "--gpu-memory-utilization",
        str(cfg.gpu_memory_utilization),
        "--dtype",
        cfg.dtype,
        "--seed",
        str(cfg.seed),
    ]


def verify_reasoner_info(observed_arch: str, observed_dtype: str, model_dir: str) -> EngineInfo:
    """Pure Calculation: confirm the served identity, or raise (we never serve an unconfirmed engine).

    Two gates: the architecture MUST be ``Cosmos3ForConditionalGeneration`` (defeats serving the wrong
    model), and the dtype MUST be bf16 (the reasoner is unquantized — no silent fp16/fp32 downcast).
    """
    if observed_arch != EXPECTED_ARCH:
        raise ReasonerLoadError(
            f"{model_dir}: served architecture {observed_arch!r} is not {EXPECTED_ARCH!r}"
        )
    if "bfloat16" not in observed_dtype.lower() and observed_dtype not in ("bf16",):
        raise ReasonerLoadError(
            f"{model_dir}: reasoner dtype {observed_dtype!r} is not bf16 (the reasoner is unquantized)"
        )
    return EngineInfo(engine="vllm", precision=Precision.BF16, checkpoint_dir=model_dir)


def observe_arch_dtype(llm) -> tuple[str, str]:
    """Action (# RUNTIME, confirmed against vllm 0.23.0): read the loaded engine's arch + dtype."""
    engine = getattr(llm, "llm_engine", llm)
    model_config = getattr(engine, "model_config", None) or getattr(
        getattr(engine, "vllm_config", None), "model_config", None
    )
    hf_config = getattr(model_config, "hf_config", None)
    archs = list(getattr(hf_config, "architectures", None) or [])
    arch = archs[0] if archs else ""
    dtype = str(getattr(model_config, "dtype", ""))
    return arch, dtype


def _data_uri(path: str) -> str:
    """Action: read a trusted-mount media file into a base64 data URI for the vLLM chat API (INV-8)."""
    import base64  # noqa: PLC0415
    import mimetypes  # noqa: PLC0415

    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class _VllmGreedyEngine:
    """The concrete vLLM-backed greedy engine (Action shell; deferred vllm import)."""

    def __init__(self, llm) -> None:
        self._llm = llm

    def generate_greedy(
        self,
        prompt: str,
        *,
        max_tokens: int,
        seed: int,
        image_path: str | None = None,
        video_path: str | None = None,
    ) -> GreedyOutput:
        """Action (# RUNTIME): one greedy generation; text or image/video-conditioned (EC-R2/R3).

        VRAM is sampled GPU-wide (nvidia-smi) because vLLM runs the model in a separate EngineCore
        process — an in-process torch counter would read 0 (confirmed live). Multimodal conditioning
        goes through ``llm.chat`` (applies the chat template + vision-token placeholders); text-only
        uses ``llm.generate``.
        """
        from vllm import SamplingParams  # noqa: PLC0415

        from engines.vllm.coresidency import gpu_memory_used_bytes  # noqa: PLC0415

        params = SamplingParams(temperature=0.0, seed=seed, max_tokens=max_tokens)
        if image_path is None and video_path is None:
            outputs = self._llm.generate([prompt], params)
        else:
            content: list = []
            if image_path is not None:
                content.append({"type": "image_url", "image_url": {"url": _data_uri(image_path)}})
            if video_path is not None:
                content.append({"type": "video_url", "video_url": {"url": _data_uri(video_path)}})
            content.append({"type": "text", "text": prompt})
            outputs = self._llm.chat([{"role": "user", "content": content}], params)
        completion = outputs[0].outputs[0]
        return GreedyOutput(
            text=completion.text,
            output_tokens=len(completion.token_ids),
            vram_peak_bytes=gpu_memory_used_bytes(),
        )


def build_reasoner(cfg: ReasonerConfig) -> VllmReasonerAdapter:
    """Action facade (# RUNTIME): build the in-process ``vllm.LLM`` → verify identity → wrap.

    Loads ONLY from the trusted ``cfg.model_dir`` mount (INV-8). Verification runs on the loaded engine
    before the adapter is returned, so a wrong/mislabeled model fails fast.

    Fail-closed source guard (P6-S4): before wasting a model load, refuse any source whose reasoner-kept
    understanding-tower weights are quantized or missing — e.g. a quantized blockwise checkpoint or a
    non-self-contained bundle. This inspects the ``transformer/`` safetensors headers (torch-free) and
    catches what the post-load bf16 identity gate cannot (it reads the *config* dtype, not the *weight*
    dtype). Refs: session_4/specs/reasoner-source-guard.md.
    """
    from engines.vllm.reasoner_preflight import assert_reasoner_source  # noqa: PLC0415

    assert_reasoner_source(cfg.model_dir)
    from vllm import LLM  # noqa: PLC0415

    llm = LLM(
        model=cfg.model_dir,
        dtype=cfg.dtype,
        max_model_len=cfg.max_model_len,  # forwarded via LLM(**kwargs) → EngineArgs (confirmed, vllm 0.23.0)
        gpu_memory_utilization=cfg.gpu_memory_utilization,
        seed=cfg.seed,
        enforce_eager=True,  # deterministic; no CUDA-graph capture for the greedy goldens
    )
    arch, dtype = observe_arch_dtype(llm)
    info = verify_reasoner_info(arch, dtype, cfg.model_dir)
    return VllmReasonerAdapter(_VllmGreedyEngine(llm), llm.get_tokenizer(), info, cfg.cap_config())
