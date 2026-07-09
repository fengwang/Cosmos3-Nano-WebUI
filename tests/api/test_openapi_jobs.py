"""Spec: api-surface-and-errors — the OpenAPI 3.1 document carries the job surface + stays in sync."""
from __future__ import annotations

import json
from pathlib import Path

from openapi_spec_validator import validate

from app.openapi_export import openapi_dict

_JOB_PATHS = (
    "/v1/jobs",
    "/v1/jobs/{job_id}",
    "/v1/jobs/{job_id}/events",
    "/v1/jobs/{job_id}/artifact",
    "/v1/jobs/{job_id}/cancel",
)


def test_openapi_31_contains_job_surface_and_validates():
    spec = openapi_dict()
    assert spec["openapi"].startswith("3.1")
    for path in _JOB_PATHS:
        assert path in spec["paths"], f"missing job path {path}"
    schemas = spec["components"]["schemas"]
    assert {"Job", "JobStatus", "ErrorModel", "JobSubmit"} <= set(schemas)
    validate(spec)  # raises if not a valid OpenAPI 3.1 document


def test_committed_contract_has_jobs_and_matches_live():
    committed = json.loads((Path(__file__).resolve().parents[2] / "schemas" / "openapi.json").read_text())
    assert "/v1/jobs" in committed["paths"]
    assert committed == openapi_dict()  # no drift (regenerate after any contract change)
