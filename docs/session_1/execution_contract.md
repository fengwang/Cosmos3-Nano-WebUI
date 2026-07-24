# LX-S1 Execution Contract

Date: 2026-07-24 · Gate: `GATE-LX-S1-TIMEOUT` · Risk: low · Routing: single_agent

Derived from `docs/session_1_contract.yaml` and `docs/session_1/refining.md`. This contract binds
the execution: it enumerates exactly what changes, the (extended) blast radius, the TDD entry
point, the per-task checks, the end-of-session review axes, the adversarial brief, and the
concrete done condition.

---

## 1. Planned file changes

| File | Change | Requirement |
|---|---|---|
| `api/app/main.py` | line 173 env fallback `"600" → "1800"` | FR-1/FR-2 |
| `api/orchestrator/manager.py` | line 46 `idle_timeout: float = 600.0 → 1800.0` | FR-1 (anti-drift, E-06/R-02) |
| `.env.example` | add a section with `COSMOS3_IDLE_TIMEOUT_SECONDS=1800` + one-line comment | FR-3 |
| `tests/test_idle_keepwarm_default.py` (new) | spec-derived CPU test: app-wired 1800, override, `0`, constructor default | FR-2 |
| `docs/evidence_map.md` | append the LX-S1 execution audit (gen/cold-start ≥30 min, unchanged) | FR-4 |
| `docs/session_1/**` | this pack + review/adversarial/handoff-adjacent working docs | process |
| `docs/risk_register.md` | close-out note (R-02 discharged; residuals) | process |
| `docs/eval_seed_cases.md` / `docs/eval_corpus/**` | eval seeds | process |
| `docs/handoff.md` (new) | LX-S2 handoff | process |
| **`docs/archive/phase-3/session_4/plan.md`** | **authorized exception** — scrub line 9 leaked path | see §2.1 |

Explicitly **not** changed: `README.md`; `api/jobs/gen_client.py`; `api/engines/vllm_omni/work.py`;
`api/app/routes/reasoning.py`; `schemas/openapi.json`; any `webui/**` or `deploy/**`; and
`api/app/main.py:177` (`COSMOS3_PLANE_READY_TIMEOUT`, audit-only).

## 2. Allowed blast radius

As `docs/session_1_contract.yaml → blast_radius.allowed_files`:
`api/app/main.py`, `api/orchestrator/manager.py`, `.env.example`, `tests/**`,
`docs/session_1/**`, `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
`docs/handoff.md`. Forbidden as listed (README, other `api/**`, `webui/**`, `deploy/**`, schemas,
other-timeout files, `docs/archive/**`, weights/media).

### 2.1 Authorized exception (owner-approved, 2026-07-24)

`docs/archive/phase-3/session_4/plan.md` is normally forbidden (`docs/archive/**` boundary,
Hard Commitment 9). The baseline `uv run pytest -m "not gpu"` has one **pre-existing** failure:
`tests/test_private_ref_scan.py::test_clean_tree_has_no_findings` flags a leaked checkout path
`/workspace/…` at that file's line 9 (a genuine INV-1 hygiene leak the `workspace_path` rule was
added to catch, MIG-S8). The owner authorized a **single-file, single-line** exception to scrub
it to the sanctioned ellipsis form (`/workspace/…`, which the scanner skips by design — see
`test_workspace_ellipsis_form_not_flagged`).

Bounded so the archive boundary's intent is preserved:
- Only line 9's absolute path is edited; **no** archived decision, narrative, or history is
  rewritten.
- Consistent with existing repo practice (sibling docs already name this path class with the
  ellipsis form) and with precedent (`db5d615` "extend blast radius to fix").
- Rationale recorded here and in the handoff so the deviation is explicit, not latent.

## 3. First test to write (TDD entry point — RED before GREEN)

`tests/test_idle_keepwarm_default.py::test_app_wires_idle_keepwarm_default_1800`:

```python
def test_app_wires_idle_keepwarm_default_1800(monkeypatch):
    monkeypatch.delenv("COSMOS3_IDLE_TIMEOUT_SECONDS", raising=False)
    app = create_app()  # no injected orchestrator → real env→wire path
    assert app.state.orchestrator._inner._idle_timeout == 1800.0
```

It MUST fail on the current tree (wired value is `600.0`) before either constant is edited —
proving the test pins the **app-wired** value, not a literal (defeats the contract's adversarial
"asserts the constant" case). Companions in the same module: override (`=900`), zero (`=0`),
constructor default (`Orchestrator(stub)` → `1800.0`), and a behavioral `0`-schedules-no-timer
assertion.

## 4. Checks to run after each task

- After the test is written: `uv run pytest tests/test_idle_keepwarm_default.py -q` → **RED**.
- After the code change: the same file → **GREEN**; then
  `uv run pytest tests/api/test_orchestrator_stub.py -q` (no regression in existing idle tests).
- After `.env.example`: `rg -n "COSMOS3_IDLE_TIMEOUT_SECONDS" api/app/main.py .env.example`
  (both show 1800) and `rg -n "idle_timeout" api/orchestrator/manager.py` (default `1800.0`).
- After the archive scrub: `uv run python tests/test_private_ref_scan.py` (0 findings).
- End of session (full): `uv run pytest -m "not gpu"` **green**; `git status`/`git diff --stat`
  confirms `README.md` and all forbidden files untouched.

## 5. Review axes to run at the end (contract `review_axes`)

correctness · security · tests · architecture · performance · readability. Low risk → a focused
review (self + one read-only subagent pass) rather than a full six-agent shard; fix
**High/Critical** only; record to `docs/session_1/sharded_review.md`.

## 6. Adversarial verifier brief

Fresh context; sees only the contract, the diff, and the evidence (not this conversation). Try to
**falsify** `GATE-LX-S1-TIMEOUT`. Specifically probe the contract's adversarial cases:
1. Was only `main.py` changed, leaving `manager.py` at `600.0` (drift)?
2. Was a *generation* timeout changed instead of idle keep-warm (wrong knob, R-01)?
3. Is the default hard-coded so the env override or `0`-disables no longer works (INV-2)?
4. Was `README.md` edited (R-05)?
5. Does the test assert a literal constant rather than the app-wired value?
6. Did any other timeout / schema / route change (INV-3)?
7. Is the CPU suite actually green (including the scrubbed archive)?

Record to `docs/session_1/adversarial_verification.md`.

## 7. Concrete done condition

`GATE-LX-S1-TIMEOUT` passes:
- `COSMOS3_IDLE_TIMEOUT_SECONDS` defaults to `1800` at `api/app/main.py:173` **and**
  `api/orchestrator/manager.py:46`.
- The new CPU test proves the app wires `1800` with no env, honors an override, and treats `0` as
  disabled; existing idle tests still pass.
- `.env.example` documents the knob consistent with the code default.
- The gen/cold-start audit is recorded in `docs/evidence_map.md`; no other timeout, schema, or
  route changed.
- `uv run pytest -m "not gpu"` is green (the pre-existing archive leak scrubbed under §2.1).
- `README.md` is untouched.
- Handoff + eval seeds written; residual notes (WebUI SSE heartbeat E-08/R-03; future
  single-source-of-truth cleanup) recorded.
