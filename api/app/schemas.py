"""Shared schema contract — the Data layer (inert, serializable values).

These Pydantic models are the code-first source of truth for the OpenAPI 3.1
contract (`schemas/openapi.json`). They define the async job-model types and the
error model that downstream sessions (S6 job lifecycle, S7 endpoints, S8 WebUI)
build on. No behavior, no I/O — only shape. Refs: evidence_map E2/E3.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Lifecycle states for an async media/action job (INV-5)."""

    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class ErrorModel(BaseModel):
    """Structured error body for the standard HTTP error contract (E4)."""

    code: str = Field(..., description="Machine-readable error code, e.g. 'invalid_input'.")
    message: str = Field(..., description="Human-readable error message.")
    details: dict | None = Field(default=None, description="Optional structured context.")


class Job(BaseModel):
    """An async job record (202 + job id + SSE + artifact fetch; INV-5).

    Schema stub only in S1 — no job *endpoints* exist yet (those are S6).
    """

    id: str = Field(..., description="Opaque job identifier.")
    status: JobStatus
    mode: str = Field(..., description="Public mode, e.g. 't2i' / 't2v' / 'i2v' / 'reason' / 'action'.")
    created_at: str = Field(..., description="ISO-8601 creation timestamp.")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Fractional progress in [0, 1].")
    artifact_url: str | None = Field(default=None, description="Artifact location once succeeded.")
    error: ErrorModel | None = Field(default=None, description="Populated when status is 'failed'.")
    precision: str | None = Field(
        default=None, description="The served checkpoint precision ('nvfp4'/'fp8'), reported on success (S7)."
    )
    trajectory_url: str | None = Field(
        default=None, description="Action trajectory location (FD/policy rollout + ID), when present (S7)."
    )


class HealthStatus(BaseModel):
    """Health payload for the liveness/readiness endpoints (G3/RK-07)."""

    status: str = Field(..., description="'live' | 'warming' | 'ready'.")
    detail: str | None = Field(default=None, description="Optional human-readable context.")


class InlineMedia(BaseModel):
    """Optional inline conditioning media for a job (base64 — the dep-free upload path; S6).

    The production multipart upload via the webui BFF is S7/S8; S6 validates either this inline blob
    or a trusted-volume path carried in ``params``.
    """

    kind: str = Field(..., description="'image' | 'video' | 'audio'.")
    data_base64: str = Field(..., description="Base64-encoded conditioning media bytes.")


class JobSubmit(BaseModel):
    """A media/action job submission (INV-5)."""

    mode: str = Field(
        ..., description="Job mode: t2i/t2v/i2v/t2v_audio or forward_dynamics/inverse_dynamics/policy."
    )
    params: dict = Field(
        default_factory=dict,
        description="Mode-specific params (prompt, resolution, num_frames, embodiment, conditioning paths).",
    )
    media: InlineMedia | None = Field(
        default=None, description="Optional inline conditioning media (base64)."
    )


# --- Typed per-capability request bodies (S7). The routes map these to a JobSubmit (generation/action) ---
# --- or drive the streaming reasoner (reasoning), reusing the shared validation + job machinery. ---


class GenerationBody(BaseModel):
    """A typed generation request (t2i/t2v/i2v/t2v_audio). The route fixes the mode + mode-specifics."""

    prompt: str = Field(..., description="The generation prompt.")
    negative_prompt: str | None = Field(default=None, description="Optional negative prompt.")
    resolution: int | None = Field(default=None, description="Square resolution ∈ {256,480,720} (default 480).")
    height: int | None = Field(default=None, description="Frame height (∈ the resolution families).")
    width: int | None = Field(default=None, description="Frame width (∈ the resolution families).")
    num_frames: int | None = Field(default=None, description="Frame count (t2i is forced to 1); ≤ the public cap.")
    num_inference_steps: int | None = Field(default=None, description="Denoising steps.")
    seed: int = Field(default=123, description="Deterministic seed (INV-10).")
    checkpoint: str | None = Field(
        default=None,
        description="Optional served-checkpoint label; single-checkpoint deployments serve the "
        "deployed checkpoint implicitly. If given, must equal the deployed label (else 422).",
    )
    image_path: str | None = Field(default=None, description="Trusted-volume conditioning image path (i2v).")
    image: InlineMedia | None = Field(default=None, description="Inline conditioning image (base64; i2v).")


class ActionBody(BaseModel):
    """A typed action request (forward_dynamics/inverse_dynamics/policy). The route fixes the mode."""

    domain_name: str = Field(..., description="Embodiment domain (e.g. 'agibotworld' 29-D, 'av' 9-D).")
    chunk_size: int = Field(..., description="Action transition count (the 16–400 rollout window).")
    raw_actions: list | None = Field(default=None, description="Forward-dynamics driving tensor [T, raw_dim].")
    resolution_tier: int = Field(default=480, description="Conditioning resolution tier ∈ {256,480,704,720}.")
    view_point: str = Field(default="ego_view", description="Camera view point.")
    prompt: str | None = Field(default=None, description="Optional instruction (policy).")
    seed: int = Field(default=123, description="Deterministic seed (INV-10).")
    checkpoint: str | None = Field(
        default=None,
        description="Optional served-checkpoint label; single-checkpoint deployments serve the "
        "deployed checkpoint implicitly. If given, must equal the deployed label (else 422).",
    )
    image_path: str | None = Field(default=None, description="Trusted-volume conditioning image path (FD/policy).")
    video_path: str | None = Field(default=None, description="Trusted-volume conditioning video path (ID).")
    image: InlineMedia | None = Field(default=None, description="Inline conditioning image/video (base64).")


class ReasoningBody(BaseModel):
    """A typed reasoning request (text+image/video → text, streamed as SSE)."""

    prompt: str = Field(..., description="The reasoning prompt.")
    image_path: str | None = Field(default=None, description="Trusted-volume conditioning image path (EC-R2).")
    video_path: str | None = Field(default=None, description="Trusted-volume conditioning video path (EC-R3).")
    max_output_tokens: int | None = Field(
        default=None,
        description="Output token budget. Omit/null = bounded only by the backend context window "
        "(≤ max_context_tokens − prompt). If supplied, it must fit the context window.",
    )
