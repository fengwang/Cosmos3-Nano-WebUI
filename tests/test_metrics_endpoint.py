"""S11: GET /v1/metrics — 200 Prometheus exposition, no auth required, absent from the OpenAPI.

Spec: metrics-endpoint (endpoint). Deterministic-check #1. The no-auth posture mirrors /v1/health/* (INV-1
private-net); include_in_schema=False keeps schemas/openapi.json un-drifted (schemas/** is out of radius).
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from prometheus_client import CONTENT_TYPE_LATEST

from app.main import create_app, default_warmup


def _client() -> TestClient:
    return TestClient(create_app(warmup=default_warmup))


def test_metrics_endpoint_returns_prometheus_exposition():
    client = _client()
    client.get("/v1/health/live")  # produce one HTTP sample
    resp = client.get("/v1/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == CONTENT_TYPE_LATEST
    assert resp.headers["content-type"].startswith("text/plain")
    body = resp.text
    assert "cosmos3_http_requests_total" in body
    assert "cosmos3_jobs" in body  # queue-depth / state gauge
    assert "cosmos3_plane_resident" in body


def test_metrics_endpoint_needs_no_api_key(monkeypatch):
    monkeypatch.setenv("COSMOS3_API_KEY", "secret-key")
    client = _client()
    # a protected route rejects without the key ...
    protected = client.post("/v1/jobs", json={"mode": "t2v", "params": {"prompt": "x"}})
    assert protected.status_code == 401
    # ... but /v1/metrics does not require it (private-net scraper)
    assert client.get("/v1/metrics").status_code == 200


def test_metrics_absent_from_openapi():
    client = _client()
    schema = client.get("/openapi.json").json()
    assert "/v1/metrics" not in schema["paths"]
