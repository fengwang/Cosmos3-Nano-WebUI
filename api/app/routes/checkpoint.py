"""Checkpoint label validation at the edge (ACD: a pure Calculation + one retained typed error; INV-2).

S6 standalone deployments serve exactly one generation checkpoint (FP8 XOR NVFP4), so the request
``checkpoint`` field is optional and no longer *selects* a plane — it is only validated against the
single deployed label (``COSMOS3_CHECKPOINT_LABEL``, via ``deployed_checkpoint``):

- absent (``None``/empty) → the deployed label (the WebUI no longer sends the field, FR-12);
- present and equal to the deployed label → accepted;
- present but a different label, or any value that is not a bare ``fp8``/``nvfp4`` label (a path, URL,
  or traversal string) → 422 ``invalid_param`` before any model load (INV-2).

``CheckpointUnavailable`` is retained (defined but no longer raised) because the error-handler
registration in ``app.errors`` — outside this session's blast radius — imports it. Refs:
session_6/specs/single-checkpoint-serving.md.
"""
from __future__ import annotations

from engines.vllm_omni.endpoints import KNOWN_CHECKPOINTS, deployed_checkpoint
from preprocessing.media import MediaErrorCode, MediaValidationError, MediaValidationFailed


class CheckpointUnavailable(Exception):
    """Retained for the app.errors handler import (no longer raised — a single checkpoint is deployed)."""

    code = "checkpoint_unavailable"


def _reject(message: str) -> "MediaValidationFailed":
    return MediaValidationFailed(MediaValidationError(MediaErrorCode.INVALID_PARAM, message))


def resolve_checkpoint(checkpoint: str | None) -> str:
    """Pure: validate an optional request label against the single deployed checkpoint; return the
    deployed label, or raise a typed 422 ``invalid_param``.

    Never silently substitutes a different checkpoint, and never accepts a path/URL as a checkpoint
    (INV-2). An undeployed but known label is rejected here, not at container acquire.
    """
    deployed = deployed_checkpoint()
    if checkpoint is None or checkpoint == "":
        return deployed
    if checkpoint not in KNOWN_CHECKPOINTS:
        raise _reject(f"unknown checkpoint {checkpoint!r}; expected one of {list(KNOWN_CHECKPOINTS)}")
    if checkpoint != deployed:
        raise _reject(
            f"checkpoint {checkpoint!r} is not served by this deployment (serves {deployed!r})"
        )
    return deployed
