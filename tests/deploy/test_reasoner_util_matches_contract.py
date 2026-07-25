"""AM-S4 R-08: the coresidency VRAM contract tracks the live reasoner command.

Closes the config-vs-runtime drift adversarial case (#5): the documented
gpu-memory-utilization must equal the actual ``vllm-reasoner`` serve command in the
compose file — not a dead subprocess argv. If AM-S5 retunes either, this fails until
both agree. Spec: docs/session_4/specs/cold-start-residency-lifecycle.md.
"""
from __future__ import annotations

import pathlib

import yaml

from engines.vllm.coresidency import CoResidencyContract

ROOT = pathlib.Path(__file__).resolve().parents[2]

_FLAG = "--gpu-memory-utilization"


def _reasoner_gpu_util() -> float:
    """The reasoner's gpu-memory-utilization, robust to `--flag value` and `--flag=value` forms."""
    fp8 = yaml.safe_load((ROOT / "deploy/docker-compose.fp8.yml").read_text())
    cmd = fp8["services"]["vllm-reasoner"]["command"]
    for i, tok in enumerate(cmd):
        tok = str(tok)
        if tok == _FLAG:
            return float(cmd[i + 1])
        if tok.startswith(_FLAG + "="):
            return float(tok.split("=", 1)[1])
    raise AssertionError(f"vllm-reasoner command carries no {_FLAG} flag: {cmd}")


def test_reasoner_gpu_util_equals_contract():
    assert _reasoner_gpu_util() == CoResidencyContract().gpu_memory_utilization
