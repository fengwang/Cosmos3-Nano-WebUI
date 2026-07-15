"""Generation capability endpoints (S7; FR2): t2i/t2v/i2v/t2v_audio → the validated job path.

Thin typed facades: each route maps a ``GenerationBody`` to a ``JobSubmit`` and reuses
``submit_and_enqueue`` (the same INV-6 edge validation + single runner as ``/v1/jobs``). The route fixes
the mode-specifics (t2i → single frame; t2v_audio → request audio); the conservative public limits and
conditioning-path containment are enforced by the shared validator before enqueue. Checkpoint selection
is resolved at the edge (D-6). Refs: session_7/specs/generation-endpoints.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, status

from app.jobs_router import submit_and_enqueue
from app.routes.checkpoint import resolve_checkpoint
from app.schemas import GenerationBody, Job, JobSubmit
from jobs.runner import JobRunner
from jobs.store import JobStore
from preprocessing.media import MediaErrorCode, MediaValidationError, MediaValidationFailed
from preprocessing.negative_prompt import load_default_negative_prompt

if TYPE_CHECKING:
    from app.observability.metrics import Metrics


def _params(
    body: GenerationBody,
    *,
    num_frames: int | None,
    generate_sound: bool = False,
    negative_prompt_default: str | None = None,
) -> dict:
    """Map the typed body → the JobSubmit params (checkpoint resolved at the edge; absent fields dropped).

    ``negative_prompt_default`` is the curated overridable default (UX-S2, INV-5): a user value wins,
    otherwise the default is applied when present, otherwise the field is omitted (graceful fallback).
    """
    params: dict = {"prompt": body.prompt, "seed": body.seed, "checkpoint": resolve_checkpoint(body.checkpoint)}
    for key in ("negative_prompt", "resolution", "height", "width", "num_inference_steps", "image_path"):
        value = getattr(body, key)
        if value is not None:
            params[key] = value
    if params.get("negative_prompt") is None and negative_prompt_default is not None:
        params["negative_prompt"] = negative_prompt_default
    if num_frames is not None:  # the route's mode-specific override (t2i → 1)
        params["num_frames"] = num_frames
    elif body.num_frames is not None:
        params["num_frames"] = body.num_frames
    if generate_sound:
        params["generate_sound"] = True
    return params


def build_generation_router(store: JobStore, runner: JobRunner, metrics: Metrics | None = None) -> APIRouter:
    """Build the ``/v1/generation`` router bound to the injected store + runner."""
    router = APIRouter(prefix="/v1/generation", tags=["generation"])

    @router.post("/t2i", status_code=status.HTTP_202_ACCEPTED, response_model=Job)
    async def t2i(body: GenerationBody) -> Job:
        return await submit_and_enqueue(
            JobSubmit(mode="t2i", params=_params(body, num_frames=1, negative_prompt_default=load_default_negative_prompt()), media=body.image),
            store, runner, metrics=metrics,
        )

    @router.post("/t2v", status_code=status.HTTP_202_ACCEPTED, response_model=Job)
    async def t2v(body: GenerationBody) -> Job:
        return await submit_and_enqueue(
            JobSubmit(mode="t2v", params=_params(body, num_frames=None, negative_prompt_default=load_default_negative_prompt()), media=body.image),
            store, runner, metrics=metrics,
        )

    @router.post("/i2v", status_code=status.HTTP_202_ACCEPTED, response_model=Job)
    async def i2v(body: GenerationBody) -> Job:
        if body.image is None and not body.image_path:
            raise MediaValidationFailed(
                MediaValidationError(
                    MediaErrorCode.INVALID_PARAM, "i2v requires a conditioning image ('image' or 'image_path')"
                )
            )
        return await submit_and_enqueue(
            JobSubmit(mode="i2v", params=_params(body, num_frames=None, negative_prompt_default=load_default_negative_prompt()), media=body.image),
            store, runner, metrics=metrics,
        )

    @router.post("/t2v_audio", status_code=status.HTTP_202_ACCEPTED, response_model=Job)
    async def t2v_audio(body: GenerationBody) -> Job:
        return await submit_and_enqueue(
            JobSubmit(
                mode="t2v_audio",
                params=_params(body, num_frames=None, generate_sound=True, negative_prompt_default=load_default_negative_prompt()),
                media=body.image,
            ),
            store, runner, metrics=metrics,
        )

    return router
