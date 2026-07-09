"""Pure, torch-free public context-cap validator for the reasoning plane (ACD: Data + Calculation).

The reasoner can address 256K positions, but KV-cache pressure on the 32 GB 5090 makes that
infeasible (RK-13): ~144 KiB/token bf16 KV against ~16 GB of reasoner weights. So the *public*
context window is a config-grounded cap (the vLLM ``max_model_len``), and an over-cap request is
rejected with a typed error that maps to **422 before any engine call** (INV-6).

This module is deliberately torch-free at import: it takes an already-counted ``prompt_tokens``
(token counting is an Action owned by the adapter) and decides Ok | typed error. The single public
Calculation is ``validate_context``. Refs: session_5/specs/context-cap-validator.md.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

# The public context window (== the vLLM ``max_model_len``), calibrated by the EC-R4 near-cap VRAM
# measurement (RK-13). S7 (FR-10/INV-12): output is NOT truncated below this window — the output ceiling
# defaults to the full context window, so the combined ``prompt+output ≤ max_context_tokens`` is the only
# length bound by default. An operator MAY set ``COSMOS3_REASONER_MAX_OUTPUT`` below the window to opt
# into a hard output clamp (kept as a feature; no longer the truncating 1024 default).
DEFAULT_MAX_CONTEXT_TOKENS = 32768
DEFAULT_MAX_OUTPUT_TOKENS = DEFAULT_MAX_CONTEXT_TOKENS


class ReasoningErrorCode(Enum):
    """The reason a reasoning request was rejected at the edge (no string blindness)."""

    EMPTY_PROMPT = "empty_prompt"
    BAD_MAX_TOKENS = "bad_max_tokens"
    CONTEXT_OVER_CAP = "context_over_cap"


@dataclass(frozen=True)
class ContextCapConfig:
    """The public context window (inert Data). ``max_context_tokens`` == the vLLM ``max_model_len``."""

    max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS

    @staticmethod
    def from_env() -> "ContextCapConfig":
        """Action: read the operator-controlled cap from the environment (the only impure member)."""
        return ContextCapConfig(
            max_context_tokens=int(
                os.environ.get("COSMOS3_REASONER_MAX_CONTEXT", str(DEFAULT_MAX_CONTEXT_TOKENS))
            ),
            max_output_tokens=int(
                os.environ.get("COSMOS3_REASONER_MAX_OUTPUT", str(DEFAULT_MAX_OUTPUT_TOKENS))
            ),
        )


@dataclass(frozen=True)
class ReasoningValidationError:
    """A structured, 422-able rejection (inert Data — no bool/null blindness)."""

    code: ReasoningErrorCode
    message: str
    expected: int | None = None
    got: int | None = None


class ReasoningValidationFailed(Exception):
    """Raised by the adapter to abort BEFORE any engine call; carries the typed error (→ 422)."""

    def __init__(self, error: ReasoningValidationError) -> None:
        self.error = error
        super().__init__(f"{error.code.value}: {error.message}")


def validate_context(
    prompt_tokens: int, max_output_tokens: int, cfg: ContextCapConfig
) -> ReasoningValidationError | None:
    """Pure Calculation: decide whether a request fits the public window. ``None`` == Ok.

    Deterministic precedence (so the returned code is stable): EMPTY_PROMPT → BAD_MAX_TOKENS →
    CONTEXT_OVER_CAP. The cap is on the **combined** budget ``prompt_tokens + max_output_tokens``
    (== the vLLM ``max_model_len`` bound), so a prompt that alone exceeds the cap is also rejected.
    """
    if prompt_tokens <= 0:
        return ReasoningValidationError(
            code=ReasoningErrorCode.EMPTY_PROMPT,
            message="prompt is empty (zero tokens); supply a non-empty prompt",
            got=prompt_tokens,
        )
    if max_output_tokens <= 0 or max_output_tokens > cfg.max_output_tokens:
        return ReasoningValidationError(
            code=ReasoningErrorCode.BAD_MAX_TOKENS,
            message=f"max_output_tokens must be in 1..{cfg.max_output_tokens}",
            expected=cfg.max_output_tokens,
            got=max_output_tokens,
        )
    total = prompt_tokens + max_output_tokens
    if total > cfg.max_context_tokens:
        return ReasoningValidationError(
            code=ReasoningErrorCode.CONTEXT_OVER_CAP,
            message=(
                f"prompt+output tokens ({total}) exceed the {cfg.max_context_tokens}-token "
                "public context cap"
            ),
            expected=cfg.max_context_tokens,
            got=total,
        )
    return None
