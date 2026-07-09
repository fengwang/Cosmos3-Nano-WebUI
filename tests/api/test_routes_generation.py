"""Generation capability endpoints (host; stub orchestrator + stub work).

Spec: session_7/specs/generation-endpoints.md — typed routes → 202 jobs; t2i is single-frame;
t2v_audio requests audio; public limits + i2v conditioning enforced before enqueue (INV-6 / RK-08).
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_t2v_accepted_as_queued_job(make_app):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "a robotic arm wiping a plate", "num_frames": 8})
        assert resp.status_code == 202
        body = resp.json()
        assert body["mode"] == "t2v" and body["status"] == "queued" and body["id"]


def test_t2i_forces_single_frame(make_app):
    app = make_app()
    with TestClient(app) as client:
        job_id = client.post("/v1/generation/t2i", json={"prompt": "x", "num_frames": 16}).json()["id"]
    assert app.state.jobs.get(job_id).params["num_frames"] == 1  # t2i is the single-frame path


def test_t2v_audio_sets_sound_flag(make_app):
    app = make_app()
    with TestClient(app) as client:
        job_id = client.post("/v1/generation/t2v_audio", json={"prompt": "x"}).json()["id"]
    assert app.state.jobs.get(job_id).params.get("generate_sound") is True


def test_over_family_resolution_is_422_no_enqueue(make_app):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "x", "resolution": 123})
        assert resp.status_code == 422 and resp.json()["code"] == "invalid_dimension"
    assert app.state.jobs._jobs == {}  # rejected before enqueue (INV-6)


def test_landscape_720p_dimensions_accepted(make_app):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "x", "height": 720, "width": 1280})
        assert resp.status_code == 202


def test_landscape_480p_dimensions_accepted(make_app):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "x", "height": 480, "width": 640})
        assert resp.status_code == 202


def test_invalid_dimension_is_422(make_app):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "x", "height": 720, "width": 9999})
        assert resp.status_code == 422 and resp.json()["code"] == "invalid_dimension"
    assert app.state.jobs._jobs == {}


def test_i2v_without_image_is_422(make_app):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/i2v", json={"prompt": "x"})
        assert resp.status_code == 422 and resp.json()["code"] == "invalid_param"
    assert app.state.jobs._jobs == {}


def test_i2v_with_trusted_image_path_accepted(make_app, tmp_path):
    cond = tmp_path / "cond.png"
    cond.write_bytes(b"\x89PNG\r\n\x1a\n")
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/i2v", json={"prompt": "x", "image_path": str(cond)})
        assert resp.status_code == 202 and resp.json()["mode"] == "i2v"
