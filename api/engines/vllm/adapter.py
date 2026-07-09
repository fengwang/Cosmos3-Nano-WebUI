"""VllmReasonerAdapter — a typed reasoning surface over vLLM (Action shell, torch-free import).

The reasoner is a **sibling** of the generation ``EngineAdapter`` (text→text, not latents/frames),
reusing ``EngineInfo``. ``reason`` is the only Action and it VALIDATES first (INV-6): an over-cap /
empty request raises ``ReasoningValidationFailed`` and NEVER reaches the engine. It is deterministic
under the request's greedy params (INV-10: temperature 0, fixed seed).

The adapter depends only on a small engine-agnostic ``generate_greedy`` surface — the concrete
vLLM-backed engine (and its deferred ``vllm``/``torch`` imports) lives in ``loader.py`` — so this
module imports torch-free and ``reason`` is host-testable with a spy. Refs:
session_5/specs/reasoner-adapter.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from engines.base import EngineInfo
from engines.vllm.context_cap import ContextCapConfig, ReasoningValidationFailed, validate_context


@dataclass(frozen=True)
class ReasoningRequest:
    """One deterministic reasoning request (inert Data).

    ``image_path``/``video_path`` are trusted-mount conditioning paths (EC-R2/EC-R3). The greedy
    params mirror the determinism contract (INV-10) — ``temperature=0`` makes the output reproducible.
    """

    prompt: str
    case_id: str = ""
    image_path: str | None = None
    video_path: str | None = None
    max_output_tokens: int = 256
    temperature: float = 0.0
    seed: int = 123


@dataclass(frozen=True)
class GreedyOutput:
    """What an engine returns for one greedy generation (inert Data crossing the engine seam)."""

    text: str
    output_tokens: int = 0
    vram_peak_bytes: int = 0


@dataclass(frozen=True)
class ReasoningResult:
    """Outputs of one reasoning generation (inert Data the M4 metrics compare).

    ``structured`` is an optional parsed field (e.g. a bbox for EC-R2 grounding — parsed by the
    metrics layer, not the adapter). ``info`` records the engine/precision that produced this result.
    """

    case_id: str
    text: str
    structured: Any | None = None
    prompt_tokens: int = 0
    output_tokens: int = 0
    vram_peak_bytes: int = 0
    info: EngineInfo | None = None


class GreedyEngine(Protocol):
    """The minimal surface the adapter needs (the vLLM-backed impl lives in ``loader.py``)."""

    def generate_greedy(
        self, prompt: str, *, max_tokens: int, seed: int, image_path: str | None = None,
        video_path: str | None = None,
    ) -> GreedyOutput: ...


class Tokenizer(Protocol):
    """A tokenizer exposing ``encode`` (the HF/vLLM tokenizer satisfies this)."""

    def encode(self, text: str) -> list: ...


def count_prompt_tokens(tokenizer: Tokenizer, request: ReasoningRequest) -> int:
    """Action: count the text-prompt tokens — the RK-13 long-context gate.

    Vision-token expansion (EC-R2/R3) is bounded by vLLM's ``max_model_len`` as defense-in-depth; the
    edge cap gates on the text count (a documented v1 limitation — see design.md Step 4).
    """
    return len(tokenizer.encode(request.prompt))


class VllmReasonerAdapter:
    """Reasoning over vLLM's ``Cosmos3ForConditionalGeneration`` (INV-2). One resident engine."""

    def __init__(
        self, engine: GreedyEngine, tokenizer: Tokenizer, info: EngineInfo, cap: ContextCapConfig
    ) -> None:
        self._engine = engine
        self._tokenizer = tokenizer
        self._info = info
        self._cap = cap

    @property
    def info(self) -> EngineInfo:
        return self._info

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        """Validate (INV-6) then run one deterministic greedy generation (INV-10).

        Raises ``ReasoningValidationFailed`` (→ 422) BEFORE any engine call when the request exceeds
        the public context cap (or is empty / has a bad output budget).
        """
        prompt_tokens = count_prompt_tokens(self._tokenizer, request)
        error = validate_context(prompt_tokens, request.max_output_tokens, self._cap)
        if error is not None:
            raise ReasoningValidationFailed(error)

        # ---- past this point: the request fits the public window; run greedy ----
        out = self._engine.generate_greedy(
            request.prompt,
            max_tokens=request.max_output_tokens,
            seed=request.seed,
            image_path=request.image_path,
            video_path=request.video_path,
        )
        return ReasoningResult(
            case_id=request.case_id or "reason",
            text=out.text,
            prompt_tokens=prompt_tokens,
            output_tokens=out.output_tokens,
            vram_peak_bytes=out.vram_peak_bytes,
            info=self._info,
        )
