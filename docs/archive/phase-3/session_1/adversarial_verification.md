# UX-S1 Adversarial Verification

Date: 2026-07-15
Verifier: fresh-context agent — did not write the code or participate in the sharded
review; saw only the session contract, project contract, risk register (incl.
UX-S1-A1), and the diff (`2c29d75..HEAD`); ran every deterministic check itself.

## Verdict: **PASS** (deterministic axis) — the mandatory human gate remains OPEN

## Falsification attempts — all failed (the completion claim survived)

| Adversarial case | Result | Evidence |
|---|---|---|
| (a) Leftover `Depends`/gate on a router | Disproven | `rg "dependencies=\|Security\(\|Depends\("` over `api/app/` → no matches; all four routers included with no `dependencies=`; `auth.py` deleted; `require_api_key`/`UnauthorizedError` unreferenced. |
| (b) Sweep passes only by hiding `.env`/`.git` | Disproven | Prescribed `--hidden` sweep: all matches in `docs/**` prose except the one self-excluded scanner comment `tests/test_private_ref_scan.py:12`. `.env.example` confirmed clean of `COSMOS3_API_KEY`; `.env` gitignored/untracked. |
| (c) `openapi.json` hand-edited, not regenerated | Disproven (strong) | `python -m app.openapi_export /tmp/x.json` → **byte-identical** to committed `schemas/openapi.json`; diff vs pre-session = **0 additions / 242 deletions** (pure `x-api-key` param removal, INV-6); `tests/test_openapi.py` passes. |
| (d) Open contract asserted only by deletions | Disproven | Positive tests pass and would flip to failure if a gate returned (schema guard). |
| (e) Residual `x-api-key` spoofing seam in BFF | Disproven | Live probe: `POST` with `x-api-key: attacker` → 202, identical to keyless; header inert (no gate to spoof); INV-7 intact. |
| (f) Health/metrics behavior drift | Disproven | Live: `/v1/health/{live,ready}` → 200, `/v1/metrics` → 200, all keyless (INV-2); metrics still `include_in_schema=False`. |
| #6 BIND_ADDR flipped to 0.0.0.0 | Disproven | `.env.example` `BIND_ADDR=127.0.0.1`; compose `${BIND_ADDR:-127.0.0.1}` both services (INV-4). |

## Independent check results
- CPU suite (`pytest -m "not gpu"`): **486 passed, 0 failed**.
- WebUI: `build` OK, `lint` exit 0, `typecheck` exit 0, `test` **208 passed (39 files)** (proxy tests 9).
- OpenAPI regen: byte-identical to committed; 0 `x-api-key`/`securitySchemes`/`security`.
- `webui/lib/api/schema.d.ts`: `pnpm gen:api` byte-identical to committed; 0 `x-api-key`.
- Blast radius: all 30 changed files ∈ `allowed_files`, deletions, or the UX-S1-A1-sanctioned `tests/api/test_errors.py`; no forbidden file; working tree clean.

## UX-S1-A1 assessment
**Legitimate, not a cover for a defect.** `tests/api/test_errors.py` genuinely imported
`UnauthorizedError` and would break at collection once `auth.py` was deleted; the fix is
present and its 8 tests pass. The `-g '!.git'` refinement and the single documented
scanner-comment allowance are honest and mask no live auth code.

## Disproven / Unsupported claims / Strongest counterexample
- Disproven claims: **none**.
- Unsupported claims: **none** (every done-claim element backed by command/code evidence).
- Strongest counterexample: **none** (the only residual, `test_private_ref_scan.py:12`, is a
  pre-disclosed inert scanner comment).

## Caveat (explicitly outside verifier scope)
The contract `done_condition` also requires the **mandatory pre-merge human decision gate**
(security-posture change: removing the only app-layer control in front of a root-equivalent
socket-mounted API). That owner sign-off is a process step not verifiable from the repo and
remains **OPEN**. No push / PR / merge was performed.
