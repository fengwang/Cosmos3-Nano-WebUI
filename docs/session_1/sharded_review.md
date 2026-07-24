# LX-S1 Review — 6 axes

Date: 2026-07-24 · Routing: single_agent → one review (low risk). One independent, read-only
reviewer over the diff against `docs/session_1_contract.yaml` (axes, adversarial cases, failure
modes), corroborated by the implementer's own pass. Deterministic checks were re-run by the
reviewer.

## Diff reviewed
`api/app/main.py` (env fallback 600→1800 + comment), `api/orchestrator/manager.py` (ctor default
600.0→1800.0), `.env.example` (idle keep-warm section), `tests/test_idle_keepwarm_default.py`
(new), `docs/evidence_map.md` (LX-S1 audit), `docs/archive/phase-3/session_4/plan.md` (authorized
one-line path scrub). No forbidden file touched.

## Findings by axis

| Axis | Result | Notes |
|---|---|---|
| Correctness | **Clean** | Both sources of truth = 1800 (`main.py:175`, `manager.py:46`); env override path intact. No drift (R-02/E-06). |
| Security / safety | **Clean** | Archive scrub uses the single char U+2026 (`e2 80 a6`, hexdump-confirmed), which the `workspace_path` regex `/workspace/[A-Za-z0-9._/-]+` correctly skips; `...` would NOT have fixed the leak. Scan → 0 findings. Edit minimal; no narrative rewritten. |
| Tests | **Clean** | Asserts the app-wired value via `create_app().state.orchestrator._inner._idle_timeout` (not a literal); default/override/zero/constructor + behavioral 0-schedules-no-timer all present. `create_app()` verified CPU-safe (factory passed by reference, invoked only in `acquire()`). |
| Architecture / maintainability | **Clean** | `notify_idle`/`acquire`/`_cancel_idle_timer` byte-for-byte unchanged → notify_idle contract + INV-4 preserved. `.env.example` consistent with code default. Audit refs accurate. |
| Performance | **Clean** | No hot-path change; only the idle-eviction delay (10→30 min). |
| Readability | **Clean** | Added comment clear and correct. One Nit ("warm 30 min" beside an overridable value) — no action; the next clause states the override. |

## Adversarial cases / failure modes — all pass
- R-02/E-06 drift → both sources 1800; the only other `600` tokens are the test comment and an unrelated `metrics.py` Prometheus bucket.
- R-01 wrong knob → only the idle knob changed; `gen_client.py` / `work.py` / `reasoning.py` / `openapi.json` show no diff (INV-3).
- INV-2 hard-code → env override + `0` both work, both covered by tests.
- R-05 README → `git diff README.md` empty (untouched).
- App-wired vs literal → satisfied.
- Stale-600 test → none; existing orchestrator tests pass `idle_timeout=` explicitly.
- CPU suite green incl. scrubbed archive → pass, private-ref scan clean.

## Outcome
No Critical/High/Medium findings. One Nit, no change required. **Verdict: GATE-LX-S1-TIMEOUT
satisfied by the diff.** Process note (not a gate blocker): the change is currently uncommitted;
it must be committed to land.
