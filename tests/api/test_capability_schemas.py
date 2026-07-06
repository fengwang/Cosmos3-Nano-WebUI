"""Typed capability request bodies + the Job precision/trajectory view (host).

Spec: session_7/specs/{generation,action,reasoning,engine-checkpoint-selection}.md — the per-mode
request models give typed OpenAPI bodies; the Job view surfaces the served precision + a trajectory URL.
"""
from __future__ import annotations

from app.schemas import ActionBody, GenerationBody, Job, JobStatus, ReasoningBody


def test_generation_body_defaults():
    body = GenerationBody(prompt="a robotic arm wiping a plate")
    assert body.checkpoint is None  # S6/FR-12: optional; the single-checkpoint deployment resolves it
    assert body.seed == 123 and body.num_frames is None and body.image is None


def test_action_body_defaults():
    body = ActionBody(domain_name="agibotworld", chunk_size=17)
    assert body.checkpoint is None and body.resolution_tier == 480 and body.view_point == "ego_view"
    assert body.raw_actions is None


def test_reasoning_body_defaults():
    body = ReasoningBody(prompt="why did the arm slip?")
    # S7 (FR-10): the 256 default is removed — an omitted budget (None) means "bounded only by the
    # backend context window"; the route resolves it to (max_context_tokens − prompt).
    assert body.max_output_tokens is None and body.image_path is None and body.video_path is None


def test_job_view_has_precision_and_trajectory_fields():
    job = Job(id="j1", status=JobStatus.succeeded, mode="forward_dynamics", created_at="t0")
    assert job.precision is None and job.trajectory_url is None  # additive, default None
