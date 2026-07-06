"""Spec: shared-schemas — OpenAPI 3.1 contract + job/error components (code-first)."""
import json
from pathlib import Path

from openapi_spec_validator import validate

from app.openapi_export import contract_component_schemas, openapi_dict

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED = REPO_ROOT / "schemas" / "openapi.json"


def test_contract_components_are_pure_and_complete():
    # specs/shared-schemas.md :: Job and JobStatus appear as components
    comps = contract_component_schemas()
    assert {"Job", "JobStatus", "ErrorModel"} <= set(comps)
    assert set(comps["JobStatus"]["enum"]) == {
        "queued",
        "running",
        "succeeded",
        "failed",
        "cancelled",
    }
    props = comps["ErrorModel"]["properties"]
    assert "code" in props and "message" in props


def test_openapi_is_31_with_versioned_health_and_components():
    spec = openapi_dict()
    assert spec["openapi"].startswith("3.1")  # specs :: validates as 3.1
    assert "/v1/health/live" in spec["paths"]  # specs/health-readiness :: versioned
    assert "/v1/health/ready" in spec["paths"]
    schemas = spec["components"]["schemas"]
    assert {"Job", "JobStatus", "ErrorModel"} <= set(schemas)
    validate(spec)  # raises if not a valid OpenAPI 3.1 document


def test_committed_openapi_matches_live_app():
    # specs/shared-schemas.md :: committed schema matches the live app (no drift)
    assert COMMITTED.exists(), "run `make -f deploy/Makefile schemas` to emit schemas/openapi.json"
    assert json.loads(COMMITTED.read_text()) == openapi_dict()
