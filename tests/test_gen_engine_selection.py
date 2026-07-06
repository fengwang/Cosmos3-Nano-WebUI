"""Spec: generation-engine-integration — COSMOS3_GEN_ENGINE selects the worker + job_work together.

Host-testable: constructing a ContainerPlaneWorker / SubprocessPlaneWorker has no side effects
(no docker, no subprocess) until the orchestrator calls start().
"""
from __future__ import annotations

from app.main import _select_gen_work, default_worker_factory
from engines.vllm_omni.work import vllm_omni_work
from jobs.gen_client import work as gen_plane_work
from orchestrator.container import ContainerPlaneWorker
from orchestrator.planes import Plane
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


def test_reasoning_branch_unchanged_under_either_engine(monkeypatch):
    # R-11: the factory's REASONING branch must be unchanged by the S4 refactor — not just the
    # worker class, but the spec it builds (INV-7 parent-env stripping + the operator vLLM bin).
    monkeypatch.setenv("COSMOS3_VLLM_BIN", "/opt/vllm-venv/bin/vllm")
    for engine in ("vllm_omni", "diffusers"):
        monkeypatch.setenv("COSMOS3_GEN_ENGINE", engine)
        w = default_worker_factory(_REASON)
        assert isinstance(w, SubprocessPlaneWorker)
        assert w._spec.strip_parent_env is True                    # INV-7 env isolation preserved
        assert w._spec.argv[0] == "/opt/vllm-venv/bin/vllm"        # operator-set bin, not literal "vllm"


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
