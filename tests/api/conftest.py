"""Shared fixtures for the S7 capability-route tests.

A `create_app()` factory wired with a stub orchestrator (no GPU) + the default stub work, so the
generation/action routes are exercised end-to-end through the real app + error handlers on the host.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI

from app.main import create_app
from app.readiness import mark_warmed
from orchestrator.manager import Orchestrator


class _NoopWorker:
    def start(self) -> None: ...

    def wait_ready(self, timeout: float) -> bool:
        return True

    def evict(self) -> None: ...

    def is_alive(self) -> bool:
        return True


async def _warm(holder) -> None:
    holder.state = mark_warmed(holder.state)


@pytest.fixture
def make_app(tmp_path, monkeypatch):
    """Factory → a stub-orchestrator app. Pass env overrides as kwargs (e.g. COSMOS3_FP8_MODEL_DIR=...)."""

    def _factory(**env: str) -> FastAPI:
        monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
        monkeypatch.setenv("COSMOS3_INPUT_ALLOWLIST", str(tmp_path))
        monkeypatch.delenv("COSMOS3_API_KEY", raising=False)
        monkeypatch.delenv("COSMOS3_FP8_MODEL_DIR", raising=False)
        monkeypatch.delenv("COSMOS3_CHECKPOINT_LABEL", raising=False)  # default deployment = fp8
        for key, value in env.items():
            monkeypatch.setenv(key, value)
        orch = Orchestrator(lambda plane: _NoopWorker(), post_evict_wait=lambda: True)
        return create_app(warmup=_warm, orchestrator=orch)

    return _factory
