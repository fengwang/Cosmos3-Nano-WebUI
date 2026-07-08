# Specification - BFF Auth Header Alignment (X-1)

Session: MIG-S7
Capability: bff-auth-header

## ADDED Requirements

### Requirement: WebUI forwards the API key on the header the API enforces

The WebUI BFF proxy MUST forward the server-side API key to the internal API on the
`X-API-Key` header — the header the API enforces (`api/app/auth.py`). It MUST NOT rely on
the `Authorization: Bearer` scheme, which the API does not check. The API's request shape
MUST NOT change (`INV-9`): the fix is confined to the WebUI client.

#### Scenario: Key is forwarded as X-API-Key

WHEN `filterForwardHeaders(incoming, "secret")` is called
THEN the returned headers SHALL contain `x-api-key: secret`
AND SHALL NOT contain an injected `authorization: Bearer secret` header.

#### Scenario: No key configured means no injected auth header

WHEN `filterForwardHeaders(incoming)` is called with no API key
THEN the returned headers SHALL NOT contain an injected `x-api-key` header.

#### Scenario: End-to-end forward sets X-API-Key

WHEN `forward(req, segments, fetchImpl)` runs with `COSMOS3_API_KEY` set
THEN the request sent upstream SHALL carry `x-api-key: <key>`
AND the key SHALL NOT appear in any header or body returned to the caller.

### Requirement: The server-injected key cannot be spoofed by the client

Because the browser never holds the key and the proxy injects it server-side, a
client-supplied `X-API-Key` header MUST NOT override the server-injected value.

#### Scenario: Client-supplied X-API-Key is overwritten

WHEN incoming request headers already contain an `x-api-key` value and a server key is
configured
THEN `filterForwardHeaders` SHALL emit the server key value on `x-api-key`, overwriting
the client-supplied one.

### Requirement: Existing proxy guarantees are preserved

The header change MUST NOT regress the proxy's other behaviors: hop-by-hop and `host`
header stripping on the request, `content-encoding` stripping and `x-accel-buffering: no`
on the response, SSE pass-through, and the masked `502` on an unreachable upstream.

#### Scenario: WebUI test suite passes

WHEN `pnpm test` runs in `webui/`
THEN the `proxy` and `proxyFetch` suites SHALL pass, including the updated header
assertions
AND `pnpm lint` and `pnpm typecheck` SHALL pass.
