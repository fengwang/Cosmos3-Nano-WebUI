# Session 1 (UX-S1) - Remove API-Key Authentication

Contract: `docs/session_1_contract.yaml`
Risk: high
Routing: branch_and_compare (independent test writer + sharded review + adversarial verifier + mandatory human gate)

## Objective

Remove the `X-API-Key` / `COSMOS3_API_KEY` authentication mechanism entirely
from the API, the WebUI BFF, configuration, tests, and the auth-specific lines
of the docs — so a trusted-LAN operator needs no auth configuration at all —
without changing the default network binding and without leaving a single
dangling reference.

## Why This Session Exists

On a trusted LAN the optional API key is pure configuration ceremony: every
operator must reason about it, and the WebUI has to forward it end to end
(`webui/lib/proxy.ts:39`). The mechanism is cleanly compartmentalized
(`docs/evidence_map.md` E-01), so removing it is mechanical — but it is a
**security-posture change**: the API mounts the root-equivalent host Docker
socket (`SECURITY.md:52-55`), and auth was the only application-layer control
in front of the four generation/jobs/action/reasoning routers. This session is
`high` risk and gated on that basis (`R-01`).

## In Scope

1. Delete the auth dependency and its wiring: `api/app/auth.py` (whole file),
   the import and `auth = [Depends(require_api_key)]` in `api/app/main.py:19,211`,
   and `dependencies=auth` on the four routers (`api/app/main.py:215-217,220-226`).
2. Remove the `UnauthorizedError`→401 mapping and handler registration in
   `api/app/errors.py`.
3. Remove the WebUI BFF key injection: the `apiKey` handling in
   `webui/lib/proxy.ts:39` and the `process.env.COSMOS3_API_KEY` read in
   `webui/lib/proxyFetch.ts:30`, keeping the same-origin proxy otherwise intact
   (INV-7).
4. Remove `COSMOS3_API_KEY` from `.env`, `.env.example`, and
   `deploy/docker-compose.base.yml` (both the WebUI and API service
   passthroughs), leaving `BIND_ADDR` and its **loopback default unchanged**
   (INV-4).
5. Regenerate `schemas/openapi.json` from code so no `x-api-key` parameter or
   security scheme remains; keep `tests/test_openapi.py` green.
6. Rewrite the affected tests to assert the **new open contract** rather than
   only deleting old assertions (see Deliverables): backend
   `tests/api/test_auth.py`, `tests/api/test_jobs_api.py`,
   `tests/api/test_sse.py`, `tests/api/test_s7_product_surface_matrix.py`,
   `tests/test_metrics_endpoint.py`, `tests/api/conftest.py`; WebUI
   `webui/lib/proxy.test.ts`, `webui/lib/proxyFetch.test.ts`.
7. Edit only the **auth-specific** lines of `README.md` (`:81,172,188`) and
   `SECURITY.md` (`:46-49`) so no auth documentation dangles. Replace them with
   a slim honest note: no auth, trusted-LAN assumption, loopback default, LAN
   is an explicit opt-in, socket is root-equivalent. The broad README
   restructure is `UX-S4`, not here.

## Out of Scope

- The README features-first restructure and CONTRIBUTING relocation (`UX-S4`).
- Any generation-default change (`UX-S2`) or WebUI declutter (`UX-S3`).
- Changing `BIND_ADDR`, adding TLS, or adding any replacement auth mechanism.
- Docker-socket hardening (archived `R-16`).

## Deliverables

- Auth mechanism removed across API, WebUI BFF, config, and tests, with a
  clean whole-repo `rg --hidden` sweep (`EV-UX-AUTH-SWEEP-CLEAN`).
- A regenerated `schemas/openapi.json` with no auth surface
  (`EV-UX-OPENAPI-INSYNC`).
- Rewritten tests proving the open contract: the formerly-protected routers
  return their normal non-401 responses for the same requests, and
  health/metrics are unchanged (`EV-UX-HEALTH-OPEN-NOAUTH`, `R-10`).
- Slim honest auth/security note in `README.md` and `SECURITY.md`
  (auth-specific lines only).

## Deterministic Checks

```bash
rg --hidden -n "COSMOS3_API_KEY|X-API-Key|x_api_key|api_key|apiKey|require_api_key|UnauthorizedError" -g '!docs/archive/**'
uv run pytest -m "not gpu"
# from webui/
pnpm build && pnpm lint && pnpm typecheck && pnpm test
# regenerate + diff the OpenAPI, then:
uv run pytest tests/test_openapi.py
```

## Exit Criteria

- `GATE-UX-S1-AUTH` passes.
- The auth sweep is clean outside `docs/archive/**`.
- `schemas/openapi.json` regenerates with no `x-api-key`; `tests/test_openapi.py` passes.
- CPU + WebUI suites green; health and metrics still respond without a key.
- `BIND_ADDR` loopback default unchanged; `README.md`/`SECURITY.md` carry the
  slim honest note and no dangling auth prose.
- Mandatory human decision gate cleared before merge (security-posture change).

## Handoff

Hand off to `UX-S4` the exact auth-related lines already changed in
`README.md`/`SECURITY.md` (so the docs session rewrites on the settled state,
`R-09`), and confirm to `UX-S2`/`UX-S3` that no auth plumbing remains in the
request path they will touch.
