"""Single-checkpoint label validation at the edge (host; stub orchestrator).

Spec: session_6/specs/single-checkpoint-serving.md — a standalone deployment serves ONE checkpoint;
the request ``checkpoint`` field is optional and validated against the deployed label
(``COSMOS3_CHECKPOINT_LABEL``): absent → deployed; equal → accepted; a different (but known) label, an
unknown value, or a path/URL → 422 ``invalid_param`` before any load (INV-2, FR-12).
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_absent_checkpoint_uses_deployed_fp8(make_app):
    app = make_app()  # default deployment = fp8
    with TestClient(app) as client:
        job_id = client.post("/v1/generation/t2v", json={"prompt": "x"}).json()["id"]
    assert app.state.jobs.get(job_id).params["checkpoint"] == "fp8"


def test_matching_label_accepted_on_fp8_deployment(make_app):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "x", "checkpoint": "fp8"})
        assert resp.status_code == 202
        job_id = resp.json()["id"]
    assert app.state.jobs.get(job_id).params["checkpoint"] == "fp8"


def test_mismatched_label_rejected_on_fp8_deployment(make_app):
    # nvfp4 is a known label but not this deployment's — rejected before any load (INV-2), no job created.
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "x", "checkpoint": "nvfp4"})
        assert resp.status_code == 422 and resp.json()["code"] == "invalid_param"
    assert app.state.jobs._jobs == {}


def test_nvfp4_deployment_accepts_nvfp4(make_app):
    app = make_app(COSMOS3_CHECKPOINT_LABEL="nvfp4")
    with TestClient(app) as client:
        # absent → deployed nvfp4
        j1 = client.post("/v1/generation/t2v", json={"prompt": "x"}).json()["id"]
        # matching → accepted
        r2 = client.post("/v1/generation/t2v", json={"prompt": "y", "checkpoint": "nvfp4"})
        # the other known label → 422
        r3 = client.post("/v1/generation/t2v", json={"prompt": "z", "checkpoint": "fp8"})
    assert app.state.jobs.get(j1).params["checkpoint"] == "nvfp4"
    assert r2.status_code == 202
    assert r3.status_code == 422 and r3.json()["code"] == "invalid_param"


def test_action_absent_checkpoint_uses_deployed_fp8(make_app, tmp_path):
    cond = tmp_path / "frame.png"
    cond.write_bytes(b"\x89PNG\r\n\x1a\n")
    app = make_app()
    with TestClient(app) as client:
        body = {"domain_name": "agibotworld", "chunk_size": 16, "image_path": str(cond),
                "raw_actions": [[0.0] * 29] * 16}
        job_id = client.post("/v1/action/forward_dynamics", json=body).json()["id"]
    assert app.state.jobs.get(job_id).params["checkpoint"] == "fp8"


def test_unknown_checkpoint_is_422_invalid_param(make_app):
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "x", "checkpoint": "int4"})
        assert resp.status_code == 422 and resp.json()["code"] == "invalid_param"
    assert app.state.jobs._jobs == {}


def test_pathlike_checkpoint_is_422_invalid_param(make_app):
    # INV-2: checkpoint is a label only; a path-like value is unknown → invalid_param, never a load path.
    app = make_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "x", "checkpoint": "/data/models/evil"})
        assert resp.status_code == 422 and resp.json()["code"] == "invalid_param"
    assert app.state.jobs._jobs == {}
