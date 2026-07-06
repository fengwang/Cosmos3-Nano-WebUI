"""Host (torch-free) test: the adapter validates BEFORE any pipeline/diffusers work (INV-6).

An invalid request must raise ActionValidationFailed and NEVER reach the pipeline. Run on the host
(no torch/diffusers): if generate_action tried to build CosmosActionCondition or call the pipe, it would
fail differently (ImportError / sentinel) — so a clean ActionValidationFailed proves validate-first.
Refs: session_4/specs/action-engine-adapter.md (validation precedes any GPU work).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from engines.base import EngineInfo, Precision
from engines.diffusers_action.adapter import ActionRequest, DiffusersActionAdapter, spec_of
from preprocessing.action_schema import ActionMode, ActionValidationFailed, ErrorCode


class _SentinelPipe:
    """A pipe that fails the test if it is ever called."""

    def __init__(self) -> None:
        self.called = False

    def __call__(self, *args, **kwargs):  # noqa: ANN002, ANN003
        self.called = True
        raise AssertionError("pipeline must not be called for an invalid request")


def _adapter(pipe) -> DiffusersActionAdapter:
    info = EngineInfo(engine="diffusers_action", precision=Precision.NVFP4, checkpoint_dir="/x")
    return DiffusersActionAdapter(pipe, info, device="cpu")


def test_width_mismatch_never_reaches_pipeline():
    pipe = _SentinelPipe()
    bad = ActionRequest(
        mode=ActionMode.FORWARD_DYNAMICS,
        domain_name="av",
        chunk_size=16,
        raw_actions=SimpleNamespace(shape=(16, 10)),  # width 10 -> av expects 9
        image_path="first_frame.png",
    )
    with pytest.raises(ActionValidationFailed) as excinfo:
        _adapter(pipe).generate_action(bad)
    assert excinfo.value.error.code is ErrorCode.WIDTH_MISMATCH
    assert excinfo.value.error.expected == 9 and excinfo.value.error.got == 10
    assert pipe.called is False


def test_unknown_embodiment_never_reaches_pipeline():
    pipe = _SentinelPipe()
    bad = ActionRequest(
        mode=ActionMode.INVERSE_DYNAMICS, domain_name="frobnicator", chunk_size=16, video_path="x.mp4"
    )
    with pytest.raises(ActionValidationFailed) as excinfo:
        _adapter(pipe).generate_action(bad)
    assert excinfo.value.error.code is ErrorCode.UNKNOWN_EMBODIMENT
    assert pipe.called is False


def test_info_property_exposed():
    info = EngineInfo(engine="diffusers_action", precision=Precision.NVFP4, checkpoint_dir="/x")
    adapter = DiffusersActionAdapter(_SentinelPipe(), info, device="cpu")
    assert adapter.info is info


def test_spec_of_reads_2d_width_and_passes_tier():
    req = ActionRequest(
        mode=ActionMode.FORWARD_DYNAMICS, domain_name="agibotworld", chunk_size=16,
        raw_actions=SimpleNamespace(shape=(16, 29)), image_path="x.png", resolution_tier=256,
    )
    spec = spec_of(req)
    assert spec.raw_action_width == 29
    assert spec.resolution_tier == 256
    assert spec.chunk_size == 16
    assert spec.has_image is True and spec.has_video is False


def test_spec_of_malformed_actions_yields_none_width_not_indexerror():
    # 1-D raw_actions -> width None (no IndexError); validate then rejects FD as CONDITION_MISSING.
    req = ActionRequest(
        mode=ActionMode.FORWARD_DYNAMICS, domain_name="av", chunk_size=16,
        raw_actions=SimpleNamespace(shape=(9,)), image_path="x.png",
    )
    assert spec_of(req).raw_action_width is None


def test_malformed_actions_raise_typed_error_not_indexerror():
    pipe = _SentinelPipe()
    bad = ActionRequest(
        mode=ActionMode.FORWARD_DYNAMICS, domain_name="av", chunk_size=16,
        raw_actions=SimpleNamespace(shape=(9,)), image_path="x.png",  # malformed 1-D
    )
    with pytest.raises(ActionValidationFailed) as excinfo:
        _adapter(pipe).generate_action(bad)
    assert excinfo.value.error.code is ErrorCode.CONDITION_MISSING
    assert pipe.called is False
