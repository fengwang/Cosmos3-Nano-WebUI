"""The single deployed generation endpoint + deployment identity (ACD: Data + pure Calculations; INV-3).

S6 standalone deployments serve exactly ONE generation checkpoint (FP8 XOR NVFP4), so there is no
per-request routing between two planes: ``endpoint_for()`` returns the one container/URL from operator
env, and ``deployed_checkpoint()`` is the deployment's implicit label (``COSMOS3_CHECKPOINT_LABEL``).
These are the single source of truth shared by the orchestrator worker factory
(``app.main.default_worker_factory`` — which container to start/stop) and the generation adapter
(``engines.vllm_omni.work`` — which base URL to POST to); if the two disagreed a job could be submitted
to a container the orchestrator never made resident. Reads ONLY operator env (never a request field).
Refs: session_6/specs/single-checkpoint-serving.md.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_URL = "http://vllm-omni:8000"
_DEFAULT_CONTAINER = "cosmos3-nano-webui-vllm-omni"

KNOWN_CHECKPOINTS = ("fp8", "nvfp4")
DEFAULT_CHECKPOINT = "fp8"


def deployed_checkpoint() -> str:
    """Pure: the single checkpoint label this deployment serves (operator env; INV-3). Defaults to
    ``fp8`` when unset or set to an unknown value (the compose files set it explicitly per stack)."""
    label = os.environ.get("COSMOS3_CHECKPOINT_LABEL", DEFAULT_CHECKPOINT)
    return label if label in KNOWN_CHECKPOINTS else DEFAULT_CHECKPOINT


@dataclass(frozen=True)
class OmniEndpoint:
    """The vllm-omni endpoint serving the deployed checkpoint (inert Data)."""

    checkpoint: str
    container: str
    base_url: str


def endpoint_for() -> OmniEndpoint:
    """Pure: the single deployed generation endpoint from operator env (INV-3/INV-8).

    A standalone deployment has exactly one generation plane, so there is no label to route on; the
    reported ``checkpoint`` is the deployed label.
    """
    return OmniEndpoint(
        deployed_checkpoint(),
        os.environ.get("COSMOS3_GEN_CONTAINER", _DEFAULT_CONTAINER),
        os.environ.get("COSMOS3_VLLM_OMNI_URL", _DEFAULT_URL),
    )
