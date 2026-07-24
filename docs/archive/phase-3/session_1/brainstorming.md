# UX-S1 Brainstorming — Remove API-Key Authentication

Date: 2026-07-15
Session: UX-S1 (high risk)
Inputs: `docs/prd.md`, `docs/project_contract.md`, `docs/session_1.md`,
`docs/session_1_contract.yaml`, `docs/evidence_map.md` (E-01..E-03, E-14),
`docs/risk_register.md` (R-01, R-02).

## Context explored

- **Baseline green before edits:** CPU suite `486 passed`; WebUI
  `build ✓ / lint ✓ / typecheck ✓` and `209` vitest tests pass. This is the
  clean pre-edit reference.
- **Auth is cleanly compartmentalized (E-01):** `require_api_key` in
  `api/app/auth.py`; wired in `api/app/main.py:19,211,215-217,220-226`;
  `UnauthorizedError`→401 in `api/app/errors.py`; BFF injects via
  `webui/lib/proxy.ts:39` reading `webui/lib/proxyFetch.ts:30`.
- **Health/metrics already unauthenticated (E-02):** no `dependencies=auth`;
  untouched by removal.
- **OpenAPI models auth as a header parameter, not a security scheme:** the
  committed `schemas/openapi.json` carries **14 operation-level `x-api-key`
  header parameters (28 lines)** and **no** `securityScheme`. Regenerating from
  code (`api/app/openapi_export.py`, guarded by `tests/test_openapi.py`) drops
  them — nothing to hand-edit.
- **Root-equivalent socket (E-03, R-01):** the API mounts the host Docker
  socket; auth was the only app-layer gate in front of it. This is *why* the
  session is high-risk. The mitigation is the unchanged loopback bind (INV-4) +
  honest docs, never a replacement gate.

## Contract-vs-reality gaps found at baseline → amendment UX-S1-A1

1. `tests/api/test_errors.py` imports `UnauthorizedError` and asserts the 401
   mapping, but was **not** in the blast radius (E-14 omitted it). Deleting the
   symbol breaks it at import. **Approved (Q1a):** add it to the radius; drop
   the import + `test_unauthorized_maps_to_401`.
2. The literal auth sweep is non-zero after removal because it descends into
   `.git/` (immutable commit history) and hits one legitimate `apiKey` mention
   in the self-excluded scanner `tests/test_private_ref_scan.py:12`.
   **Approved:** refine the sweep to exclude `.git/`; record the scanner-doc
   mention as an allowed legitimate reference (file untouched).
3. `.env` is gitignored/untracked (`.gitignore:37`) → no committed change
   there. The tracked config edits are `.env.example` +
   `deploy/docker-compose.base.yml`. A now-inert `COSMOS3_API_KEY` may remain in
   an operator's local `.env`; noted for handoff.

## Approach — a single sound path

Auth removal is a mechanical excision, not a design fork: delete → rewire →
regenerate → rewrite-tests. Per the owner's "keep thin docs honest"
instruction, no invented 2–3 option alternatives for the removal itself. The
genuine design choices are the two below.

## Decision 1 — shape of the "new open contract" tests ✅ Approved: (B)

Guards adversarial case #4 (a re-introduced gate passing unnoticed) and R-02.

- (A) Minimal: one keyless→non-401 test per formerly-gated router +
  health/metrics keyless.
- **(B) Chosen:** rewrite `tests/api/test_s7_product_surface_matrix.py` to
  exercise **every** formerly-gated route keyless and assert non-401; assert a
  supplied `x-api-key` header is **inert** (identical behavior); and add a
  direct assertion that regenerated `openapi.json` contains **zero**
  `x-api-key`. Behavioral proof the gate is gone and cannot silently return.

Trade-off: (B) is a little more test code, but the whole reason this session
routes through an independent test writer is to prove the *open* contract, not
merely delete assertions. (B) pays for itself.

## Decision 2 — BFF handling of a client-supplied `x-api-key` ✅ Approved: (A)

- **(A) Chosen:** drop the `apiKey` parameter from `filterForwardHeaders`
  entirely; a client `x-api-key` passes through untouched and the
  now-indifferent API ignores it. This exactly reproduces **today's
  auth-disabled default** (with `COSMOS3_API_KEY` unset, current code already
  forwards a client `x-api-key` untouched), so it is a true no-op beyond
  dropping the gate (INV-3, INV-7).
- (B) Rejected: actively stripping `x-api-key` is *new* behavior (today it
  passes through when auth is off) → invites an INV-3 "behavior change beyond
  dropping the gate" finding from the adversarial verifier.

## Deferred to design.md

Exact wording of the slim honest README/SECURITY note (content fixed by the
contract: no-auth; trusted-LAN assumption; loopback default; LAN opt-in;
root-equivalent socket). The broad README restructure is **UX-S4**, not here
(S1/S4 boundary).
