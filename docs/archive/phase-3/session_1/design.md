# UX-S1 Design — Remove API-Key Authentication

Date: 2026-07-15
Inputs: `proposal.md`; `project_contract.md` (INV-2/3/4/6/7; GATE-UX-S1-AUTH);
`evidence_map.md`.

## Context

`require_api_key` is a FastAPI dependency applied as
`dependencies=[Depends(require_api_key)]` to four routers. It raises
`UnauthorizedError` (→401 via the `errors.py` table) when `COSMOS3_API_KEY` is
set and the header is missing/wrong, and no-ops (with a one-time startup
warning) when the env var is unset. The BFF injects the key server-side.
Health/metrics are already dependency-free. The mechanism is compartmentalized
(E-01), so removal is excision, not refactor.

## Goals

- Remove the entire `X-API-Key`/`COSMOS3_API_KEY` path with **no dangling
  reference** (FR-1).
- Prove the resulting **open** contract by tests (Decision 1B), not by deletion
  alone.
- Keep health/metrics, loopback bind, schema shapes, and BFF same-origin
  posture invariant (INV-2/4/6/7).

## Non-Goals

- No `BIND_ADDR` change, TLS, or replacement auth. No socket hardening (R-16).
  No README restructure (UX-S4).

## Decisions

- **D1 — mechanical excision, no compatibility shim.** Delete `auth.py`
  outright and remove every reference, rather than leaving a stub that always
  returns. Rationale: no-backward-compat directive; a stub would itself be a
  dangling reference the sweep must catch. Also drop the now-unused `Depends`
  import from `main.py` (else ruff F401).
- **D2 — errors table shrinks by one row.** Remove only the `UnauthorizedError`
  branch (`errors.py:55-56`) and its handler-registration entry (line 78); the
  rest of the typed-error→status table is untouched (INV-3). `UnauthorizedError`
  ceases to exist as a symbol, so `tests/api/test_errors.py` drops its import
  and the 401 case (UX-S1-A1).
- **D3 — BFF: drop the key param (Decision 2A).**
  `filterForwardHeaders(incoming: Headers): Headers` no longer takes or injects
  a key. Reproduces today's auth-off forwarding behavior; honors INV-3/INV-7.
  The docstring loses its API-key clause.
- **D4 — regenerate, never hand-edit (INV-6).**
  `PYTHONPATH=api python -m app.openapi_export schemas/openapi.json`, then
  `pnpm -C webui run gen:api`.
  `tests/test_openapi.py::test_committed_openapi_matches_live_app` guards the
  server sync; `git diff --exit-code webui/lib/api/schema.d.ts` guards the
  client types.
- **D5 — open-contract tests (Decision 1B).**
  `test_s7_product_surface_matrix.py` becomes the behavioral proof: every
  formerly-gated route, keyless, returns its normal non-401; an `x-api-key`
  header is inert; `openapi.json` has zero `x-api-key`. `test_auth.py` is
  deleted (its subject is gone). `conftest.py` loses the
  `delenv("COSMOS3_API_KEY")` fixture line; because tests no longer read the
  var, removing it must not perturb others — verified by the full CPU suite
  (a named failure-mode to watch).
- **D6 — slim honest note (wording below).** README and SECURITY are restated
  to: no application-layer auth; trusted-LAN/lab assumption; loopback default;
  LAN exposure is an explicit opt-in that puts the root-equivalent
  socket-backed API on the network. Kept minimal; the broad restructure is
  UX-S4.

## Proposed README/SECURITY wording (for spec-review)

`README.md:81` (quickstart comment):

```
cp .env.example .env      # edit for LAN binding or custom model paths
```

`README.md` posture bullets (replacing `:172` and `:188`):

> - **No authentication.** The API has no application-layer auth; it assumes a
>   trusted LAN / lab machine.
> - **Loopback by default.** Published ports bind to `127.0.0.1`. Set
>   `BIND_ADDR=0.0.0.0` to expose on your LAN — an explicit choice that places
>   the (root-equivalent, Docker-socket-backed) API on the network; do this
>   only on a trusted network.

`SECURITY.md:46-49` (replacing the "Authentication is off by default" bullet):

> - **No authentication.** There is no `X-API-Key` or other application-layer
>   gate. Access control is network placement only: ports bind to loopback by
>   default; `BIND_ADDR=0.0.0.0` (LAN exposure) is an explicit operator opt-in.
>   Because the API drives generation through the root-equivalent host Docker
>   socket, treat any network you expose it on as trusted.

## Risks / Trade-offs

- [Removing the only app-layer gate on a socket-mounted API (R-01)] → loopback
  default unchanged (INV-4) + honest docs (D6); mandatory human gate before
  merge.
- [Sweep false-negative if run without `--hidden` (archived R-03)] → sweep MUST
  use `--hidden` and now also `-g '!.git'`; the deterministic check encodes it.
- [conftest fixture removal perturbs unrelated tests] → run the full CPU suite;
  classify any breakage via the Failure Arbiter before touching product code.
- [OpenAPI / `schema.d.ts` not regenerated → CI drift] → explicit regen tasks +
  `test_openapi.py` in the gate + a `schema.d.ts` diff check.
- [`test_errors.py` outside the original radius] → UX-S1-A1 records the
  expansion; no other file needs it (verified by the
  `UnauthorizedError`/`require_api_key` sweep, which hits only auth.py, main.py,
  errors.py, test_auth.py, test_errors.py).

## Migration Plan

Single branch `phase3-session-1`; checkpoint commits per phase; regenerate
artifacts; run full checks; sharded review; adversarial verifier; **stop at the
mandatory human gate (no push/PR/merge)**. Rollback = revert the branch commits;
the auth code is self-contained, so revert is clean.

## Open Questions

None blocking. The exact README/SECURITY wording above is subject to your
spec-review.
