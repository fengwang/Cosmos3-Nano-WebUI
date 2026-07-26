"""AM-S5: the NVFP4 stack is a single all-modes, zero-BF16 wiring.

Pure-file YAML assertions (no docker, no GPU): mirrors test_fp8_allmodes_wiring for the NVFP4 stack.
The NVFP4 reasoner serves the quantized understanding tower via `--quantization nvfp4_blockwise_w4a16`
(no --omni), and — unlike FP8 — the NVFP4 omni forbids layerwise offload (Marlin FP4 kernel).
Spec: docs/session_5/specs/nvfp4-all-modes-wiring.md. GPU evidence: docs/session_5/evidence/P1–P2.
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
            **_load("docker-compose.nvfp4.yml").get("services", {})}


def _all_volume_strings() -> list[str]:
    vols: list[str] = []
    for name in ("docker-compose.base.yml", "docker-compose.nvfp4.yml"):
        for svc in _load(name).get("services", {}).values():
            for v in svc.get("volumes") or []:
                vols.append(v if isinstance(v, str) else str(v))
    return vols


def _cmd(svc: dict) -> str:
    return " ".join(str(t) for t in (svc.get("command") or []))


def test_nvfp4_declares_omni_and_reasoner_services():
    services = _all_services()
    assert "vllm-omni" in services, "generation (Studio/Action) plane missing from nvfp4"
    assert "vllm-reasoner" in services, "reasoning plane missing from the nvfp4 stack (AM-S5)"


def test_nvfp4_reasoner_uses_w4a16_and_no_omni():
    reasoner = _load("docker-compose.nvfp4.yml")["services"]["vllm-reasoner"]
    cmd = _cmd(reasoner)
    assert "nvfp4_blockwise_w4a16" in cmd, f"nvfp4 reasoner must serve --quantization nvfp4_blockwise_w4a16; got: {cmd}"
    assert "--omni" not in cmd.split(), "the reasoner serves TEXT — it must NOT use --omni"


def test_nvfp4_reasoner_builds_the_separate_nvfp4_image():
    # Blast radius (design D1): the FP8 reasoner image/Dockerfile is frozen; nvfp4 gets its own.
    reasoner = _load("docker-compose.nvfp4.yml")["services"]["vllm-reasoner"]
    dockerfile = str((reasoner.get("build") or {}).get("dockerfile", ""))
    assert dockerfile.endswith("vllm-reasoner-nvfp4.Dockerfile"), (
        f"nvfp4 reasoner must build deploy/vllm-reasoner-nvfp4.Dockerfile (not the FP8 one); got {dockerfile!r}")


def test_nvfp4_no_bf16_base_mount():
    joined = "\n".join(_all_volume_strings())
    assert "/models/base" not in joined, "BF16 base mount (/models/base) must not exist on nvfp4 (INV-4)"
    for v in _all_volume_strings():
        assert not re.search(r"Cosmos3-Nano(?![-\w])", v), f"BF16 base source still referenced on nvfp4: {v}"


def test_nvfp4_reasoner_and_omni_mount_the_nvfp4_checkpoint():
    nv = _load("docker-compose.nvfp4.yml")["services"]
    for svc in ("vllm-omni", "vllm-reasoner"):
        vols = "\n".join(nv[svc].get("volumes") or [])
        assert "/models/checkpoint" in vols, f"{svc} does not mount the checkpoint"
        assert "NVFP4" in vols, f"{svc} does not mount the quantized NVFP4 checkpoint"


def _up_nvfp4_recipe() -> str:
    """The `up-nvfp4:` recipe lines from the Makefile (until the next target/blank block)."""
    lines = (pathlib.Path(__file__).resolve().parents[2] / "Makefile").read_text().splitlines()
    out, capture = [], False
    for ln in lines:
        if ln.startswith("up-nvfp4:"):
            capture = True
            continue
        if capture:
            # recipe lines are RECIPEPREFIX-'>' prefixed or comments/blank; stop at the next target.
            if ln and not ln.startswith((">", "#", "\t", " ")):
                break
            out.append(ln)
    return "\n".join(out)


def test_up_nvfp4_cold_starts_and_stops_both_heavy_planes():
    # INV-5: boot must never co-load the two heavy planes. up-nvfp4 mirrors up-fp8 — create-but-not-start,
    # stop BOTH heavy planes (omni + the AM-S5 reasoner), then start only api+webui.
    recipe = _up_nvfp4_recipe()
    assert "--no-start" in recipe, "up-nvfp4 must create-but-not-start (cold-start)"
    stop_lines = [ln for ln in recipe.splitlines() if "stop" in ln]
    joined = "\n".join(stop_lines)
    assert "vllm-omni" in joined and "vllm-reasoner" in joined, (
        f"up-nvfp4 must stop BOTH heavy planes (vllm-omni + vllm-reasoner); stop lines: {stop_lines!r}")
    assert "start api webui" in recipe, "up-nvfp4 must start only api+webui (orchestrator owns the heavy planes)"


def test_nvfp4_omni_forbids_layerwise_offload_but_fp8_allows_it():
    # NVFP4's Marlin FP4 kernel repacks on CUDA after load and forbids offload; FP8 uses it.
    nvfp4_omni = _cmd(_load("docker-compose.nvfp4.yml")["services"]["vllm-omni"])
    fp8_omni = _cmd(_load("docker-compose.fp8.yml")["services"]["vllm-omni"])
    assert "--enable-layerwise-offload" not in nvfp4_omni, "NVFP4 omni must NOT use --enable-layerwise-offload (Marlin FP4)"
    assert "--enable-layerwise-offload" in fp8_omni, "FP8 omni should still use --enable-layerwise-offload (non-regress signal)"
