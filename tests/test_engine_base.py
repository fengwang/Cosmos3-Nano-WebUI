"""Host-loop tests for the EngineAdapter interface.

These run in the torch-free host venv (S1's fast loop). The interface module MUST be
importable without torch — green here is the proof (the host venv has no torch). Refs:
session_2/specs/engine-adapter-interface.md.
"""
from __future__ import annotations

import dataclasses

import pytest


def test_base_module_imports_without_torch():
    # Succeeds in the torch-free host venv only if base.py imports no torch at module scope.
    from engines import base

    for name in ("EngineAdapter", "Precision", "GenerationRequest", "GenerationResult", "EngineInfo"):
        assert hasattr(base, name), name


def test_precision_is_a_typed_enum():
    from engines.base import Precision

    assert {p.name for p in Precision} == {"NVFP4", "FP8", "BF16"}


def test_generation_records_are_frozen():
    from engines.base import EngineInfo, GenerationRequest, Precision

    req = GenerationRequest(mode="t2v", prompt="p")
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.prompt = "q"  # type: ignore[misc]

    info = EngineInfo(engine="diffusers_oracle", precision=Precision.NVFP4, checkpoint_dir="/x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        info.precision = Precision.FP8  # type: ignore[misc]


def test_engine_adapter_is_abstract():
    from engines.base import EngineAdapter

    with pytest.raises(TypeError):
        EngineAdapter()  # type: ignore[abstract]  # abstract — generate/info unimplemented


def test_generation_request_pins_inv10_determinism_knobs():
    # INV-10 fixed params — pin the values in the fast host loop (not only via the GPU golden SHA).
    from engines.base import GenerationRequest

    req = GenerationRequest(mode="t2v")
    assert (req.seed, req.flow_shift, req.guidance_scale, req.num_inference_steps) == (123, 10.0, 6.0, 8)
    assert (req.num_frames, req.height, req.width) == (1, 480, 480)


def test_loader_unipc_flow_shift_constant():
    # loader imports torch-free; the scheduler flow_shift (INV-10) must stay 10.0.
    from engines.diffusers_oracle.loader import UNIPC_FLOW_SHIFT

    assert UNIPC_FLOW_SHIFT == 10.0


def test_observe_precision_discriminates_by_double_scale():
    # Pure discriminator over a synthetic state_dict (no torch tensors needed) — host-runnable.
    from engines.base import Precision
    from engines.diffusers_oracle.loader import observe_precision

    class _FakeModule:
        def __init__(self, keys):
            self._keys = keys

        def state_dict(self):
            return {k: None for k in self._keys}

    nvfp4 = [f"layers.{i}.weight_quantizer._amax" for i in range(3)] + ["layers.0.weight_quantizer._double_scale"]
    precision, n = observe_precision(_FakeModule(nvfp4))
    assert precision is Precision.NVFP4 and n == 3  # _double_scale present -> NVFP4

    fp8 = [f"layers.{i}.weight_quantizer._amax" for i in range(2)]  # no _double_scale
    precision, n = observe_precision(_FakeModule(fp8))
    assert precision is Precision.FP8 and n == 2


def test_verify_precision_rejects_wrong_quantized_count():
    # A partial/corrupt restore that still trips the precision discriminator MUST be rejected.
    from engines.diffusers_oracle.loader import OraclePrecisionError, verify_precision

    class _FakeModule:
        def __init__(self, keys):
            self._keys = keys

        def state_dict(self):
            return {k: None for k in self._keys}

    # NVFP4-looking (has _double_scale, matches the declared recipe) but only 3 quantized modules.
    keys = [f"l{i}.weight_quantizer._amax" for i in range(3)] + ["l0.weight_quantizer._double_scale"]
    cfg = {"recipe": "nvfp4_awq", "scale_layout": {"granularity": "per-block-16"}}
    with pytest.raises(OraclePrecisionError):
        verify_precision(_FakeModule(keys), cfg, "/fake", expected_quantized=505)
