"""Hermetic (GPU-free) product-surface contract tests for the S7 eval matrix.

These encode the matrix invariants as fast, deterministic tests against the REAL app
(`create_app` + a stub orchestrator + a stub `work` that echoes the resolved checkpoint as
`precision` and writes a typed artifact). Scope = the route→params→job-router plumbing + artifact
typing + failure hygiene — i.e. everything except the actual GPU work. The live matrix
(`docs/session_7/outputs/run_matrix.py`) witnesses the same invariants on real hardware, and
`tests/test_vllm_omni_work.py` covers the real adapter's precision reporting.

Spec: docs/session_7/specs/product-surface-mode-matrix.md
Adversarial cases covered: "WebUI shows NVFP4 but backend says FP8", "default route secretly selects
NVFP4", "t2i stored as video", "failed job leaves a partial artifact visible as success".
"""
from __future__ import annotations

import os
import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.readiness import mark_warmed
from jobs import artifacts
from jobs.runner import WorkResult
from orchestrator.manager import Orchestrator

_TERMINAL = {"succeeded", "failed", "cancelled"}
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_MP4_MAGIC = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"


class _NoopWorker:
    def start(self) -> None: ...
    def wait_ready(self, timeout: float) -> bool: return True
    def evict(self) -> None: ...
    def is_alive(self) -> bool: return True


async def _warm(holder) -> None:
    holder.state = mark_warmed(holder.state)


def _echo_work(record, report) -> WorkResult:
    """Stub work: fail on the `[fail]` marker; else write a typed artifact and report the SERVED
    precision as the checkpoint the edge resolved into the job params (models real work.py D4)."""
    report(0.5)
    if "[fail]" in (record.params.get("prompt") or ""):
        raise RuntimeError("induced failure (contract test)")
    ext = "png" if record.mode == "t2i" else "mp4"
    data = _PNG_MAGIC if ext == "png" else _MP4_MAGIC
    os.makedirs(artifacts.artifacts_dir(), exist_ok=True)
    path = artifacts.artifact_path_for(record.id, ext=ext)
    with open(path, "wb") as handle:
        handle.write(data)
    precision = record.params.get("checkpoint") or "fp8"
    return WorkResult(path, {"precision": precision, "engine": "stub"})


@pytest.fixture
def make_matrix_app(tmp_path, monkeypatch):
    def _factory(checkpoint: str | None = None):
        monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
        monkeypatch.setenv("COSMOS3_INPUT_ALLOWLIST", str(tmp_path))
        if checkpoint is None:  # S6: single-checkpoint deployment; default = fp8
            monkeypatch.delenv("COSMOS3_CHECKPOINT_LABEL", raising=False)
        else:
            monkeypatch.setenv("COSMOS3_CHECKPOINT_LABEL", checkpoint)
        orch = Orchestrator(lambda plane: _NoopWorker(), post_evict_wait=lambda: True)
        return create_app(warmup=_warm, orchestrator=orch, job_work=_echo_work)
    return _factory


def _poll(client: TestClient, job_id: str, target: set[str] = _TERMINAL, tries: int = 300) -> dict:
    for _ in range(tries):
        body = client.get(f"/v1/jobs/{job_id}").json()
        if body["status"] in target:
            return body
        time.sleep(0.02)
    return client.get(f"/v1/jobs/{job_id}").json()


def _run(client: TestClient, route: str, body: dict) -> dict:
    resp = client.post(route, json=body)
    assert resp.status_code == 202, resp.text
    return _poll(client, resp.json()["id"])


def _cond_image(tmp_path):
    p = tmp_path / "cond.png"
    p.write_bytes(_PNG_MAGIC)
    return str(p)


# --- attribution: served precision == requested checkpoint (the spine) ---

def test_default_request_is_served_by_fp8(make_matrix_app):
    with TestClient(make_matrix_app()) as client:
        job = _run(client, "/v1/generation/t2v", {"prompt": "x"})
    assert job["status"] == "succeeded"
    assert job["precision"] == "fp8"  # INV-3: default is FP8, never nvfp4


def test_nvfp4_deployment_serves_nvfp4(make_matrix_app):
    # S6: nvfp4 is served by the nvfp4 STACK (implicit), not by a per-request selector on an fp8 stack.
    with TestClient(make_matrix_app(checkpoint="nvfp4")) as client:
        job = _run(client, "/v1/generation/t2v", {"prompt": "x"})
    assert job["precision"] == "nvfp4"


def test_explicit_matching_label_is_served(make_matrix_app):
    with TestClient(make_matrix_app()) as client:
        job = _run(client, "/v1/generation/t2v", {"prompt": "x", "checkpoint": "fp8"})
    assert job["precision"] == "fp8"


def test_mismatched_checkpoint_rejected_no_enqueue(make_matrix_app):
    # S6/INV-2: a known-but-undeployed label is rejected at the edge, never served by the other stack.
    app = make_matrix_app()  # fp8 deployment
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "x", "checkpoint": "nvfp4"})
        assert resp.status_code == 422 and resp.json()["code"] == "invalid_param"
    assert app.state.jobs._jobs == {}


# --- artifact media type per mode (the deployed checkpoint is implicit) ---

def _artifact_bytes(client: TestClient, job: dict) -> bytes:
    assert job["artifact_url"], job
    resp = client.get(job["artifact_url"])
    assert resp.status_code == 200
    return resp.content


def test_t2i_artifact_is_png_not_video(make_matrix_app):
    with TestClient(make_matrix_app()) as client:
        job = _run(client, "/v1/generation/t2i", {"prompt": "x"})
        content = _artifact_bytes(client, job)
    assert content.startswith(_PNG_MAGIC) and b"ftyp" not in content[:32]


def test_t2v_artifact_is_video(make_matrix_app):
    with TestClient(make_matrix_app()) as client:
        job = _run(client, "/v1/generation/t2v", {"prompt": "x"})
        content = _artifact_bytes(client, job)
    assert b"ftyp" in content[:32]


def test_i2v_artifact_is_video(make_matrix_app, tmp_path):
    with TestClient(make_matrix_app()) as client:
        job = _run(client, "/v1/generation/i2v", {"prompt": "x", "image_path": _cond_image(tmp_path)})
        content = _artifact_bytes(client, job)
    assert job["precision"] == "fp8" and b"ftyp" in content[:32]


def test_forward_dynamics_artifact_is_video(make_matrix_app, tmp_path):
    body = {"domain_name": "agibotworld", "chunk_size": 16, "checkpoint": "fp8",
            "image_path": _cond_image(tmp_path), "raw_actions": [[0.0] * 29] * 16}
    with TestClient(make_matrix_app()) as client:
        job = _run(client, "/v1/action/forward_dynamics", body)
        content = _artifact_bytes(client, job)
    assert job["precision"] == "fp8" and b"ftyp" in content[:32]


# --- security: request-supplied checkpoint paths rejected at the edge (INV-2) ---

@pytest.mark.parametrize("evil", ["/data/models/evil", "../../etc/passwd", "http://x/y", "nvfp4/../fp8"])
def test_evil_checkpoint_rejected_no_enqueue(make_matrix_app, evil):
    app = make_matrix_app()
    with TestClient(app) as client:
        resp = client.post("/v1/generation/t2i", json={"prompt": "x", "checkpoint": evil})
        assert resp.status_code == 422 and resp.json()["code"] == "invalid_param"
    assert app.state.jobs._jobs == {}  # rejected before any job dispatch


# --- failure hygiene: a failed job never exposes a partial artifact as success ---

def test_failed_job_exposes_no_artifact(make_matrix_app):
    with TestClient(make_matrix_app()) as client:
        resp = client.post("/v1/generation/t2v", json={"prompt": "boom [fail]"})
        assert resp.status_code == 202
        job_id = resp.json()["id"]
        job = _poll(client, job_id)
        assert job["status"] == "failed"
        assert job.get("artifact_url") is None
        assert job.get("error") is not None
        assert client.get(f"/v1/jobs/{job_id}/artifact").status_code == 404


# --- open access: no API-key gate remains on the formerly-protected routers (UX-S1) ---


def test_formerly_gated_routers_open_without_key(make_matrix_app):
    """Each formerly-gated router returns a normal non-401 result with no X-API-Key (UX-S1)."""
    with TestClient(make_matrix_app()) as client:
        assert client.post("/v1/jobs", json={"mode": "t2i", "params": {"prompt": "x"}}).status_code == 202
        assert client.post("/v1/generation/t2v", json={"prompt": "x"}).status_code == 202
        # action + reasoning: even an invalid body validates (422), proving there is no auth gate in front.
        assert client.post("/v1/action/forward_dynamics", json={}).status_code != 401
        assert client.post("/v1/reason", json={}).status_code != 401


def test_supplied_x_api_key_is_inert(make_matrix_app):
    """A client-supplied X-API-Key changes nothing — the header is ignored, not a gate (Decision 2A)."""
    with TestClient(make_matrix_app()) as client:
        without = client.post("/v1/generation/t2v", json={"prompt": "x"})
        withkey = client.post("/v1/generation/t2v", json={"prompt": "x"}, headers={"X-API-Key": "anything"})
    assert without.status_code == withkey.status_code == 202


def test_openapi_has_no_api_key(make_matrix_app):
    """The live app's OpenAPI carries no x-api-key parameter and no auth security scheme (INV-6)."""
    with TestClient(make_matrix_app()) as client:
        resp = client.get("/openapi.json")
    spec_text = resp.text
    spec = resp.json()
    assert "x-api-key" not in spec_text.lower()
    assert "securitySchemes" not in (spec.get("components") or {})
