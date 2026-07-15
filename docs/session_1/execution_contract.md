# UX-S1 Execution Contract

Derived from `session_1_contract.yaml` + amendment **UX-S1-A1**. This is the
binding, checkable frame for implementation.

## Planned file changes

- **Deleted:** `api/app/auth.py`, `tests/api/test_auth.py`.
- **Edited (code):** `api/app/main.py`, `api/app/errors.py`,
  `webui/lib/proxy.ts`, `webui/lib/proxyFetch.ts`.
- **Edited (tests):** `tests/api/test_errors.py` *(A1)*,
  `tests/api/test_jobs_api.py`, `tests/api/test_sse.py`,
  `tests/api/test_s7_product_surface_matrix.py`, `tests/api/conftest.py`,
  `tests/test_metrics_endpoint.py`, `webui/lib/proxy.test.ts`,
  `webui/lib/proxyFetch.test.ts`.
- **Regenerated (never hand-edited):** `schemas/openapi.json`,
  `webui/lib/api/schema.d.ts`.
- **Config:** `.env.example`, `deploy/docker-compose.base.yml`.
- **Docs:** `README.md` (`:81,:172,:188`), `SECURITY.md` (`:46-49`),
  `docs/risk_register.md`, `docs/evidence_map.md`, `docs/session_1/**`.

## Allowed blast radius

`session_1_contract.yaml.blast_radius.allowed_files` **plus**
`tests/api/test_errors.py` (UX-S1-A1). Forbidden: every other file — in
particular the `BIND_ADDR` default value (stays `127.0.0.1`), any other
`api/**` or `webui/**` source, `deploy/**` other than the base compose,
`docs/archive/**`, and any model-weight/generated-media file.

## First test to write

`tests/api/test_s7_product_surface_matrix.py::test_openapi_has_no_api_key` —
**RED** against current code (the live app's OpenAPI carries `x-api-key`
parameters), **GREEN** once the `require_api_key` dependency is removed from
`api/app/main.py`.

## Checks after each task

- After API edits: `uv run pytest tests/api/test_errors.py tests/api/test_s7_product_surface_matrix.py`.
- After WebUI edits: `pnpm -C webui run test`.
- After regen: `uv run pytest tests/test_openapi.py`; `git diff --exit-code webui/lib/api/schema.d.ts`; `rg -c -i x-api-key schemas/openapi.json` → 0.
- After config/docs: `rg -n "COSMOS3_API_KEY|X-API-Key" .env.example deploy/docker-compose.base.yml README.md SECURITY.md` → none.
- Full gate: `uv run pytest -m "not gpu"`; `pnpm -C webui run build && … lint && … typecheck && … test`; refined `--hidden` sweep excluding `.git` + `docs/archive`.

## Review axes (sharded, high-risk)

correctness · security · tests · architecture · performance.

## Adversarial verifier brief

Fresh context; sees only `session_1_contract.yaml`, the diff, and this pack's
evidence. Job: **falsify** "GATE-UX-S1-AUTH passes." Probe specifically:
1. a leftover `Depends`/gate on any of the four routers (grep the router includes);
2. a sweep that "passed" only by omitting `--hidden` (misses `.env.example`) or by misattributing `.git`/scanner-doc noise;
3. `schemas/openapi.json` hand-edited rather than regenerated (compare to a fresh `openapi_export` run + `test_openapi.py`);
4. the open contract asserted by deletions only, with no positive keyless-→-non-401 / inert-key / openapi-clean test;
5. a residual `x-api-key` spoofing seam in the BFF (and confirm Decision 2A passthrough is intentional, not accidental stripping);
6. `BIND_ADDR` moved off `127.0.0.1`;
7. health/metrics behavior drift;
8. `webui/lib/api/schema.d.ts` / `openapi.json` drift vs code.

## Concrete done condition

`GATE-UX-S1-AUTH`: refined auth sweep clean (only pack prose + the one
scanner-doc mention remain); `schemas/openapi.json` regenerated with **zero**
`x-api-key` and `tests/test_openapi.py` green; CPU suite (`-m "not gpu"`) green;
WebUI build/lint/typecheck/test green; `schema.d.ts` in sync; health + metrics
respond keyless; the four formerly-gated routers return non-401 keyless;
`BIND_ADDR` loopback default unchanged; `README.md`/`SECURITY.md` carry the slim
honest note with no dangling auth prose. **Then STOP** at the mandatory pre-merge
human decision gate (no push / PR / merge).
