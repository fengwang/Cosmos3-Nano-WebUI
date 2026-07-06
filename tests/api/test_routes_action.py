"""Action capability endpoints (host; stub orchestrator + stub work).

Spec: session_7/specs/action-endpoints.md — typed routes → 202 jobs; the S4 embodiment schema is
enforced BEFORE enqueue (EC-A4 width_mismatch; ID needs video; unknown embodiment rejected).
v1 scope: FD/policy on agibotworld (29-D), ID on av (9-D).
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def _cond(tmp_path, name: str):
    path = tmp_path / name
    path.write_bytes(b"\x89PNG\r\n\x1a\n")
    return str(path)


def test_forward_dynamics_agibotworld_accepted(make_app, tmp_path):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post(
            "/v1/action/forward_dynamics",
            json={"domain_name": "agibotworld", "chunk_size": 17,
                  "raw_actions": [[0.0] * 29], "image_path": _cond(tmp_path, "c.png")},
        )
        assert resp.status_code == 202 and resp.json()["mode"] == "forward_dynamics"


def test_ec_a4_width_mismatch_is_422_no_enqueue(make_app, tmp_path):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post(
            "/v1/action/forward_dynamics",
            json={"domain_name": "av", "chunk_size": 32,
                  "raw_actions": [[0.0] * 10], "image_path": _cond(tmp_path, "c.png")},  # 10 ≠ av's 9
        )
        assert resp.status_code == 422 and resp.json()["code"] == "width_mismatch"
    assert app.state.jobs._jobs == {}  # never enqueued / never reached the engine (RK-12)


def test_inverse_dynamics_without_video_is_422(make_app):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/action/inverse_dynamics", json={"domain_name": "av", "chunk_size": 17})
        assert resp.status_code == 422 and resp.json()["code"] == "condition_missing"


def test_inverse_dynamics_av_accepted(make_app, tmp_path):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post(
            "/v1/action/inverse_dynamics",
            json={"domain_name": "av", "chunk_size": 17, "video_path": _cond(tmp_path, "v.mp4")},
        )
        assert resp.status_code == 202 and resp.json()["mode"] == "inverse_dynamics"


def test_unknown_embodiment_is_422(make_app, tmp_path):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post(
            "/v1/action/policy",
            json={"domain_name": "not_a_robot", "chunk_size": 17, "image_path": _cond(tmp_path, "c.png")},
        )
        assert resp.status_code == 422 and resp.json()["code"] == "unknown_embodiment"
