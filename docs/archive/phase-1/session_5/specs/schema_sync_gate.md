# Specification - Schema Sync Gate

Session: MIG-S5
Capability: Schema Sync Gate

## ADDED Requirements

### Requirement: App-to-OpenAPI drift fails CI

CI MUST fail if the FastAPI application's generated OpenAPI document differs from
the committed `schemas/openapi.json`. This check MUST be torch-free and run in the
Python job. The committed document MUST also validate as OpenAPI 3.1.

#### Scenario: Committed OpenAPI matches the app

WHEN `tests/test_openapi.py` runs under `pytest -m "not gpu"`
THEN it SHALL regenerate the OpenAPI document from the app
AND SHALL fail if it differs from committed `schemas/openapi.json`
AND SHALL validate the committed document as OpenAPI 3.1.

#### Scenario: Drift is detected

WHEN the app's routes or models change without regenerating `schemas/openapi.json`
THEN the Python job SHALL fail.

### Requirement: OpenAPI-to-TypeScript drift fails CI

CI MUST fail if the generated WebUI client types `webui/lib/api/schema.d.ts` differ
from what `pnpm gen:api` produces from `schemas/openapi.json`.

#### Scenario: Generated types match the schema

WHEN the WebUI job runs `pnpm gen:api`
THEN `git diff --exit-code webui/lib/api/schema.d.ts` SHALL report no change.

#### Scenario: Stale committed types fail CI

WHEN `schemas/openapi.json` changes without regenerating `schema.d.ts`
THEN the WebUI job's `git diff --exit-code` step SHALL fail.
