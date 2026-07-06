"""Startup hook tests (torch-free → run in the host loop).

Green here proves `app.main` imports torch-free and the production startup hook
marks readiness without loading any GPU model (INV-P2-2).
"""
from __future__ import annotations

import asyncio
import inspect

import app.main
from app.main import ReadinessHolder, default_warmup
from app.readiness import is_ready


def test_main_imports_torch_free_and_exposes_default_warmup():
    assert hasattr(app.main, "default_warmup")
    assert not hasattr(app.main, "oracle_warmup")
    assert not hasattr(app.main, "stub_warmup")


def test_default_warmup_marks_ready():
    holder = ReadinessHolder()
    assert not is_ready(holder.state)
    asyncio.run(default_warmup(holder))
    assert is_ready(holder.state)


def test_create_app_uses_default_warmup():
    sig = inspect.signature(app.main.create_app)
    assert sig.parameters["warmup"].default is app.main.default_warmup


def test_readiness_holder_has_no_adapter():
    """INV-P2-2: ReadinessHolder SHALL NOT have an adapter field (no GPU model reference)."""
    holder = ReadinessHolder()
    assert not hasattr(holder, "adapter")
