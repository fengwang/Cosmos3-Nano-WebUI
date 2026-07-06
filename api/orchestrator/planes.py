"""Engine-plane identity + launch specs (ACD: Data + pure Calculations; torch-free import).

A `Plane` is one of the two heavy GPU residents the single slot swaps between. A `PlaneSpec` says
how to launch that plane's out-of-process worker (argv) and how to know it is ready (probe). The
reasoning spec reuses the frozen S5 `server_launch_argv` (vLLM, located via an operator-set binary);
the generation spec runs the in-package `gen_worker` entrypoint. These are pure functions of explicit
config — env reads live in the manager's factory — so the argv is host-testable. INV-8: only
operator/config dirs reach the loader argv, never a request field. Refs:
session_6/specs/single-gpu-orchestrator.md.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from enum import Enum

from engines.vllm.loader import ReasonerConfig, server_launch_argv


class Plane(Enum):
    """The heavy GPU residents the orchestrator swaps between (no string blindness)."""

    GENERATION = "generation"
    REASONING = "reasoning"


class ProbeKind(Enum):
    """How a worker signals readiness."""

    HTTP = "http"          # poll a URL for HTTP 200 (vLLM's OpenAI server /health)
    READY_FILE = "ready_file"  # wait for the worker to touch a file (the gen_worker handshake)


@dataclass(frozen=True)
class PlaneSpec:
    """How to launch + probe one plane's out-of-process worker (inert Data)."""

    plane: Plane
    argv: tuple[str, ...]
    probe_kind: ProbeKind
    probe_target: str
    # vLLM runs in its OWN venv → strip parent-venv leakage (PYTHONPATH/VIRTUAL_ENV/LD_LIBRARY_PATH)
    # so the worker's own torch/libs win (the S5 _clean_env lesson).
    strip_parent_env: bool = False
    # S2: per-checkpoint env overrides (e.g. COSMOS3_MODEL_DIR) merged into the subprocess environment.
    env_overrides: tuple[tuple[str, str], ...] | None = None


def reasoning_spec(
    cfg: ReasonerConfig, *, vllm_bin: str, port: int, host: str = "127.0.0.1", enforce_eager: bool = True
) -> PlaneSpec:
    """Pure: the reasoning worker spec — `vllm serve` (S5 argv) on a port, probed via /health.

    `server_launch_argv(cfg)[0]` is the literal "vllm"; we replace it with the operator-set binary
    (`COSMOS3_VLLM_BIN`) so the orchestrator runs vLLM from its dedicated venv (INV-7 / the S5 pattern).
    """
    extra = ["--port", str(port)]
    if enforce_eager:
        extra.append("--enforce-eager")
    argv = (vllm_bin, *server_launch_argv(cfg)[1:], *extra)
    return PlaneSpec(
        plane=Plane.REASONING, argv=argv, probe_kind=ProbeKind.HTTP,
        probe_target=f"http://{host}:{port}/health", strip_parent_env=True,
    )


def generation_spec(
    *, ready_file: str, python_bin: str | None = None, module: str = "orchestrator.gen_worker",
    model_dir: str | None = None,
) -> PlaneSpec:
    """Pure: the generation worker spec — run `gen_worker` (loads+warms the real oracle), probed via a ready-file."""
    argv = (python_bin or sys.executable, "-m", module, ready_file)
    env_overrides = (("COSMOS3_MODEL_DIR", model_dir),) if model_dir else None
    return PlaneSpec(
        plane=Plane.GENERATION, argv=argv, probe_kind=ProbeKind.READY_FILE, probe_target=ready_file,
        env_overrides=env_overrides,
    )


def container_generation_spec(*, base_url: str, health_path: str = "/v1/models") -> PlaneSpec:
    """Pure: the vllm-omni container generation plane spec (S4) — probed via the server HTTP endpoint.

    The container is launched/stopped by a `ContainerController` (not an argv subprocess), so `argv`
    is empty; readiness is an HTTP probe on the server's readiness endpoint (`/v1/models` returns 200
    with the loaded model list once the checkpoint is resident — the proven S1-S3 diag readiness
    signal). Pure function of operator config (INV-8): no request field reaches it. Refs:
    session_4/specs/container-plane-lifecycle.md; design.md D-1/D-8.
    """
    probe_target = f"{base_url.rstrip('/')}{health_path}"
    return PlaneSpec(
        plane=Plane.GENERATION, argv=(), probe_kind=ProbeKind.HTTP, probe_target=probe_target,
    )
