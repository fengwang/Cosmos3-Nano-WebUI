"""Spec: health-readiness — wired endpoints (Actions: thin shell over pure calc)."""
import asyncio
import time

from fastapi.testclient import TestClient

from app.main import create_app


async def _never_warm(holder):
    """A warmup that never completes — pins readiness in the 'warming' state."""
    await asyncio.Event().wait()


def test_liveness_is_200_while_warming():
    # specs/health-readiness.md :: liveness is 200 while warming
    with TestClient(create_app(warmup=_never_warm)) as client:
        assert client.get("/v1/health/live").status_code == 200


def test_readiness_is_503_warming_before_warmup_completes():
    # specs/health-readiness.md :: readiness is 503 warming before warmup completes
    with TestClient(create_app(warmup=_never_warm)) as client:
        r = client.get("/v1/health/ready")
        assert r.status_code == 503
        assert r.json()["status"] == "warming"


def test_readiness_becomes_200_ready_after_warmup():
    # specs/health-readiness.md :: readiness is 200 ready after warmup completes
    with TestClient(create_app()) as client:  # default warmup completes promptly
        r = client.get("/v1/health/ready")
        for _ in range(100):  # warmup runs in the background; poll the gate
            if r.status_code == 200:
                break
            time.sleep(0.02)
            r = client.get("/v1/health/ready")
        assert r.status_code == 200
        assert r.json()["status"] == "ready"
