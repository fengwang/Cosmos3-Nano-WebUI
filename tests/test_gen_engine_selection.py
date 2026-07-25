"""Spec: generation-engine-integration — COSMOS3_GEN_ENGINE selects the worker + job_work together.

Host-testable: constructing a ContainerPlaneWorker / SubprocessPlaneWorker has no side effects
(no docker, no subprocess) until the orchestrator calls start().
"""
from __future__ import annotations

from app.main import _select_gen_work, default_worker_factory
from engines.vllm_omni.work import vllm_omni_work
from jobs.gen_client import work as gen_plane_work
from orchestrator.container import ContainerPlaneWorker
from orchestrator.planes import Plane, ProbeKind
from orchestrator.residency import ResidencyId
from orchestrator.worker import SubprocessPlaneWorker

_GEN = ResidencyId(Plane.GENERATION, "fp8-blockwise")
_REASON = ResidencyId(Plane.REASONING, None)


def test_default_engine_selects_container_worker(monkeypatch):
    monkeypatch.delenv("COSMOS3_GEN_ENGINE", raising=False)  # default = vllm_omni
    monkeypatch.setenv("COSMOS3_VLLM_OMNI_URL", "http://vllm-omni:8000")
    monkeypatch.setenv("COSMOS3_GEN_CONTAINER", "cosmos3-vllm-omni")
    assert isinstance(default_worker_factory(_GEN), ContainerPlaneWorker)


def test_diffusers_engine_selects_subprocess_worker(monkeypatch):
    monkeypatch.setenv("COSMOS3_GEN_ENGINE", "diffusers")
    assert isinstance(default_worker_factory(_GEN), SubprocessPlaneWorker)


def test_reasoning_branch_serves_via_reasoner_container(monkeypatch):
    # AM-S2: the REASONING branch now builds a vllm-reasoner CONTAINER worker (zero BF16 — the
    # quantized understanding tower served via `--quantization fp8_blockwise_w8a16`), NOT an in-api
    # subprocess. So the api image needs no torch/vLLM/WITH_REASONING. Independent of the gen engine;
    # the single-slot FSM still evicts-before-loads vs generation (INV-5), eviction = container stop.
    monkeypatch.setenv("COSMOS3_VLLM_REASONER_URL", "http://vllm-reasoner:8000")
    monkeypatch.setenv("COSMOS3_REASONER_CONTAINER", "cosmos3-nano-webui-vllm-reasoner")
    for engine in ("vllm_omni", "diffusers"):
        monkeypatch.setenv("COSMOS3_GEN_ENGINE", engine)
        w = default_worker_factory(_REASON)
        assert isinstance(w, ContainerPlaneWorker)                 # container, not subprocess
        assert not isinstance(w, SubprocessPlaneWorker)
        assert w._spec.plane is Plane.REASONING
        assert w._spec.argv == ()                                  # docker-managed: no argv
        assert w._spec.probe_kind is ProbeKind.HTTP
        assert w._spec.probe_target == "http://vllm-reasoner:8000/v1/models"
        assert w._controller._name == "cosmos3-nano-webui-vllm-reasoner"  # operator-set container


def test_unknown_engine_value_fails_fast(monkeypatch):
    import pytest
    monkeypatch.setenv("COSMOS3_GEN_ENGINE", "vllm-omni")  # common typo (hyphen)
    with pytest.raises(ValueError, match="COSMOS3_GEN_ENGINE"):
        default_worker_factory(_GEN)
    with pytest.raises(ValueError):
        _select_gen_work()


def test_job_work_selection_matches_engine(monkeypatch):
    monkeypatch.setenv("COSMOS3_GEN_ENGINE", "vllm_omni")
    assert _select_gen_work() is vllm_omni_work
    monkeypatch.setenv("COSMOS3_GEN_ENGINE", "diffusers")
    assert _select_gen_work() is gen_plane_work
