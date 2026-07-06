"""Host-loop tests for the pure, torch-free context-cap validator (RK-13 / INV-6).

These run in the torch-free host venv. `context_cap.py` MUST import without torch/vllm/transformers
(green here is the proof — the host venv has none). Refs: session_5/specs/context-cap-validator.md.
"""
from __future__ import annotations

import dataclasses

import pytest


def test_module_imports_torch_free():
    # Succeeds in the torch-free host venv only if context_cap imports no torch/vllm/transformers.
    from engines.vllm import context_cap

    for name in (
        "ReasoningErrorCode",
        "ContextCapConfig",
        "ReasoningValidationError",
        "ReasoningValidationFailed",
        "validate_context",
    ):
        assert hasattr(context_cap, name), name


def test_error_code_enum_values():
    from engines.vllm.context_cap import ReasoningErrorCode

    assert {c.name for c in ReasoningErrorCode} == {"CONTEXT_OVER_CAP", "BAD_MAX_TOKENS", "EMPTY_PROMPT"}


def test_config_is_frozen_data():
    from engines.vllm.context_cap import ContextCapConfig

    cfg = ContextCapConfig(max_context_tokens=100, max_output_tokens=10)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.max_context_tokens = 200  # type: ignore[misc]


def test_from_env_default_is_provisional_cap(monkeypatch):
    # The provisional context window is 32768 (EC-R4). S7 (FR-10/INV-12): the output ceiling defaults to
    # the FULL context window — non-truncating — replacing the old fixed 1024 output default.
    monkeypatch.delenv("COSMOS3_REASONER_MAX_CONTEXT", raising=False)
    monkeypatch.delenv("COSMOS3_REASONER_MAX_OUTPUT", raising=False)
    from engines.vllm.context_cap import ContextCapConfig

    cfg = ContextCapConfig.from_env()
    assert cfg.max_context_tokens == 32768
    assert cfg.max_output_tokens == cfg.max_context_tokens  # non-truncating default (no output cap < context)


def test_default_config_allows_output_far_above_old_cap():
    # FR-10/INV-12: under the default config an output far above the old 256/1024 caps is accepted as long
    # as prompt+output fits the context window — the UI no longer truncates reasoning at 256.
    from engines.vllm.context_cap import ContextCapConfig, validate_context

    cfg = ContextCapConfig.from_env()  # default: output ceiling == context window
    assert validate_context(prompt_tokens=100, max_output_tokens=4000, cfg=cfg) is None
    assert validate_context(prompt_tokens=100, max_output_tokens=20000, cfg=cfg) is None


def test_from_env_override(monkeypatch):
    monkeypatch.setenv("COSMOS3_REASONER_MAX_CONTEXT", "65536")
    monkeypatch.setenv("COSMOS3_REASONER_MAX_OUTPUT", "2048")
    from engines.vllm.context_cap import ContextCapConfig

    cfg = ContextCapConfig.from_env()
    assert (cfg.max_context_tokens, cfg.max_output_tokens) == (65536, 2048)


def test_over_cap_combined_budget_rejected():
    # The EC-R4 over-cap anchor: prompt + output exceeds the cap -> CONTEXT_OVER_CAP (not None).
    from engines.vllm.context_cap import ContextCapConfig, ReasoningErrorCode, validate_context

    cfg = ContextCapConfig(max_context_tokens=32768, max_output_tokens=1024)
    err = validate_context(prompt_tokens=32700, max_output_tokens=256, cfg=cfg)
    assert err is not None
    assert err.code is ReasoningErrorCode.CONTEXT_OVER_CAP
    assert err.expected == 32768
    assert err.got == 32956


def test_prompt_alone_over_cap_rejected():
    from engines.vllm.context_cap import ContextCapConfig, ReasoningErrorCode, validate_context

    cfg = ContextCapConfig(max_context_tokens=4096, max_output_tokens=1024)
    err = validate_context(prompt_tokens=5000, max_output_tokens=1, cfg=cfg)
    assert err is not None and err.code is ReasoningErrorCode.CONTEXT_OVER_CAP


def test_within_cap_passes():
    from engines.vllm.context_cap import ContextCapConfig, validate_context

    cfg = ContextCapConfig(max_context_tokens=32768, max_output_tokens=1024)
    assert validate_context(prompt_tokens=1000, max_output_tokens=256, cfg=cfg) is None


def test_at_exact_cap_passes():
    # Boundary: prompt + output == cap is allowed (<= is the rule).
    from engines.vllm.context_cap import ContextCapConfig, validate_context

    cfg = ContextCapConfig(max_context_tokens=4096, max_output_tokens=1024)
    assert validate_context(prompt_tokens=4000, max_output_tokens=96, cfg=cfg) is None


def test_empty_prompt_rejected():
    from engines.vllm.context_cap import ContextCapConfig, ReasoningErrorCode, validate_context

    cfg = ContextCapConfig(max_context_tokens=4096, max_output_tokens=1024)
    err = validate_context(prompt_tokens=0, max_output_tokens=256, cfg=cfg)
    assert err is not None and err.code is ReasoningErrorCode.EMPTY_PROMPT


def test_non_positive_max_output_rejected():
    from engines.vllm.context_cap import ContextCapConfig, ReasoningErrorCode, validate_context

    cfg = ContextCapConfig(max_context_tokens=4096, max_output_tokens=1024)
    err = validate_context(prompt_tokens=10, max_output_tokens=0, cfg=cfg)
    assert err is not None and err.code is ReasoningErrorCode.BAD_MAX_TOKENS


def test_over_ceiling_max_output_rejected():
    # The opt-in operator clamp: when an operator sets a hard output ceiling BELOW the context window,
    # an output over it is rejected. (The DEFAULT ceiling == context window, so this never fires by default.)
    from engines.vllm.context_cap import ContextCapConfig, ReasoningErrorCode, validate_context

    cfg = ContextCapConfig(max_context_tokens=32768, max_output_tokens=1024)
    err = validate_context(prompt_tokens=10, max_output_tokens=2048, cfg=cfg)
    assert err is not None and err.code is ReasoningErrorCode.BAD_MAX_TOKENS


def test_code_precedence_empty_before_bad_max():
    # Empty prompt AND bad max_tokens -> EMPTY_PROMPT wins (checked first), for a stable code.
    from engines.vllm.context_cap import ContextCapConfig, ReasoningErrorCode, validate_context

    cfg = ContextCapConfig(max_context_tokens=4096, max_output_tokens=1024)
    err = validate_context(prompt_tokens=0, max_output_tokens=0, cfg=cfg)
    assert err is not None and err.code is ReasoningErrorCode.EMPTY_PROMPT


def test_code_precedence_bad_max_before_over_cap():
    # Bad max_tokens AND over-cap -> BAD_MAX_TOKENS wins (checked before the cap).
    from engines.vllm.context_cap import ContextCapConfig, ReasoningErrorCode, validate_context

    cfg = ContextCapConfig(max_context_tokens=4096, max_output_tokens=1024)
    err = validate_context(prompt_tokens=5000, max_output_tokens=-1, cfg=cfg)
    assert err is not None and err.code is ReasoningErrorCode.BAD_MAX_TOKENS


def test_error_carries_actionable_fields():
    from engines.vllm.context_cap import ContextCapConfig, validate_context

    cfg = ContextCapConfig(max_context_tokens=4096, max_output_tokens=1024)
    err = validate_context(prompt_tokens=5000, max_output_tokens=10, cfg=cfg)
    assert err is not None
    assert err.message and isinstance(err.message, str)
    assert err.expected == 4096 and err.got == 5010


def test_validation_failed_exception_wraps_error():
    from engines.vllm.context_cap import (
        ContextCapConfig,
        ReasoningValidationFailed,
        validate_context,
    )

    cfg = ContextCapConfig(max_context_tokens=4096, max_output_tokens=1024)
    err = validate_context(prompt_tokens=5000, max_output_tokens=10, cfg=cfg)
    assert err is not None
    exc = ReasoningValidationFailed(err)
    assert exc.error is err
    assert err.code.value in str(exc)
