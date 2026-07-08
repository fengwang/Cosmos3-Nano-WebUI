# Specification - CPU Source Smoke

Session: MIG-S3
Capability: CPU Source Smoke

## ADDED Requirements

### Requirement: Imported API compiles

The imported `api/` tree SHALL byte-compile without syntax errors under the
project's Python (>=3.12,<3.13) without CUDA or model weights.

#### Scenario: compileall passes

WHEN `python -m compileall api` is run from the repo root
THEN it SHALL exit 0.

### Requirement: FastAPI app imports torch-free

The FastAPI application SHALL import in a torch-free environment so CPU CI and
local checks do not need GPU dependencies.

#### Scenario: App import succeeds without heavy deps

WHEN `PYTHONPATH=api python -c "import app.main"` is run without `torch`,
`tensorrt_llm`, `vllm`, or CUDA
THEN it SHALL exit 0.

### Requirement: CPU test set passes or failures are classified

The imported CPU-safe test set SHALL pass, or every failure SHALL be classified as
BUG, SPEC_GAP, AMBIGUITY, ENVIRONMENT, or TEST_BUG before any fix.

#### Scenario: CPU tests green or classified

WHEN `python -m pytest -q -m "not gpu"` is run over the imported tests with server
dependencies installed
THEN it SHALL pass
OR each failure SHALL have a recorded Failure Arbiter classification.

### Requirement: OpenAPI schema is in sync

The committed `schemas/openapi.json` SHALL equal the document produced by the
imported app's OpenAPI exporter.

#### Scenario: Regenerated schema matches committed schema

WHEN the OpenAPI document is regenerated via `api/app/openapi_export.py`
THEN it SHALL be byte-equal (or semantically equal after canonical formatting) to
the committed `schemas/openapi.json`
OR the difference SHALL be recorded and dispositioned.

### Requirement: WebUI toolchain checks are best-effort with a clear disposition

WebUI lint/typecheck/unit tests SHALL be run when node and network are available;
otherwise they SHALL be classified ENVIRONMENT and handed to MIG-S5.

#### Scenario: WebUI checks run or are deferred

WHEN the WebUI checks are attempted
THEN they SHALL pass
OR their unavailability SHALL be classified ENVIRONMENT with a handoff note to
MIG-S5
AND the WebUI structure, manifest, and lockfile SHALL still be present and
private-reference clean.
