# UX-S1 Plan — Remove API-Key Authentication (executable, TDD)

Conventions: `uv run` ≡ `uv run --frozen --group dev --group test-cpu`. WebUI
commands via `pnpm -C webui`. Commit at each **⎇** checkpoint with the
`Co-Authored-By` trailer; **no push / PR / merge** (stop at the human gate).

Honest note on TDD for a *removal*: auth is disabled-by-default today
(`COSMOS3_API_KEY` unset), so keyless requests already return non-401 — those
assertions are green before and after. The genuine red→green anchor is
**`test_openapi_has_no_api_key`** (the live app's OpenAPI carries `x-api-key`
now; it must not after the dependency is dropped) and the **WebUI proxy** tests
(injection → no injection). Pure deletions (auth.py, the 401 row, config) are
guarded by the full suite staying green + the clean sweep, not by a red test.

---

## Commit 0 — refining pack + amendment UX-S1-A1
- Files already written: `docs/session_1/{brainstorming,proposal,design,tasks,plan,execution_contract}.md`, `specs/api-access-control.md`.
- Add UX-S1-A1 row to `docs/risk_register.md`; extend `docs/evidence_map.md` E-14 to list `tests/api/test_errors.py`.
- **⎇ `docs(ux-s1): refining pack + UX-S1-A1 amendment`**

## Task 2 — API auth removal (TDD anchor)
**2a (RED).** In `tests/api/test_s7_product_surface_matrix.py`: delete line 65
`monkeypatch.delenv("COSMOS3_API_KEY", raising=False)`; append:
```python
# --- open access: no API-key gate remains on the formerly-protected routers (UX-S1) ---

def test_formerly_gated_routers_open_without_key(make_matrix_app):
    """Each formerly-gated router returns a normal non-401 result with no X-API-Key."""
    with TestClient(make_matrix_app()) as client:
        assert client.post("/v1/jobs", json={"mode": "t2i", "params": {"prompt": "x"}}).status_code == 202
        assert client.post("/v1/generation/t2v", json={"prompt": "x"}).status_code == 202
        # action + reasoning: even an invalid body validates (non-401), proving no auth gate.
        assert client.post("/v1/action/forward_dynamics", json={}).status_code != 401
        assert client.post("/v1/reason", json={}).status_code != 401  # confirm path in 2a


def test_supplied_x_api_key_is_inert(make_matrix_app):
    """A client-supplied X-API-Key changes nothing — the header is ignored, not a gate."""
    with TestClient(make_matrix_app()) as client:
        without = client.post("/v1/generation/t2v", json={"prompt": "x"})
        withkey = client.post("/v1/generation/t2v", json={"prompt": "x"}, headers={"X-API-Key": "anything"})
    assert without.status_code == withkey.status_code == 202


def test_openapi_has_no_api_key(make_matrix_app):
    """The live app's OpenAPI carries no x-api-key parameter and no auth security scheme."""
    with TestClient(make_matrix_app()) as client:
        spec_text = client.get("/openapi.json").text
        spec = client.get("/openapi.json").json()
    assert "x-api-key" not in spec_text.lower()
    assert "securitySchemes" not in (spec.get("components") or {})
```
Before writing, confirm the reasoning route path from `api/app/routes/reasoning.py`
/ `build_reasoning_router` (expected `/v1/reason`); if different, use the real
path so the `!= 401` probe is not vacuous (a 404 would falsely pass).
Run `uv run pytest tests/api/test_s7_product_surface_matrix.py::test_openapi_has_no_api_key`
→ **RED**.

**2b (GREEN).** Remove the dependency:
- `api/app/main.py`: line 17 `from fastapi import Depends, FastAPI` → `from fastapi import FastAPI`; delete line 19 `from app.auth import require_api_key`; delete line 211 `auth = [Depends(require_api_key)]`; drop `, dependencies=auth` from the jobs/generation/action includes (215-217) and the `dependencies=auth,` line in the reasoning include (225).
- `api/app/errors.py`: delete line 10 import; delete the `UnauthorizedError`→401 branch (55-56); delete `UnauthorizedError,` from the registration tuple (78).
- `git rm api/app/auth.py`.
Run the anchor test → **GREEN**.

**2c.** `tests/api/test_errors.py`: delete line 4 `from app.auth import UnauthorizedError` and `test_unauthorized_maps_to_401` (69-71).

Targeted check:
`uv run pytest tests/api/test_errors.py tests/api/test_s7_product_surface_matrix.py`
- **⎇ `refactor(ux-s1): remove X-API-Key dependency, handler, and auth.py`**

## Task 3 — Config
- `.env.example`: delete the `COSMOS3_API_KEY=` line + its two continuation comment lines (10-12); keep `BIND_ADDR=127.0.0.1` (13).
- `deploy/docker-compose.base.yml`: delete both `COSMOS3_API_KEY: ${COSMOS3_API_KEY:-}` lines (13, 31); reword the loopback comment (15) to drop the "auth is off when …" clause, keeping "Loopback by default; set BIND_ADDR=0.0.0.0 for LAN."
- **⎇ `chore(ux-s1): drop COSMOS3_API_KEY from .env.example + compose`**

## Task 4 — WebUI BFF (TDD)
**4a (RED).** `webui/lib/proxy.test.ts`: rewrite the `filterForwardHeaders` block:
```ts
describe("filterForwardHeaders", () => {
  it("strips hop-by-hop + host and injects no api key", () => {
    const incoming = new Headers({
      host: "webui:3000", connection: "keep-alive", "content-length": "42",
      "content-type": "application/json", "x-request-id": "abc",
    });
    const out = filterForwardHeaders(incoming);
    expect(out.get("host")).toBeNull();
    expect(out.get("connection")).toBeNull();
    expect(out.get("content-length")).toBeNull();
    expect(out.get("content-type")).toBe("application/json");
    expect(out.get("x-request-id")).toBe("abc");
    expect(out.get("x-api-key")).toBeNull();      // auth removed: proxy injects nothing
    expect(out.get("authorization")).toBeNull();
  });

  it("forwards a client-supplied x-api-key untouched (inert; the API ignores it)", () => {
    // Decision 2A / INV-3: no new stripping — a leftover header passes through like any other.
    const out = filterForwardHeaders(new Headers({ "x-api-key": "whatever" }));
    expect(out.get("x-api-key")).toBe("whatever");
  });
});
```
`webui/lib/proxyFetch.test.ts`: remove the `COSMOS3_API_KEY` env dance (lines 6, 11, 14-15) and replace the "injects COSMOS3_API_KEY" test (34-50) with:
```ts
  it("forwards to the internal api without injecting an api key", async () => {
    let captured: RequestInit | undefined;
    const fetchImpl = vi.fn((_url: string, init?: RequestInit) => {
      captured = init;
      return Promise.resolve(new Response("{}", { status: 200 }));
    });
    await forward(new Request("http://webui/api/v1/jobs"), ["v1", "jobs"], fetchImpl as unknown as typeof fetch);
    const sent = new Headers(captured?.headers);
    expect(sent.get("x-api-key")).toBeNull();
  });
```
`pnpm -C webui run test` → **RED** (old impl injects / old signature).

**4b (GREEN).**
- `webui/lib/proxy.ts`: signature → `filterForwardHeaders(incoming: Headers): Headers`; delete line 39 `if (apiKey) out.set("x-api-key", apiKey);`; trim the API-key clause from the docstring (28-33).
- `webui/lib/proxyFetch.ts`: line 30 → `const headers = filterForwardHeaders(req.headers);`.
`pnpm -C webui run test` → **GREEN**.
- **⎇ `refactor(ux-s1): BFF stops injecting X-API-Key`**

## Task 5 — Regenerate artifacts (never hand-edited)
- `PYTHONPATH=api uv run python -m app.openapi_export schemas/openapi.json`
- `pnpm -C webui run gen:api` → `git diff --exit-code webui/lib/api/schema.d.ts` (expect clean; the removed params are the only delta and openapi.json already carries them out).
- `uv run pytest tests/test_openapi.py` → **GREEN**; `rg -c -i x-api-key schemas/openapi.json` → 0.
- **⎇ `chore(ux-s1): regenerate openapi.json + client types (no x-api-key)`**

## Task 6 — Remaining test rewrites
- `git rm tests/api/test_auth.py`.
- `tests/api/test_jobs_api.py`: in `_client`, drop the `api_key` param + the `if api_key … else …` env block (57, 61-64), leaving no `COSMOS3_API_KEY` reference; delete `test_auth_enforced_with_health_and_openapi_exempt` (234-240) and replace with:
```python
def test_jobs_open_without_key_health_and_openapi_exempt(tmp_path, monkeypatch):
    with _client(tmp_path, monkeypatch) as client:
        assert client.post("/v1/jobs", json={"mode": "t2i", "params": {}}).status_code == 202  # open, not 401
        assert client.get("/v1/health/ready").status_code in (200, 503)
        r = client.get("/openapi.json")
        assert r.status_code == 200 and "x-api-key" not in r.text.lower()
```
  Remove the two stray `monkeypatch.delenv("COSMOS3_API_KEY", …)` lines (211, 275); relabel the `# ---- auth (RK-17) ----` comment (205) to `# ---- submit-side validation hygiene ----`.
- `tests/api/test_sse.py`: remove the `delenv("COSMOS3_API_KEY")` lines (39, 78).
- `tests/api/conftest.py`: remove the `delenv("COSMOS3_API_KEY")` line (39).
- `tests/test_metrics_endpoint.py`: rewrite `test_metrics_endpoint_needs_no_api_key` (31-38) →
```python
def test_metrics_and_gated_route_open_without_key():
    client = _client()
    # a formerly-protected route now responds without any key (not 401) ...
    assert client.post("/v1/jobs", json={"mode": "t2v", "params": {"prompt": "x"}}).status_code == 202
    # ... and /v1/metrics is reachable too (private-net scraper)
    assert client.get("/v1/metrics").status_code == 200
```
- Targeted: `uv run pytest tests/api tests/test_metrics_endpoint.py`.
- **⎇ `test(ux-s1): assert the open contract; drop auth-specific tests`**

## Task 7 — Docs (auth-specific lines only, design D6 wording)
- `README.md` `:81,:172,:188` → the D6 wording. `SECURITY.md` `:46-49` → the D6 bullet.
- Verify no dangling auth prose: `rg -n "COSMOS3_API_KEY|X-API-Key" README.md SECURITY.md` → none.
- **⎇ `docs(ux-s1): slim honest no-auth / trusted-LAN note (README + SECURITY)`**

## Task 8 — Full verification
- Refined sweep: `rg --hidden -n "COSMOS3_API_KEY|X-API-Key|x_api_key|api_key|apiKey|require_api_key|UnauthorizedError" -g '!docs/archive/**' -g '!.git'` → only `docs/**` pack prose + the one `tests/test_private_ref_scan.py:12` scanner-doc mention remain (documented as allowed); zero code/config/test hits.
- `uv run pytest -m "not gpu"` → green.
- `pnpm -C webui run build && pnpm -C webui run lint && pnpm -C webui run typecheck && pnpm -C webui run test` → green.
- `uv run pytest tests/test_openapi.py` → green; `schema.d.ts` diff clean.

## Task 9 — Review, verify, handoff
- Sharded review (correctness/security/tests/architecture/performance) → fix High/Critical → re-check.
- Adversarial verifier vs the done condition → Failure Arbiter on any fail.
- `docs/handoff.md` + eval seeds; **stop at the mandatory human gate**.
- **⎇ `docs(ux-s1): sharded review + adversarial verification + handoff`**
