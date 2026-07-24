# UX-S1 Sharded Review

Date: 2026-07-15
Risk: high → sharded review over the contract axes (correctness, security, tests,
architecture, performance), five independent **read-only** reviewers. Diff under
review: `git diff 2c29d75..HEAD` (commits `e591ae9`, `c1db13a`, `04a39b6`, `6963c10`).

## Verdict by axis

| Axis | Result |
|---|---|
| Correctness | NO FINDINGS — all four routers rewired without the dependency; error table coherent minus the 401 row; no leftover symbols; `/v1/reason` probe non-vacuous (422). Reviewer ran 47 targeted tests. |
| Security | NO FINDINGS — INV-4 loopback default intact (adversarial #6 cleared); no replacement auth / no new capability (INV-3); BFF has no spoofing seam (Decision 2A safe, adversarial #5); NFR-1 clean (`.env` untracked); README/SECURITY posture honest. |
| Tests | 1 MEDIUM + 1 LOW (below) — **fixed**. |
| Architecture | NO FINDINGS — blast radius matches `allowed_files` + `test_errors.py` (UX-S1-A1); clean excision (no stub/dead code/orphan imports); `openapi.json`/`schema.d.ts` genuinely regenerated (pure `x-api-key` removal); BFF signature change propagated to its sole caller. |
| Performance | NO FINDINGS — purely subtractive (one fewer per-request dependency; one fewer header `set`); middleware/router order unchanged. |

## Findings & resolutions

### F1 — MEDIUM (tests): runtime open-contract tests overclaimed; the real reintroduction guard is the OpenAPI test
Evidence (empirical probe by the reviewer): the removed `require_api_key` gate only
returned 401 when `COSMOS3_API_KEY` was **set**; every runtime open-contract test runs
with the key **unset**, so re-attaching the exact gate leaves `jobs=202, gen=202,
action=422, reason=422` — the runtime assertions still pass. Their docstrings ("proving
there is no auth gate in front") therefore overstated what they verify. The genuine
reintroduction guard is `test_openapi_has_no_auth_surface` +
`tests/test_openapi.py::test_committed_openapi_matches_live_app`, which fail when the
`Header`-based dependency re-adds the `x-api-key` parameter to the schema.

Violated clause: R-10 / R-02 / adversarial case #4 (removal proven by tests that would
fail if a gate returned). The removal **is** proven — by the schema tests — but the
runtime docstrings were misleading.

**Resolution (fixed in `tests/api/test_s7_product_surface_matrix.py`):** corrected the
docstrings so the runtime tests state they document the *shipped open behavior*, and
named `test_openapi_has_no_auth_surface` (+ `tests/test_openapi.py`) as the explicit
reintroduction guard. Deliberately did **not** add a runtime test that sets
`COSMOS3_API_KEY`: that would reintroduce the very token FR-1/`EV-UX-AUTH-SWEEP-CLEAN`
requires removed. The clean-sweep MUST takes priority; the schema guard already satisfies
"prove the removal" for the removed mechanism, and `auth.py` deletion + the sweep prove
the env-var path is gone.

### F2 — LOW (tests): weak `!= 401` assertions
`test_formerly_gated_routers_open_without_key` used `!= 401` for the action/reason probes
(satisfied by 422 *or* 500). **Resolution:** tightened both to `== 422` (the confirmed
normal validation result), pinning the "route's normal result" clause.

## Dedup / consensus notes
- F1 was raised by one reviewer (tests) but carries **strong, reproduced evidence**, so it
  is actioned per the protocol ("do not require consensus … with concrete evidence"; Medium
  needs 2+ reviewers **or** strong evidence).
- Security and correctness reviewers independently confirmed the OpenAPI + `auth.py`
  deletion + sweep as the removal proof, consistent with F1's resolution.
- Housekeeping: the tests reviewer created scratch `reintro_probe*.py` files outside the
  repo tree; confirmed none are tracked or present under the repo.

## Post-fix re-check
- `uv run pytest -m "not gpu"` → **486 passed**.
- `tests/api/test_s7_product_surface_matrix.py` → 16 passed.
- Code/config/test auth sweep (excl. docs pack prose, `.git`, scanner) → **ZERO**.
- `ruff check api tests` → clean.
