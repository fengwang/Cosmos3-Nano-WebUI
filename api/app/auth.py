"""Minimal single-key auth (Action; INV-11 / RK-17).

A constant-time `X-API-Key` check against `COSMOS3_API_KEY`. When the key is **unset**, auth is
disabled with a one-time startup warning (the trusted-lab posture — guardrails/auth MAY be off on a
private network, MUST be on before any external exposure, change-controlled). The dependency is applied
only to the job/artifact routes; health + `/openapi.json` stay exempt so the Docker healthcheck and the
contract remain reachable. Refs: session_6/specs/api-surface-and-errors.md; evidence_map H2.
"""
from __future__ import annotations

import logging
import os
import secrets

from fastapi import Header

_API_KEY_ENV = "COSMOS3_API_KEY"
_log = logging.getLogger("cosmos3.auth")
_warned = False


class UnauthorizedError(Exception):
    """A missing/wrong API key on a protected route (→ 401)."""


def _warn_disabled_once() -> None:
    global _warned
    if not _warned:
        _warned = True
        _log.warning(
            "%s is unset — API authentication is DISABLED (trusted-lab posture). "
            "Set it (and enable guardrails) before any external exposure.",
            _API_KEY_ENV,
        )


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """FastAPI dependency: enforce the API key when configured; allow (with a warning) when unset."""
    key = os.environ.get(_API_KEY_ENV)
    if not key:
        _warn_disabled_once()
        return
    if x_api_key is None or not secrets.compare_digest(x_api_key, key):
        raise UnauthorizedError("invalid or missing API key (X-API-Key)")
