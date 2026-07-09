"""Spec: api-surface-and-errors — minimal single-key auth (RK-17 / INV-11), unit level."""
from __future__ import annotations

import pytest

from app.auth import UnauthorizedError, require_api_key


def test_auth_disabled_when_key_unset(monkeypatch):
    monkeypatch.delenv("COSMOS3_API_KEY", raising=False)
    assert require_api_key(None) is None  # disabled (lab posture) — no raise


def test_auth_enforced_when_key_set(monkeypatch):
    monkeypatch.setenv("COSMOS3_API_KEY", "s3cret")
    assert require_api_key("s3cret") is None
    with pytest.raises(UnauthorizedError):
        require_api_key(None)
    with pytest.raises(UnauthorizedError):
        require_api_key("wrong")
