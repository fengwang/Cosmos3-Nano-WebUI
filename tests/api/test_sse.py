"""Spec: api-surface-and-errors / async-job-model — SSE progress + Last-Event-ID replay (RK-09).

Streams are read AFTER the job is terminal, so the generator replays a complete log and stops on the
terminal event (no waiting on heartbeats — deterministic).
"""
from __future__ import annotations

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


async def _warm(holder) -> None:
    holder.state = mark_warmed(holder.state)


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("COSMOS3_SSE_HEARTBEAT_SECONDS", "0.1")
    orch = Orchestrator(lambda plane: _NoopWorker(), post_evict_wait=lambda: True)
    return TestClient(create_app(warmup=_warm, orchestrator=orch))


def _submit_and_finish(client: TestClient) -> str:
    job_id = client.post("/v1/jobs", json={"mode": "t2i", "params": {}}).json()["id"]
    for _ in range(300):
        if client.get(f"/v1/jobs/{job_id}").json()["status"] in _TERMINAL:
            break
        time.sleep(0.02)
    return job_id


def test_sse_headers_and_terminal_event(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        job_id = _submit_and_finish(client)
        with client.stream("GET", f"/v1/jobs/{job_id}/events") as stream:
            assert stream.headers["content-type"].startswith("text/event-stream")
            assert stream.headers.get("x-accel-buffering") == "no"
            assert stream.headers.get("cache-control") == "no-cache"
            body = "".join(stream.iter_text())
        assert "event: running" in body
        assert "event: succeeded" in body  # the terminal event is delivered, then the stream closes


def test_sse_last_event_id_replays_only_missed(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        job_id = _submit_and_finish(client)
        with client.stream("GET", f"/v1/jobs/{job_id}/events", headers={"Last-Event-ID": "2"}) as stream:
            body = "".join(stream.iter_text())
        assert "id: 1" not in body and "id: 2" not in body  # already-seen events are not replayed
        assert "id: 3" in body  # only events after id 2


def test_sse_emits_heartbeat_for_a_running_job(tmp_path, monkeypatch):
    # RK-09: a long-running job keeps the connection observable via heartbeats (exercised over the wire)
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("COSMOS3_SSE_HEARTBEAT_SECONDS", "0.05")
    release = threading.Event()

    def blocking_work(record, report):
        report(0.1)
        release.wait(10)  # hold the job 'running' so the heartbeat branch is exercised
        return WorkResult(write_stub(record.id))

    orch = Orchestrator(lambda plane: _NoopWorker(), post_evict_wait=lambda: True)
    with TestClient(create_app(warmup=_warm, orchestrator=orch, job_work=blocking_work)) as client:
        job_id = client.post("/v1/jobs", json={"mode": "t2v", "params": {}}).json()["id"]
        for _ in range(300):
            if client.get(f"/v1/jobs/{job_id}").json()["status"] == "running":
                break
            time.sleep(0.02)
        saw_heartbeat = False
        try:
            with client.stream("GET", f"/v1/jobs/{job_id}/events") as stream:
                for line in stream.iter_lines():
                    if "event: heartbeat" in line:
                        saw_heartbeat = True
                        break
        finally:
            release.set()
        assert saw_heartbeat
