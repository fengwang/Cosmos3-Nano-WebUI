"""Spec: api-surface-and-errors — the job HTTP surface end-to-end (EC-S1/S3/S4/A4/S6 + auth + idempotency).

Uses a TestClient over an app wired with a stub orchestrator (no GPU) + the default stub work (writes
the deterministic PNG to a tmp ARTIFACTS_DIR). Conditioning-path tests set the input allowlist to tmp.
"""
from __future__ import annotations

import base64
import os
import struct
import threading
import time

from fastapi.testclient import TestClient

from app.main import create_app
from app.readiness import mark_warmed
from jobs.artifacts import write_stub
from jobs.runner import WorkResult
from orchestrator.manager import Orchestrator

_TERMINAL = {"succeeded", "failed", "cancelled"}


class _NoopWorker:
    def start(self) -> None: ...
    def wait_ready(self, timeout: float) -> bool:
        return True

    def evict(self) -> None: ...
    def is_alive(self) -> bool:
        return True


def _stub_orch() -> Orchestrator:
    return Orchestrator(lambda plane: _NoopWorker(), post_evict_wait=lambda: True)


class _RecordingOrch:
    """A duck-typed orchestrator that records whether the runner ever dispatched (acquired a plane)."""

    def __init__(self) -> None:
        self.acquired: list = []

    async def acquire(self, plane) -> None:
        self.acquired.append(plane)

    async def evict_all(self) -> None: ...

    def notify_idle(self) -> None: ...


async def _warm(holder) -> None:
    holder.state = mark_warmed(holder.state)


def _client(tmp_path, monkeypatch, *, job_work=None) -> TestClient:
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("COSMOS3_INPUT_ALLOWLIST", str(tmp_path))
    monkeypatch.setenv("COSMOS3_SSE_HEARTBEAT_SECONDS", "0.1")
    kwargs = {"warmup": _warm, "orchestrator": _stub_orch()}
    if job_work is not None:
        kwargs["job_work"] = job_work
    return TestClient(create_app(**kwargs))


def _png_b64(width: int, height: int) -> str:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">II", width, height) + b"\x08\x06\x00\x00\x00"
    data = sig + struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr + b"\x00\x00\x00\x00"
    return base64.b64encode(data).decode()


def _poll_status(client: TestClient, job_id: str, target: set[str], tries: int = 300) -> str:
    for _ in range(tries):
        status = client.get(f"/v1/jobs/{job_id}").json()["status"]
        if status in target:
            return status
        time.sleep(0.02)
    return client.get(f"/v1/jobs/{job_id}").json()["status"]


# ---- EC-S1: async lifecycle ------------------------------------------------------------------
def test_ec_s1_submit_then_fetch_artifact(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        resp = client.post("/v1/jobs", json={"mode": "t2i", "params": {"prompt": "a robot", "resolution": 480}})
        assert resp.status_code == 202
        job = resp.json()
        assert job["status"] == "queued" and job["id"]
        assert _poll_status(client, job["id"], _TERMINAL) == "succeeded"
        view = client.get(f"/v1/jobs/{job['id']}").json()
        assert view["artifact_url"] == f"/v1/jobs/{job['id']}/artifact"
        artifact = client.get(view["artifact_url"])
        assert artifact.status_code == 200
        assert artifact.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_get_unknown_job_is_404(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        resp = client.get("/v1/jobs/does-not-exist")
        assert resp.status_code == 404 and resp.json()["code"] == "not_found"


# ---- EC-S3: edge validation (413/415/422), no SSRF -------------------------------------------
def test_ec_s3_oversized_upload_is_413(tmp_path, monkeypatch):
    monkeypatch.setenv("COSMOS3_MAX_IMAGE_BYTES", "1024")
    with _client(tmp_path, monkeypatch) as client:
        big = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 4000).decode()
        resp = client.post("/v1/jobs", json={"mode": "i2v", "params": {}, "media": {"kind": "image", "data_base64": big}})
        assert resp.status_code == 413 and resp.json()["code"] == "payload_too_large"


def test_ec_s3_wrong_codec_is_415(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        data = base64.b64encode(b"this is plain text, not an image").decode()
        resp = client.post("/v1/jobs", json={"mode": "i2v", "params": {}, "media": {"kind": "image", "data_base64": data}})
        assert resp.status_code == 415 and resp.json()["code"] == "unsupported_media_type"


def test_ec_s3_over_dimension_is_422(tmp_path, monkeypatch):
    monkeypatch.setenv("COSMOS3_MAX_IMAGE_DIMENSION", "100")
    with _client(tmp_path, monkeypatch) as client:
        resp = client.post(
            "/v1/jobs",
            json={"mode": "i2v", "params": {}, "media": {"kind": "image", "data_base64": _png_b64(640, 360)}},
        )
        assert resp.status_code == 422 and resp.json()["code"] == "invalid_dimension"


def test_invalid_output_resolution_is_422(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        resp = client.post("/v1/jobs", json={"mode": "t2i", "params": {"resolution": 123}})
        assert resp.status_code == 422 and resp.json()["code"] == "invalid_dimension"


def test_unknown_mode_is_422(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        resp = client.post("/v1/jobs", json={"mode": "bogus", "params": {}})
        assert resp.status_code == 422


# ---- EC-A4: action dim mismatch → 422 before dispatch ----------------------------------------
def test_ec_a4_action_width_mismatch_is_422(tmp_path, monkeypatch):
    cond = tmp_path / "cond.png"
    cond.write_bytes(b"\x89PNG\r\n\x1a\n")
    with _client(tmp_path, monkeypatch) as client:
        resp = client.post(
            "/v1/jobs",
            json={
                "mode": "forward_dynamics",
                "params": {"domain_name": "av", "chunk_size": 32, "raw_action_width": 10, "image_path": str(cond)},
            },
        )
        assert resp.status_code == 422 and resp.json()["code"] == "width_mismatch"


# ---- EC-S6 / no-SSRF: conditioning path containment ------------------------------------------
def test_ec_s6_conditioning_path_outside_mount_is_422(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        resp = client.post("/v1/jobs", json={"mode": "i2v", "params": {"image_path": "/etc/passwd"}})
        assert resp.status_code == 422 and resp.json()["code"] == "untrusted_path"


def test_no_ssrf_url_conditioning_path_is_422(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        resp = client.post(
            "/v1/jobs", json={"mode": "i2v", "params": {"image_path": "http://169.254.169.254/latest"}}
        )
        assert resp.status_code == 422 and resp.json()["code"] == "untrusted_path"


# ---- EC-S4: cancellation ---------------------------------------------------------------------
def test_ec_s4_cancel_running_job(tmp_path, monkeypatch):
    release = threading.Event()

    def blocking_work(record, report):
        report(0.1)
        release.wait(5)
        return WorkResult(write_stub(record.id))

    with _client(tmp_path, monkeypatch, job_work=blocking_work) as client:
        job_id = client.post("/v1/jobs", json={"mode": "t2v", "params": {}}).json()["id"]
        assert _poll_status(client, job_id, {"running"}) == "running"
        resp = client.post(f"/v1/jobs/{job_id}/cancel")
        release.set()
        assert resp.status_code == 200 and resp.json()["status"] == "cancelled"
        assert client.get(f"/v1/jobs/{job_id}").json()["status"] == "cancelled"


# ---- idempotency -----------------------------------------------------------------------------
def test_idempotency_replay_and_conflict(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        headers = {"Idempotency-Key": "k-1"}
        first = client.post("/v1/jobs", json={"mode": "t2i", "params": {"prompt": "x"}}, headers=headers)
        second = client.post("/v1/jobs", json={"mode": "t2i", "params": {"prompt": "x"}}, headers=headers)
        assert first.json()["id"] == second.json()["id"]  # replayed, not duplicated
        conflict = client.post("/v1/jobs", json={"mode": "t2i", "params": {"prompt": "DIFFERENT"}}, headers=headers)
        assert conflict.status_code == 409 and conflict.json()["code"] == "idempotency_conflict"


# ---- submit-side validation hygiene ----------------------------------------------------------
def test_rejected_submit_does_not_enqueue_or_dispatch(tmp_path, monkeypatch):
    # EC-S3/EC-A4 negative side-effect: an invalid submission is rejected BEFORE enqueue/dispatch
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("COSMOS3_INPUT_ALLOWLIST", str(tmp_path))
    monkeypatch.setenv("COSMOS3_MAX_IMAGE_BYTES", "1024")
    rec_orch = _RecordingOrch()
    app = create_app(warmup=_warm, orchestrator=rec_orch)
    with TestClient(app) as client:
        big = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 4000).decode()
        assert client.post(
            "/v1/jobs", json={"mode": "i2v", "params": {}, "media": {"kind": "image", "data_base64": big}}
        ).status_code == 413
        cond = tmp_path / "c.png"
        cond.write_bytes(b"\x89PNG\r\n\x1a\n")
        assert client.post(
            "/v1/jobs",
            json={
                "mode": "forward_dynamics",
                "params": {"domain_name": "av", "chunk_size": 32, "raw_action_width": 10, "image_path": str(cond)},
            },
        ).status_code == 422
        # malformed scalar param → 422 (not a 500): the H2 regression
        assert client.post("/v1/jobs", json={"mode": "t2i", "params": {"resolution": "abc"}}).status_code == 422
        assert rec_orch.acquired == []  # no orchestrator dispatch occurred (EC-A4)
        assert app.state.jobs._jobs == {}  # no job was enqueued (EC-S3)


def test_jobs_open_without_key_health_and_openapi_exempt(tmp_path, monkeypatch):
    # UX-S1: auth removed — the jobs router is open (no 401 for a keyless request), health stays
    # reachable, and the OpenAPI carries no x-api-key surface.
    with _client(tmp_path, monkeypatch) as client:
        assert client.post("/v1/jobs", json={"mode": "t2i", "params": {}}).status_code == 202
        assert client.get("/v1/health/ready").status_code in (200, 503)
        schema = client.get("/openapi.json")
        assert schema.status_code == 200 and "x-api-key" not in schema.text.lower()


# ---- S7: the Job view surfaces precision + trajectory; the trajectory route serves the sidecar ----
def test_job_view_surfaces_precision_and_trajectory(tmp_path, monkeypatch):
    traj = tmp_path / "j.json"
    traj.write_text("[[1.0, 2.0]]")
    (tmp_path / "vid.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42")

    def work(record, report):
        report(0.5)
        return WorkResult(str(tmp_path / "vid.mp4"), {"precision": "nvfp4", "trajectory_path": str(traj)})

    with _client(tmp_path, monkeypatch, job_work=work) as client:
        job_id = client.post("/v1/jobs", json={"mode": "t2v", "params": {"prompt": "x"}}).json()["id"]
        assert _poll_status(client, job_id, _TERMINAL) == "succeeded"
        view = client.get(f"/v1/jobs/{job_id}").json()
        assert view["precision"] == "nvfp4"
        assert view["trajectory_url"] == f"/v1/jobs/{job_id}/trajectory"
        traj_resp = client.get(view["trajectory_url"])
        assert traj_resp.status_code == 200 and traj_resp.json() == [[1.0, 2.0]]


def test_trajectory_is_404_when_absent(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:  # default stub work → no trajectory
        job_id = client.post("/v1/jobs", json={"mode": "t2i", "params": {}}).json()["id"]
        assert _poll_status(client, job_id, _TERMINAL) == "succeeded"
        assert client.get(f"/v1/jobs/{job_id}/trajectory").status_code == 404


def test_inline_media_persisted_to_a_trusted_path(tmp_path, monkeypatch):
    # sharded-review H2: inline base64 media must be written to a contained trusted file and its path
    # injected into the job params (the worker consumes the path) — never silently dropped.
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("COSMOS3_INPUT_ALLOWLIST", str(tmp_path))
    app = create_app(warmup=_warm, orchestrator=_stub_orch())
    with TestClient(app) as client:
        resp = client.post(
            "/v1/jobs",
            json={"mode": "i2v", "params": {"prompt": "x"}, "media": {"kind": "image", "data_base64": _png_b64(64, 64)}},
        )
        assert resp.status_code == 202
        rec = app.state.jobs.get(resp.json()["id"])
        cond = rec.params.get("image_path")
        assert cond and cond.startswith(str(tmp_path)) and os.path.exists(cond)  # persisted + contained
