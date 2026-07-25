"""The single-GPU co-residency contract + pure VRAM verdicts (ACD: Data + Calculations).

This is the contract the **S6 orchestrator** must honor (S5 documents + measures it; S6 implements it).
Chosen mechanism (D-ORCH / Q2): vLLM runs as an **out-of-process** server with a hard
``gpu_memory_utilization`` cap, and the OOM-free swap is achieved by **evicting** the resident plane for
full VRAM release before the next plane loads — never concurrent co-residency. Eviction is a container
STOP for the vllm-omni/vllm-reasoner containers (AM-S2/S4) or a process kill for the dormant subprocess
path; the manager's post-evict VRAM gate is the real guarantee. The reasoner (an **FP8-quantized**
understanding tower served off the SAME checkpoint as of AM-S2 — KV-cache-dominated at 0.85 util, ≈26 GiB,
not ~16 GB BF16 base weights) and the generation stack cannot both stay hot in 32 GB (D3), and the
untiled VAE-decode peak (D4/RK-08) makes mem-cap co-residency infeasible.

``within_budget`` / ``handoff_ok`` are pure Calculations over a recorded VRAM trace, so the OOM-free
proof is testable Data — including the anti-vacuous guard (the generation plane must actually have
loaded) that defeats the "handoff works only because generation was never loaded" case (RK-15).
This module is torch-free at import. Refs: session_5/specs/co-residency-contract.md.
"""
from __future__ import annotations

from dataclasses import dataclass

# Hard memory cap on the resident reasoner (CALIBRATED live, S5; footprint reconciled AM-S4/R-08): vLLM
# pre-allocates its KV cache by this fraction. As of AM-S2 the reasoner is the **FP8-quantized**
# understanding tower served off the SAME quantized checkpoint (no ~16 GB BF16 base), so at 0.85 the
# resident ≈ 26 GiB is **KV-cache-dominated**, not BF16 weights (still ≤ 32 GiB, ~6 GiB headroom). The
# planes never CO-reside (D-ORCH stop/start); VRAM for the next plane is freed by **eviction** — a
# container STOP for the vllm-omni/vllm-reasoner containers (AM-S2/S4), or a process kill for the dormant
# subprocess path — with the manager's post-evict VRAM gate as the real guarantee, not this cap. Both the
# reasoner's serve spec (test_contract_memcap_equals_loader_serve_cap) and the live vllm-reasoner compose
# command (AM-S4 test_reasoner_util_matches_contract) carry this exact value — one shared constant.
DEFAULT_GPU_MEMORY_UTILIZATION = 0.85
VRAM_BUDGET_BYTES = 32 * 1024**3

# Trace labels the handoff harness emits; the verdicts key off these (no string blindness elsewhere).
VLLM_UP = "vllm_up"
VLLM_DOWN = "vllm_down"
GENERATION_UP = "generation_up"
GENERATION_DOWN = "generation_down"


@dataclass(frozen=True)
class CoResidencyContract:
    """The documented contract the S6 orchestrator MUST honor (inert Data)."""

    mechanism: str = "stop_start"
    # Live all-modes path: eviction is a container STOP (ContainerPlaneWorker.evict → docker stop) for the
    # vllm-omni/vllm-reasoner containers (AM-S2/S4). The dormant in-process subprocess path uses a
    # process kill; both free VRAM before the next plane loads (the manager's post-evict gate is the real
    # guarantee). Reconciled AM-S4/R-08 (was "process_kill" — accurate only for the subprocess path).
    eviction: str = "container_stop"
    vram_budget_bytes: int = VRAM_BUDGET_BYTES
    gpu_memory_utilization: float = DEFAULT_GPU_MEMORY_UTILIZATION


@dataclass(frozen=True)
class VramSample:
    """One step of a handoff VRAM trace (inert Data). ``resident_bytes`` is GPU-wide (nvidia-smi)."""

    label: str
    resident_bytes: int


def within_budget(trace: list[VramSample], budget: int) -> bool:
    """Pure Calculation: every sampled VRAM peak stays within the budget (the OOM-free invariant)."""
    return all(sample.resident_bytes <= budget for sample in trace)


def handoff_ok(
    trace: list[VramSample], budget: int, *, idle_bytes: int, min_generation_bytes: int = 1024**3
) -> bool:
    """Pure Calculation: the stop/start handoff is OOM-free **and** genuinely exercised.

    True iff: (1) every sample is within budget; (2) **both** a ``vllm_up`` and a ``generation_up`` sample
    are present, each with a non-trivial resident footprint (``>= min_generation_bytes``) — both planes
    actually LOADED, not stubs (anti-vacuous; defeats the "a plane was never loaded" adversarial case,
    RK-15); and (3) every post-kill ``vllm_down`` sample is ≤ ``idle_bytes`` — the process kill really
    released the KV cache (defeats a fake eviction).
    """
    if not within_budget(trace, budget):
        return False
    for label in (VLLM_UP, GENERATION_UP):  # both planes must genuinely have resided (not stubs)
        ups = [sample for sample in trace if sample.label == label]
        if not ups or any(sample.resident_bytes < min_generation_bytes for sample in ups):
            return False
    downs = [sample for sample in trace if sample.label == VLLM_DOWN]
    if not downs or any(sample.resident_bytes > idle_bytes for sample in downs):
        return False
    return True


def _parse_smi_used_mib(text: str) -> int:
    """Pure Calculation: the first integer MiB from ``nvidia-smi --query-gpu=memory.used`` (0 if empty)."""
    lines = [line for line in text.strip().splitlines() if line.strip()]
    return int(lines[0].split()[0]) if lines else 0


def gpu_memory_used_bytes(device_index: int = 0) -> int:
    """Action: GPU-wide resident VRAM in bytes via nvidia-smi (0 if unavailable).

    vLLM v1 runs the model in a SEPARATE EngineCore process, so an in-process ``torch`` counter reads 0;
    nvidia-smi is the authoritative GPU-wide measure for the reasoner footprint + the handoff trace.
    """
    import subprocess  # noqa: PLC0415

    try:
        result = subprocess.run(
            ["nvidia-smi", f"--id={device_index}", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    return _parse_smi_used_mib(result.stdout) * 1024 * 1024


def sample(label: str, device_index: int = 0) -> VramSample:
    """Action: one labeled GPU-wide VRAM sample for a handoff trace."""
    return VramSample(label=label, resident_bytes=gpu_memory_used_bytes(device_index))
