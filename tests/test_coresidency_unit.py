"""Host-loop tests for the co-residency contract + its pure VRAM verdicts (torch-free).

The contract is Data; the verdicts (`within_budget`, `handoff_ok`) are pure Calculations over a
recorded VRAM trace, so the OOM-free proof is testable Data — including the anti-vacuous guard that
defeats the "handoff works only because generation was never loaded" adversarial case (RK-15).
Refs: session_5/specs/co-residency-contract.md.
"""
from __future__ import annotations

import dataclasses

import pytest

GiB = 1024**3


def test_module_imports_torch_free():
    from engines.vllm import coresidency

    for name in ("CoResidencyContract", "VramSample", "within_budget", "handoff_ok"):
        assert hasattr(coresidency, name), name


def test_contract_declares_stop_start_process_kill():
    from engines.vllm.coresidency import CoResidencyContract

    c = CoResidencyContract()
    assert c.mechanism == "stop_start"
    assert c.eviction == "process_kill"
    assert c.vram_budget_bytes == 32 * GiB
    assert 0.0 < c.gpu_memory_utilization < 1.0


def test_contract_is_frozen():
    from engines.vllm.coresidency import CoResidencyContract

    with pytest.raises(dataclasses.FrozenInstanceError):
        CoResidencyContract().mechanism = "mem_cap"  # type: ignore[misc]


def test_contract_memcap_equals_loader_serve_cap():
    # The serve spec MUST carry the contract's hard mem-cap (one shared constant, not a coincidence).
    from engines.vllm.coresidency import CoResidencyContract
    from engines.vllm.loader import ReasonerConfig, server_launch_argv

    c = CoResidencyContract()
    assert ReasonerConfig().gpu_memory_utilization == c.gpu_memory_utilization
    assert str(c.gpu_memory_utilization) in server_launch_argv(ReasonerConfig())


def test_vram_sample_is_frozen():
    from engines.vllm.coresidency import VramSample

    s = VramSample(label="vllm_up", resident_bytes=10 * GiB)
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.resident_bytes = 0  # type: ignore[misc]


def test_within_budget():
    from engines.vllm.coresidency import VramSample, within_budget

    under = [VramSample("a", 10 * GiB), VramSample("b", 31 * GiB)]
    over = [VramSample("a", 10 * GiB), VramSample("b", 33 * GiB)]
    assert within_budget(under, 32 * GiB) is True
    assert within_budget(over, 32 * GiB) is False


def _real_cycle():
    from engines.vllm.coresidency import VramSample

    return [
        VramSample("vllm_up", 14 * GiB),
        VramSample("vllm_down", GiB // 5),       # ~0.2 GiB — eviction freed the KV cache
        VramSample("generation_up", 12 * GiB),   # the OTHER plane genuinely loaded
        VramSample("generation_down", GiB // 5),
        VramSample("vllm_up", 14 * GiB),
    ]


def test_handoff_ok_accepts_a_real_cycle():
    from engines.vllm.coresidency import handoff_ok

    assert handoff_ok(_real_cycle(), 32 * GiB, idle_bytes=GiB) is True


def test_handoff_ok_rejects_vacuous_trace_without_generation():
    # The "handoff works only because generation was never loaded" adversarial case.
    from engines.vllm.coresidency import VramSample, handoff_ok

    vacuous = [VramSample("vllm_up", 14 * GiB), VramSample("vllm_down", GiB // 5)]
    assert handoff_ok(vacuous, 32 * GiB, idle_bytes=GiB) is False


def test_handoff_ok_rejects_trivial_reasoner_footprint():
    # Symmetric anti-vacuous guard: the reasoner (vllm_up) must also genuinely have resided (RK-15).
    from engines.vllm.coresidency import VramSample, handoff_ok

    stub_reasoner = [
        VramSample("vllm_up", GiB // 10),         # ~0.1 GiB — the reasoner did not genuinely load
        VramSample("vllm_down", GiB // 5),
        VramSample("generation_up", 12 * GiB),
    ]
    assert handoff_ok(stub_reasoner, 32 * GiB, idle_bytes=GiB, min_generation_bytes=GiB) is False


def test_handoff_ok_rejects_trivial_generation_footprint():
    # A present-but-trivial generation_up sample (a stub that never really loaded) MUST fail (RK-15).
    from engines.vllm.coresidency import VramSample, handoff_ok

    stub = [
        VramSample("vllm_up", 14 * GiB),
        VramSample("vllm_down", GiB // 5),
        VramSample("generation_up", GiB // 10),   # ~0.1 GiB — the plane did not genuinely load
    ]
    assert handoff_ok(stub, 32 * GiB, idle_bytes=GiB, min_generation_bytes=GiB) is False


def test_handoff_ok_rejects_eviction_that_did_not_free():
    from engines.vllm.coresidency import VramSample, handoff_ok

    not_freed = [
        VramSample("vllm_up", 14 * GiB),
        VramSample("vllm_down", 20 * GiB),       # <= budget but > idle: the kill did NOT release VRAM
        VramSample("generation_up", 12 * GiB),
    ]
    assert handoff_ok(not_freed, 32 * GiB, idle_bytes=GiB) is False


def test_handoff_ok_rejects_over_budget_sample():
    from engines.vllm.coresidency import VramSample, handoff_ok

    over = [
        VramSample("vllm_up", 14 * GiB),
        VramSample("vllm_down", GiB // 5),
        VramSample("generation_up", 33 * GiB),   # exceeds the 32 GiB budget
    ]
    assert handoff_ok(over, 32 * GiB, idle_bytes=GiB) is False


def test_parse_smi_used_mib():
    # Pure parser for `nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits` (MiB).
    from engines.vllm.coresidency import _parse_smi_used_mib

    assert _parse_smi_used_mib("18\n") == 18
    assert _parse_smi_used_mib("21026\n") == 21026
    assert _parse_smi_used_mib("") == 0
    assert _parse_smi_used_mib("123\n456\n") == 123  # first GPU only
