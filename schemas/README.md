# schemas/

Code-first contract artifacts for the Cosmos3-Nano serving API.

- **`openapi.json`** — the OpenAPI **3.1** document, **generated** from the FastAPI app
  (`api/app`). It is the source of the §7 `GET /openapi.json` contract and the basis
  for WebUI type generation in later sessions. Do **not** hand-edit.

## Regenerate / verify

```bash
# regenerate schemas/openapi.json from the FastAPI app
PYTHONPATH=api python -m app.openapi_export schemas/openapi.json
# fail if the committed file drifts from the app, and validate as OpenAPI 3.1
PYTHONPATH=api python -m pytest -q tests/test_openapi.py
```

The Pydantic models in `api/app/schemas.py` are the source of truth: `JobStatus`,
`Job`, `ErrorModel` (async-job contract), and `HealthStatus`. The job/error types are
injected as reusable components even though their endpoints arrive in later sessions
(S6/S7).
