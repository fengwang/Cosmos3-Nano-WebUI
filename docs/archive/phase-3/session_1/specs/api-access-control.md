# Spec: api-access-control (UX-S1)

Capability: API request authentication / access control.
Delta against the pre-UX-S1 state. Each scenario is a testable case that drives
`tests/api/*`, `tests/test_openapi.py`, `tests/test_metrics_endpoint.py`, and
`webui/lib/*`.

## REMOVED Requirements

### Requirement: X-API-Key authentication gate

**Reason:** Trusted-LAN posture (PRD §3.3). The optional single-key gate is pure
configuration ceremony on a private network and was the only app-layer control
in front of the root-equivalent socket-mounted API (E-01, R-01). Removed
entirely, not defaulted off (no-backward-compat).

**Migration:** No replacement mechanism. Access control becomes network
placement only: ports bind to loopback by default (`BIND_ADDR=127.0.0.1`,
unchanged); LAN exposure is an explicit operator opt-in (INV-4). The
`COSMOS3_API_KEY` env var, the `require_api_key` dependency, the
`UnauthorizedError`→401 mapping, the BFF key injection, and the OpenAPI
`x-api-key` parameters are deleted. An operator with `COSMOS3_API_KEY` set in a
local `.env` may remove it; it is inert after this change.

#### Scenario: keyless request to a formerly-gated route is not rejected

- **WHEN** a client sends a well-formed request to any jobs / generation /
  action / reasoning route with no `X-API-Key` header
- **THEN** the response status SHALL be the route's normal result for that input
  (e.g. 200 / 202 / 422) and SHALL NOT be 401

#### Scenario: a supplied X-API-Key header is inert

- **WHEN** a client sends an `X-API-Key` header (any value) to a formerly-gated
  route
- **THEN** the response SHALL be identical to the same request without the
  header — the header is ignored, with no 401 and no special handling

#### Scenario: no auth code remains anywhere in the tracked tree

- **WHEN** the tracked tree is swept for
  `COSMOS3_API_KEY|X-API-Key|x_api_key|api_key|apiKey|require_api_key|UnauthorizedError`,
  excluding `docs/archive/**`, `.git/`, this session pack's own prose, and the
  single documented `apiKey` mention in `tests/test_private_ref_scan.py`
- **THEN** there SHALL be zero matches

## MODIFIED Requirements

### Requirement: OpenAPI document reflects the open contract

The generated `schemas/openapi.json` MUST be produced from the FastAPI app
(never hand-edited) and MUST contain no `x-api-key` parameter and no auth
security scheme. `webui/lib/api/schema.d.ts` MUST be regenerated from it and
stay in sync. No other schema shape changes (INV-6).

#### Scenario: regenerated OpenAPI has no auth surface

- **WHEN** `schemas/openapi.json` is regenerated from the app and
  `tests/test_openapi.py` runs
- **THEN** the committed document SHALL equal the live app's document, SHALL
  contain zero `x-api-key` occurrences, and `tests/test_openapi.py` SHALL pass

#### Scenario: client types stay in sync

- **WHEN** `pnpm gen:api` regenerates `webui/lib/api/schema.d.ts` from the
  committed `openapi.json`
- **THEN** the file SHALL show no diff (already in sync) and the WebUI typecheck
  SHALL pass

### Requirement: BFF forwards without injecting a key

The WebUI same-origin BFF MUST keep proxying browser requests to the internal
API (INV-7) but MUST NOT inject or read any API key. `filterForwardHeaders` MUST
NOT set an `x-api-key` header. A client-supplied `x-api-key` is treated like any
other non-hop-by-hop header — forwarded, then ignored by the API — with no new
stripping behavior (Decision 2A, INV-3).

#### Scenario: the proxy adds no api key

- **WHEN** the BFF builds the upstream headers for any request
- **THEN** the upstream headers SHALL NOT contain an `x-api-key` set by the
  proxy, and the proxy SHALL still strip hop-by-hop and `host` headers exactly
  as before

### Requirement: health, metrics, and network binding unchanged

`/v1/health/{live,ready}` and `/v1/metrics` MUST remain reachable and
behaviorally unchanged (INV-2). The default published-port binding MUST stay
loopback (`BIND_ADDR=127.0.0.1`); LAN exposure MUST remain an explicit opt-in
(INV-4). Auth removal MUST add no new capability and no behavior regression
beyond dropping the gate (INV-3).

#### Scenario: health and metrics respond without a key

- **WHEN** `/v1/health/live`, `/v1/health/ready`, and `/v1/metrics` are
  requested with no key
- **THEN** each SHALL respond exactly as before auth removal (health readiness
  semantics and metrics exposition unchanged)

#### Scenario: loopback default preserved and no key config remains

- **WHEN** `.env.example` and `deploy/docker-compose.base.yml` are inspected
  after the change
- **THEN** `BIND_ADDR` SHALL still default to `127.0.0.1` and no
  `COSMOS3_API_KEY` entry SHALL remain in either file

### Requirement: typed-error table minus the 401 row

`api/app/errors.py` MUST map every remaining typed domain error to its status
unchanged; the `UnauthorizedError`→401 row and its handler registration MUST be
removed, and `UnauthorizedError` MUST no longer be importable anywhere.

#### Scenario: error mapping intact except unauthorized

- **WHEN** the CPU suite exercises `to_error_response` for the media / action /
  reasoning / untrusted-path / idempotency / transition / not-found / unknown
  errors
- **THEN** each SHALL map to its documented status (413 / 415 / 422 / 409 / 404
  / 500) and there SHALL be no `UnauthorizedError` branch or import remaining
