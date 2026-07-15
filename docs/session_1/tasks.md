# UX-S1 Tasks — Remove API-Key Authentication

Ordered by dependency. Each task is verifiable. TDD micro-steps live in
`plan.md`; the WHAT lives in `specs/api-access-control.md`; the HOW in
`design.md`.

## 1. Preconditions & amendment
- [ ] 1.1 Green baseline recorded (CPU `486 passed`; WebUI build/lint/typecheck + `209` tests). *(done pre-edit)*
- [ ] 1.2 Log amendment **UX-S1-A1** in `docs/risk_register.md`; update `docs/evidence_map.md` E-14 to include `tests/api/test_errors.py`.

## 2. API auth removal (TDD)
- [ ] 2.1 Write the failing open-contract tests first: matrix keyless→non-401 + `x-api-key` inert (`test_s7_product_surface_matrix.py`); errors table minus 401 (`test_errors.py`).
- [ ] 2.2 Delete `api/app/auth.py`.
- [ ] 2.3 `api/app/main.py`: remove the auth import, the `auth = [Depends(require_api_key)]` line, and `dependencies=auth` on the four routers; drop the now-unused `Depends` import.
- [ ] 2.4 `api/app/errors.py`: remove the `UnauthorizedError` import, its 401 branch, and its handler-registration entry.
- [ ] 2.5 Targeted check: `uv run pytest tests/api/test_errors.py tests/api/test_s7_product_surface_matrix.py tests/api/test_jobs_api.py`.

## 3. Config
- [ ] 3.1 Remove `COSMOS3_API_KEY` from `.env.example` (keep `BIND_ADDR=127.0.0.1`).
- [ ] 3.2 Remove both `COSMOS3_API_KEY` passthroughs and the auth-off comment in `deploy/docker-compose.base.yml` (keep the loopback default and its comment).

## 4. WebUI BFF (TDD)
- [ ] 4.1 Rewrite `webui/lib/proxy.test.ts` / `webui/lib/proxyFetch.test.ts` to the open contract (no key injection; headers still filtered).
- [ ] 4.2 `webui/lib/proxy.ts`: drop the `apiKey` parameter and the `x-api-key` set; update the docstring.
- [ ] 4.3 `webui/lib/proxyFetch.ts`: drop the `process.env.COSMOS3_API_KEY` argument.
- [ ] 4.4 Targeted check: `pnpm -C webui run test`.

## 5. Regenerate generated artifacts (never hand-edited)
- [ ] 5.1 `PYTHONPATH=api uv run python -m app.openapi_export schemas/openapi.json`.
- [ ] 5.2 `pnpm -C webui run gen:api`; confirm `git diff --exit-code webui/lib/api/schema.d.ts` is clean.
- [ ] 5.3 Targeted check: `uv run pytest tests/test_openapi.py`; assert zero `x-api-key` in `schemas/openapi.json`.

## 6. Remaining test rewrites
- [ ] 6.1 Delete `tests/api/test_auth.py`.
- [ ] 6.2 `tests/api/test_errors.py`: drop the `UnauthorizedError` import + `test_unauthorized_maps_to_401`.
- [ ] 6.3 `tests/api/test_jobs_api.py`: remove the api-key fixture path + the `test_auth_enforced…` test; confirm the open jobs behavior still asserted.
- [ ] 6.4 `tests/api/test_sse.py`: remove the `delenv("COSMOS3_API_KEY")` lines.
- [ ] 6.5 `tests/test_metrics_endpoint.py`: rewrite `test_metrics_endpoint_needs_no_api_key` to assert keyless metrics (no `setenv`).
- [ ] 6.6 `tests/api/conftest.py`: remove the `delenv("COSMOS3_API_KEY")` fixture line.

## 7. Docs (auth-specific lines only)
- [ ] 7.1 `README.md` `:81,:172,:188` → slim honest note (design D6 wording).
- [ ] 7.2 `SECURITY.md` `:46-49` → slim honest note.

## 8. Full verification
- [ ] 8.1 Refined auth sweep clean (excl. `docs/archive/**`, `.git/`, pack prose, scanner-doc mention).
- [ ] 8.2 `uv run pytest -m "not gpu"` green.
- [ ] 8.3 `pnpm -C webui run build && … lint && … typecheck && … test` green.
- [ ] 8.4 `uv run pytest tests/test_openapi.py` green; `schema.d.ts` diff clean.

## 9. Review & verification
- [ ] 9.1 Sharded review (correctness / security / tests / architecture / performance); fix High/Critical only, then re-check.
- [ ] 9.2 Adversarial verifier against the done condition; classify any failure via the Failure Arbiter.
- [ ] 9.3 Handoff + eval seeds; **stop at the mandatory human gate** (no push/PR/merge).
