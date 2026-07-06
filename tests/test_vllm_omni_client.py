"""Unit tests for the vllm-omni async video client (spec: vllm-omni-video-client).

Host-testable via an injected fake transport + injected clock — no server, no torch.
"""
from __future__ import annotations

import inspect
import re

import pytest

from app.schemas import JobStatus
from engines.vllm_omni import client as vc
from jobs.model import JobRecord
from orchestrator.planes import Plane


def _rec(**params) -> JobRecord:
    return JobRecord(
        id="job-1", mode=params.pop("mode", "t2v"), plane=Plane.GENERATION,
        status=JobStatus.running, created_at="2026-07-02T00:00:00Z", params=params,
    )


class _FakeTransport:
    """Scripted transport: `polls` is a list of dicts (code 200) or (code, dict) tuples."""

    def __init__(self, *, submit=None, polls=None, content=b"MP4DATA"):
        self.submit_resp = submit if submit is not None else {"id": "vid-123", "status": "queued"}
        self.polls = list(polls or [])
        self.content = content
        self.calls: list[tuple[str, str]] = []
        self.last_form: dict | None = None

    def post_form(self, path, form):
        self.calls.append(("post", path))
        self.last_form = form
        return self.submit_resp

    def get_json(self, path):
        self.calls.append(("get", path))
        item = self.polls.pop(0)
        return item if isinstance(item, tuple) else (200, item)

    def get_bytes(self, path):
        self.calls.append(("content", path))
        return self.content

    def delete(self, path):
        self.calls.append(("delete", path))


# ── build_video_form (pure) ──────────────────────────────────────────────────

def test_build_video_form_pins_flagship_params():
    form = vc.build_video_form(_rec(
        prompt="a sponge on a plate", negative_prompt="blurry",
        width=1280, height=720, num_frames=189, num_inference_steps=35,
        guidance_scale=6.0, flow_shift=10.0, seed=123,
    ))
    assert form["size"] == "1280x720"
    assert form["num_frames"] == "189"
    assert form["seed"] == "123"
    assert form["guidance_scale"] == "6.0"
    assert form["flow_shift"] == "10.0"
    assert form["num_inference_steps"] == "35"
    assert form["fps"] == "24"
    assert form["negative_prompt"] == "blurry"
    import json
    extra = json.loads(form["extra_params"])
    assert extra["guardrails"] is False


def test_build_video_form_is_deterministic_and_defaults_pinned():
    rec = _rec(prompt="x", width=640, height=480, num_frames=57)
    assert vc.build_video_form(rec) == vc.build_video_form(rec)
    form = vc.build_video_form(rec)
    assert form["seed"] == "123" and form["guidance_scale"] == "6.0" and form["fps"] == "24"


def test_build_video_form_sets_sound_flag():
    form = vc.build_video_form(_rec(prompt="x", generate_sound=True, mode="t2v_audio"))
    assert form.get("generate_sound") == "true"


# ── parse_status (pure) ──────────────────────────────────────────────────────

@pytest.mark.parametrize("status,expected", [
    ("completed", "completed"), ("failed", "failed"),
    ("queued", "pending"), ("in_progress", "pending"),
])
def test_parse_status_maps_states(status, expected):
    state, _ = vc.parse_status({"status": status})
    assert state == expected


def test_parse_status_progress_is_fraction():
    _, frac = vc.parse_status({"status": "in_progress", "progress": 40})
    assert frac == pytest.approx(0.40)
    _, frac_none = vc.parse_status({"status": "in_progress"})
    assert frac_none is None


@pytest.mark.parametrize("prog,expected", [(150, 1.0), (-10, 0.0), ("soon", None), (None, None)])
def test_parse_status_progress_clamped_or_none(prog, expected):
    # out-of-range clamps to [0,1]; non-numeric / null → None (a malformed status never crashes the job)
    _, frac = vc.parse_status({"status": "in_progress", "progress": prog})
    assert frac == expected


# ── run_video_job (Action; injected transport + clock) ───────────────────────

def test_run_video_job_success_returns_bytes_and_reports_progress():
    seen: list[float] = []
    t = _FakeTransport(polls=[
        {"status": "queued", "progress": 0},
        {"status": "in_progress", "progress": 50},
        {"status": "completed", "progress": 100},
    ])
    out = vc.run_video_job(_rec(prompt="x", width=640, height=480, num_frames=57),
                           seen.append, transport=t, poll_interval=0.0,
                           now=lambda: 0.0, sleep=lambda _s: None)
    assert out == b"MP4DATA"
    assert t.calls[0][0] == "post" and t.calls[-1] == ("content", "/v1/videos/vid-123/content")
    assert seen[0] == 0.0                      # 0.0 at submit
    assert all(0.0 <= f < 1.0 for f in seen)   # client never emits terminal 1.0


def test_run_video_job_failed_status_raises_typed():
    t = _FakeTransport(polls=[{"status": "failed", "error": "boom"}])
    with pytest.raises(vc.VideoJobError) as ei:
        vc.run_video_job(_rec(prompt="x"), lambda _f: None, transport=t,
                         poll_interval=0.0, now=lambda: 0.0, sleep=lambda _s: None)
    assert ei.value.code == "generation_failed"
    assert ("content", "/v1/videos/vid-123/content") not in t.calls  # no download on failure


def test_run_video_job_non200_poll_raises_typed():
    t = _FakeTransport(polls=[(500, {"detail": "server error"})])
    with pytest.raises(vc.VideoJobError):
        vc.run_video_job(_rec(prompt="x"), lambda _f: None, transport=t,
                         poll_interval=0.0, now=lambda: 0.0, sleep=lambda _s: None)


def test_run_video_job_timeout_cancels_server_job():
    clock = iter([0.0, 100.0, 200.0])  # start=0, first check=100 > overall_timeout=10
    t = _FakeTransport(polls=[{"status": "in_progress", "progress": 10}])
    with pytest.raises(vc.VideoJobError) as ei:
        vc.run_video_job(_rec(prompt="x"), lambda _f: None, transport=t,
                         poll_interval=0.0, overall_timeout=10.0,
                         now=lambda: next(clock), sleep=lambda _s: None)
    assert ei.value.code == "timeout"
    assert ("delete", "/v1/videos/vid-123") in t.calls  # orphan prevention (R-14)


def test_run_video_job_missing_id_raises():
    t = _FakeTransport(submit={"status": "queued"})  # no id
    with pytest.raises(vc.VideoJobError):
        vc.run_video_job(_rec(prompt="x"), lambda _f: None, transport=t,
                         now=lambda: 0.0, sleep=lambda _s: None)


# ── progress helper (pure) + fail-open relay ─────────────────────────────────

def test_progress_fraction_prefers_server_and_is_bounded():
    assert vc._progress_fraction(0.5, 10.0, 100.0) == pytest.approx(0.5)
    assert vc._progress_fraction(None, 50.0, 100.0) == pytest.approx(0.5)
    assert vc._progress_fraction(0.99, 10.0, 100.0) <= 0.95      # never premature-100
    assert vc._progress_fraction(None, 1000.0, 100.0) <= 0.95


def test_progress_relay_is_fail_open():
    def boom(_f):
        raise RuntimeError("sink down")
    t = _FakeTransport(polls=[{"status": "in_progress", "progress": 10}, {"status": "completed"}])
    # a throwing report must not fail the job (FR-5 non-gating)
    out = vc.run_video_job(_rec(prompt="x"), boom, transport=t, poll_interval=0.0,
                           now=lambda: 0.0, sleep=lambda _s: None)
    assert out == b"MP4DATA"


def test_progress_is_monotonic_when_server_field_is_intermittent():
    # server reports `progress` on some polls, omits it on others → the reported bar must NOT regress
    seen: list[float] = []
    t = _FakeTransport(polls=[
        {"status": "in_progress", "progress": 60},  # server says 60%
        {"status": "in_progress"},                    # server omits it → elapsed ramp alone would be lower
        {"status": "completed"},
    ])
    vc.run_video_job(_rec(prompt="x", width=640, height=480, num_frames=57),
                     seen.append, transport=t, poll_interval=0.0, now=lambda: 0.0, sleep=lambda _s: None)
    assert seen == sorted(seen)          # non-decreasing (monotonic floor)
    assert max(seen) >= 0.60             # the server's 60% was honored and never dropped


# ── multipart encoder (pure) ─────────────────────────────────────────────────

def test_encode_multipart_roundtrips_fields():
    ct, body = vc.encode_multipart({"prompt": "hello", "seed": "123"}, boundary="B")
    assert ct == "multipart/form-data; boundary=B"
    text = body.decode("utf-8")
    assert 'name="prompt"' in text and "hello" in text
    assert 'name="seed"' in text and "123" in text
    assert text.strip().endswith("--B--")


# ── torch-free import guarantee ──────────────────────────────────────────────

def test_client_has_no_toplevel_torch_import():
    # host-loop guarantee: the client must import torch-free. Assert by source (robust in any venv —
    # a bare `import` cannot prove absence when torch is already resident from the oracle extra).
    src = inspect.getsource(vc)
    assert not re.search(r"^\s*(import torch|from torch)", src, re.M)
