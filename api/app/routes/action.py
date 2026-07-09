"""Action capability endpoints (S7; FR4): forward_dynamics/inverse_dynamics/policy → the job path.

Thin typed facades mapping an ``ActionBody`` to a ``JobSubmit`` and reusing ``submit_and_enqueue``. The
S4 embodiment schema (``preprocessing.action_schema.validate``, reused by the shared validator) runs
BEFORE enqueue (EC-A4 → 422 ``width_mismatch``; ID needs video; FD/policy need an image). The v1 scope
(S4 human gate) is FD/policy on ``agibotworld`` (29-D) and ID on ``av`` (9-D); other registered
embodiments pass the schema but are best-effort. Refs: session_7/specs/action-endpoints.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, status

from app.jobs_router import submit_and_enqueue
from app.routes.checkpoint import resolve_checkpoint
from app.schemas import ActionBody, Job, JobSubmit
from jobs.runner import JobRunner
from jobs.store import JobStore

if TYPE_CHECKING:
    from app.observability.metrics import Metrics


def _params(body: ActionBody) -> dict:
    """Map the typed body → the JobSubmit params; derive ``raw_action_width`` from a 2-D ``raw_actions``."""
    params: dict = {
        "domain_name": body.domain_name, "chunk_size": body.chunk_size,
        "resolution_tier": body.resolution_tier, "view_point": body.view_point,
        "seed": body.seed, "checkpoint": resolve_checkpoint(body.checkpoint),
    }
    for key in ("prompt", "image_path", "video_path"):
        value = getattr(body, key)
        if value is not None:
            params[key] = value
    if body.raw_actions is not None:
        params["raw_actions"] = body.raw_actions
        first = body.raw_actions[0] if body.raw_actions else None
        params["raw_action_width"] = len(first) if isinstance(first, (list, tuple)) else None
    return params


def build_action_router(store: JobStore, runner: JobRunner, metrics: Metrics | None = None) -> APIRouter:
    """Build the ``/v1/action`` router bound to the injected store + runner."""
    router = APIRouter(prefix="/v1/action", tags=["action"])

    @router.post("/forward_dynamics", status_code=status.HTTP_202_ACCEPTED, response_model=Job)
    async def forward_dynamics(body: ActionBody) -> Job:
        return await submit_and_enqueue(
            JobSubmit(mode="forward_dynamics", params=_params(body), media=body.image), store, runner, metrics=metrics
        )

    @router.post("/inverse_dynamics", status_code=status.HTTP_202_ACCEPTED, response_model=Job)
    async def inverse_dynamics(body: ActionBody) -> Job:
        return await submit_and_enqueue(
            JobSubmit(mode="inverse_dynamics", params=_params(body), media=body.image), store, runner, metrics=metrics
        )

    @router.post("/policy", status_code=status.HTTP_202_ACCEPTED, response_model=Job)
    async def policy(body: ActionBody) -> Job:
        return await submit_and_enqueue(
            JobSubmit(mode="policy", params=_params(body), media=body.image), store, runner, metrics=metrics
        )

    return router
