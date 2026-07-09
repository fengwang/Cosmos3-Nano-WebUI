"""Code-first OpenAPI 3.1 assembly + emission.

Calculations (pure): ``contract_component_schemas`` / ``build_openapi`` derive the
document from the Pydantic Data models and the app's in-memory routes — no I/O.
Actions (shell): ``install_custom_openapi`` wires ``GET /openapi.json``; ``write``
persists ``schemas/openapi.json``. The committed file is regenerated and diffed in
CI (drift = fail). Refs: project_contract §7, evidence_map E2/E3.
"""
from __future__ import annotations

import json
import sys

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.schemas import Job

OPENAPI_VERSION = "3.1.0"


def contract_component_schemas() -> dict:
    """Pure: component schemas for the async job contract (Job + JobStatus + ErrorModel).

    Derived from the Pydantic models so the contract types appear in the OpenAPI
    document without inventing S6's job endpoints. Same input -> same output, no I/O.
    """
    js = Job.model_json_schema(ref_template="#/components/schemas/{model}")
    defs = js.pop("$defs", {})
    return {"Job": js, **defs}


def build_openapi(app: FastAPI) -> dict:
    """Pure over the app: the FastAPI 3.1 document with the contract components merged.

    Reads only the app's in-memory routes/metadata (deterministic); adds no I/O.
    """
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=OPENAPI_VERSION,
        routes=app.routes,
    )
    components = schema.setdefault("components", {}).setdefault("schemas", {})
    components.update(contract_component_schemas())
    return schema


def install_custom_openapi(app: FastAPI) -> None:
    """Action (app assembly): serve ``build_openapi(app)`` from ``GET /openapi.json``, cached."""

    def _openapi() -> dict:
        if not app.openapi_schema:
            app.openapi_schema = build_openapi(app)
        return app.openapi_schema

    app.openapi = _openapi  # type: ignore[method-assign]


def openapi_dict() -> dict:
    """The canonical document from the default app instance (imports the app lazily)."""
    from app.main import app

    return app.openapi()


def openapi_json_str() -> str:
    """Deterministic JSON serialization (sorted keys, trailing newline) for stable diffs."""
    return json.dumps(openapi_dict(), indent=2, sort_keys=True) + "\n"


def write(path: str) -> None:
    """Action: persist the canonical OpenAPI document to ``path`` ('-' writes to stdout)."""
    text = openapi_json_str()
    if path == "-":
        sys.stdout.write(text)
        return
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


if __name__ == "__main__":
    write(sys.argv[1] if len(sys.argv) > 1 else "schemas/openapi.json")
