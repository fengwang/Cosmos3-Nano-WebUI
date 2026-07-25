"""AM-S4: the FP8 stack is a single all-modes, zero-BF16 wiring.

Pure-file YAML assertions (no docker, no GPU): the deploy posture is checked
structurally against ``deploy/docker-compose.{base,fp8,nvfp4}.yml``. Realizes
EV-AM-NO-OVERLAY-DEFAULT + EV-AM-ZERO-BF16-WIRING.
Spec: docs/session_4/specs/unified-fp8-allmodes-stack.md.
"""
from __future__ import annotations

import pathlib
import re

import yaml

DEPLOY = pathlib.Path(__file__).resolve().parents[2] / "deploy"


def _load(name: str) -> dict:
    return yaml.safe_load((DEPLOY / name).read_text())


def _all_services() -> dict:
    return {**_load("docker-compose.base.yml").get("services", {}),
            **_load("docker-compose.fp8.yml").get("services", {})}


def _all_volume_strings() -> list[str]:
    """Every volume mapping declared across base + fp8 (no service shadowing)."""
    vols: list[str] = []
    for name in ("docker-compose.base.yml", "docker-compose.fp8.yml"):
        for svc in _load(name).get("services", {}).values():
            for v in svc.get("volumes") or []:
                vols.append(v if isinstance(v, str) else str(v))
    return vols


def test_fp8_declares_omni_and_reasoner_services():
    services = _all_services()
    assert "vllm-omni" in services, "generation (Studio/Action) plane missing"
    assert "vllm-reasoner" in services, "reasoning plane missing from the default stack"


def test_no_bf16_base_mount_in_default_path():
    # /models/base was the only BF16 base mount target; it must be gone (INV-4).
    joined = "\n".join(_all_volume_strings())
    assert "/models/base" not in joined
    # No reference to the bare BF16 base dir (…/Cosmos3-Nano) in ANY form — a literal path or a
    # ${VAR:-default} whose default text sits in the raw string. The negative lookahead
    # `(?![-\w])` excludes the quantized …-FP8-Blockwise / …-NVFP4-Blockwise dirs, so only the
    # bare base (followed by `}`, `/`, `:`, or end) trips it.
    for v in _all_volume_strings():
        assert not re.search(r"Cosmos3-Nano(?![-\w])", v), f"BF16 base source still referenced: {v}"


def test_reasoner_and_omni_mount_the_fp8_quantized_checkpoint():
    fp8 = _load("docker-compose.fp8.yml")["services"]
    for svc in ("vllm-omni", "vllm-reasoner"):
        vols = "\n".join(fp8[svc].get("volumes") or [])
        assert "/models/checkpoint" in vols, f"{svc} does not mount the checkpoint"
        assert "FP8" in vols, f"{svc} does not mount the quantized FP8 checkpoint"


def test_no_stack_file_includes_the_reasoning_overlay():
    # Guard every stack file's include list (not just fp8's) against pulling a reasoning overlay.
    for name in ("docker-compose.base.yml", "docker-compose.fp8.yml", "docker-compose.nvfp4.yml"):
        includes = _load(name).get("include") or []
        assert not any("reasoning" in str(i) for i in includes), f"{name} includes a reasoning overlay"


def test_nvfp4_stack_renders_structurally():
    # Spec: the nvfp4 stack stays renderable (AM-S5 GPU-verifies it). Structural check here; the
    # full `docker compose … config` exit-0 render is a deterministic gate (execution_contract §checks).
    nv = _load("docker-compose.nvfp4.yml")
    includes = " ".join(str(i) for i in (nv.get("include") or []))
    assert "docker-compose.base.yml" in includes, "nvfp4 must include the shared base"
    vols = "\n".join(nv["services"]["vllm-omni"].get("volumes") or [])
    assert "/models/checkpoint" in vols and "NVFP4" in vols, "nvfp4 omni must mount the NVFP4 checkpoint"
