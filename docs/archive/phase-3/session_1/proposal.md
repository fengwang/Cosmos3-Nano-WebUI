# UX-S1 Proposal — Remove API-Key Authentication

Date: 2026-07-15
Derived from: `docs/session_1/brainstorming.md` (approved 2026-07-15).

## Motivation

On a trusted LAN the optional `X-API-Key`/`COSMOS3_API_KEY` gate is pure
configuration ceremony (PRD §1; E-01) — and it was the only app-layer control
in front of a root-equivalent socket-mounted API (E-03, R-01). Removing it
end-to-end makes zero-config the correct first run while keeping an honest
security posture (loopback default + documented socket risk). This is the first
and highest-risk UX-simplification session (PRD §7).

## Specific changes agreed

1. Delete `api/app/auth.py`; remove its import, the `Depends(require_api_key)`
   list, and `dependencies=auth` on the four routers in `api/app/main.py` (also
   drop the now-unused `Depends` import).
2. Remove the `UnauthorizedError`→401 branch and its handler registration in
   `api/app/errors.py`.
3. Remove BFF key injection: drop the `apiKey` parameter from
   `filterForwardHeaders` (`webui/lib/proxy.ts`) and the
   `process.env.COSMOS3_API_KEY` read (`webui/lib/proxyFetch.ts`), keeping the
   same-origin proxy otherwise intact (Decision 2A; INV-7).
4. Remove `COSMOS3_API_KEY` from `.env.example` and both service passthroughs in
   `deploy/docker-compose.base.yml`; leave `BIND_ADDR=127.0.0.1` untouched
   (INV-4). (`.env` is untracked — no committed change; noted for handoff.)
5. Regenerate `schemas/openapi.json` (drops 14 `x-api-key` header params) and
   `webui/lib/api/schema.d.ts` from code — never hand-edited (INV-6).
6. Rewrite the auth-coupled tests to assert the **open** contract (Decision
   1B), not merely delete assertions.
7. Edit only the auth-specific lines of `README.md` (`:81,:172,:188`) and
   `SECURITY.md` (`:46-49`) into a slim honest note.
8. **Amendment UX-S1-A1:** add `tests/api/test_errors.py` to the blast radius;
   refine the auth sweep to exclude `.git/`; record the
   `tests/test_private_ref_scan.py:12` `apiKey` mention as an allowed legitimate
   reference. Logged in `docs/risk_register.md` + `docs/evidence_map.md` (E-14).

## Capabilities

### Modified capability: `api-access-control`

The API's request-authentication requirement changes from *"optional single-key
`X-API-Key` gate on the jobs/generation/action/reasoning routers"* to *"no
application-layer authentication; all routes open; network placement (loopback
default) is the only access control."* Spec:
`docs/session_1/specs/api-access-control.md`. This is the only capability; it
carries the REMOVED requirement (the gate), the MODIFIED requirements (open
routers; BFF forwarding without injection; OpenAPI without the auth surface;
error table minus the 401 row) and the unchanged invariants (health/metrics;
loopback; schema shapes).

No new capabilities are introduced.

## Impact

- **Code:** `api/app/auth.py` (deleted), `api/app/main.py`, `api/app/errors.py`,
  `webui/lib/proxy.ts`, `webui/lib/proxyFetch.ts`.
- **Generated (regenerated, not hand-edited):** `schemas/openapi.json`,
  `webui/lib/api/schema.d.ts`.
- **Config:** `.env.example`, `deploy/docker-compose.base.yml`.
- **Tests:** `tests/api/test_auth.py` (deleted), `tests/api/test_jobs_api.py`,
  `tests/api/test_sse.py`, `tests/api/test_s7_product_surface_matrix.py`,
  `tests/api/test_errors.py` (UX-S1-A1), `tests/api/conftest.py`,
  `tests/test_metrics_endpoint.py`, `webui/lib/proxy.test.ts`,
  `webui/lib/proxyFetch.test.ts`.
- **Docs:** `README.md`, `SECURITY.md` (auth lines only);
  `docs/risk_register.md`, `docs/evidence_map.md` (amendment log);
  `docs/session_1/**`.
- **APIs/behavior:** only the `X-API-Key` parameter is removed from the four
  routers; no request/response schema shape changes (INV-6); health/metrics
  unchanged (INV-2); no new capability (INV-3).
- **Dependencies:** none added or removed.
