# LX-S1 Refining Pack — Idle Keep-Warm 10 min → 30 min

Date: 2026-07-24
Session: `LX-S1` · Risk: low · Routing: single_agent
Sources: `docs/prd.md` (FR-1..FR-5), `docs/session_1.md`, `docs/session_1_contract.yaml`,
`docs/project_contract.md` (INV-2/3/4, Gate `GATE-LX-S1-TIMEOUT`), `docs/evidence_map.md`
(E-01..E-08).

This is a **proportionate** consolidation of the brainstorming → proposal → design →
specification phases into one document (owner decision, 2026-07-24), because the change is a
low-risk edit to two aligned constants plus a spec-derived test and two doc updates, and the
underlying spec (`session_1.md` + the contract) is already precise. Nothing here relaxes the
contract; where this doc and the contract disagree, the contract wins.

---

## 1. Confirmed intent

- **Outcome:** ship `COSMOS3_IDLE_TIMEOUT_SECONDS` default `600 → 1800` at both sources of
  truth, surface the knob in `.env.example`, prove the app-wired default with a CPU test, and
  record the generation/cold-start audit — without touching `README.md`.
- **User / why now:** a single-RTX-5090 operator whose normal *generate → watch → think →
  tweak* loop is punished by a 10-min idle eviction that forces a full cold reload (E-01/E-02,
  PRD §1.1).
- **Success:** `GATE-LX-S1-TIMEOUT` passes; the CPU suite is genuinely green; an adversarial
  pass cannot falsify the done condition.
- **Constraint:** stay inside the `LX-S1` blast radius **plus one authorized exception** (scrub
  a pre-existing leaked path in `docs/archive/phase-3/session_4/plan.md` — see the execution
  contract); change no other timeout; keep INV-2/3/4 intact.
- **Out of scope:** `README.md` (LX-S2 owns it, R-05), every other timeout, the WebUI SSE
  heartbeat (E-08/R-03), GPU smoke, and any change to `notify_idle` semantics or the eviction
  mechanism.

---

## 2. Brainstorming (condensed)

### Problem framing
The originating request ("raise the video-generation timeout 10→30 min") targets a limit that
does not exist at 10 min: generation is already bounded at 2400 s / 7200 s and cold start at
1800 s (E-03/E-04). The only 10-min default in the tracked tree is the **idle keep-warm**
timeout (E-01). So the real move is to raise idle keep-warm and *audit* the rest.

### Approaches considered
| # | Approach | Verdict |
|---|---|---|
| A | Change only `api/app/main.py:173` env fallback `"600"→"1800"`. | **Rejected.** The `Orchestrator` constructor default stays `600.0`; a directly-constructed orchestrator (tests, future callers) silently keeps 10 min (E-06, R-02 drift). |
| B | Change **both** the `main.py` env fallback and the `Orchestrator` constructor default, and pin the **app-wired** value with a CPU test. | **Chosen.** Removes the two-source drift and proves the wiring, not just a literal (guards the adversarial "asserts the constant" trap). |
| C | Collapse the two definitions into one source of truth (e.g. a module constant imported by both). | **Rejected for this session.** A refactor of the constructor signature/wiring is out of scope, higher-risk, and unnecessary — aligning both values + a wiring test achieves the anti-drift goal within the contract's minimal blast radius. Noted as a possible future cleanup. |

### `.env.example` surfacing
Model it on the existing "Generation engine wiring (these defaults match the code; shown for
clarity)" block — an active `KEY=value` line whose value equals the code default, with a short
comment. This keeps "default settings = the code default" true (copying `.env.example` to `.env`
changes nothing) while making the knob discoverable (E-07, PRD Decision 4).

---

## 3. Proposal

### Motivation
Serve the intended single-GPU iteration loop by keeping the resident generation plane warm for
30 min instead of 10, so a normal think-and-tweak pause no longer costs a cold reload — while
leaving generation-duration and cold-start ceilings (already ≥30 min) untouched.

### Specific changes (agreed)
1. `api/app/main.py:173`: env fallback `"600" → "1800"`.
2. `api/orchestrator/manager.py:46`: `idle_timeout: float = 600.0 → 1800.0`.
3. `.env.example`: add `COSMOS3_IDLE_TIMEOUT_SECONDS=1800` with a one-line comment.
4. `tests/test_idle_keepwarm_default.py` (new): spec-derived CPU test (app-wired 1800; override;
   `0`; constructor default).
5. `docs/evidence_map.md`: append an LX-S1 execution audit (gen/cold-start ceilings ≥30 min,
   unchanged; idle raised at both sources).

### Capabilities
- **New capability:** none.
- **Modified capability:** `idle-keep-warm-default` — the *shipped default value* of the existing
  idle keep-warm eviction behavior changes (600 s → 1800 s) at both definitions. The mechanism,
  the override contract, and the `0`-disables semantics are unchanged.

### Impact
- Behavioral: an idle resident plane is now evicted after 30 min instead of 10. No schema, route,
  or other-timeout change (INV-3). No GPU work.
- Code touched: `api/app/main.py`, `api/orchestrator/manager.py` only.
- Tests: one new CPU module. Existing idle tests pass unchanged — they all pass explicit
  `idle_timeout=` values and never rely on the `600.0` default (verified:
  `tests/api/test_orchestrator_stub.py`, `tests/test_integ_swap_*`).
- Docs: `.env.example`, `docs/evidence_map.md`; session working docs under `docs/session_1/`.

---

## 4. Design

### Context
`idle_timeout` is plain data threaded from operator env at the app shell (`create_app`, an
Action) into the pure-ish `Orchestrator` FSM. Production always passes the env-derived value;
the constructor default only bites when the orchestrator is built without the argument. The two
defaults must agree so neither path drifts (E-06).

### Goals / Non-Goals
- **Goals:** one true shipped default (1800) at both definitions; a test that fails if the
  *wired* value regresses; a discoverable, consistent `.env.example`; a recorded audit.
- **Non-Goals:** refactoring the two-source design into one; changing eviction mechanics or the
  `notify_idle` contract; editing any other timeout, the README, or WebUI.

### Decisions (with rationale)
- **D1 — change both values, don't refactor (Approach B over C).** Minimal blast radius, removes
  drift, keeps the frozen FSM behavior. Alternative C (single source) is a larger change with no
  additional correctness benefit here.
- **D2 — assert the app-wired value, not a literal.** The test builds `create_app()` with no
  injected orchestrator and reads `app.state.orchestrator._inner._idle_timeout`, exercising
  `env → create_app → Orchestrator(...)`. This directly defeats the contract's adversarial case
  "the test asserts the constant literal rather than the app-wired value." (`_inner` is the real
  `Orchestrator` inside the `MeteredOrchestrator` pass-through; reaching a private attr in a test
  matches the repo's own style, e.g. `test_idle_timer_skipped_when_lock_held` touches `_lock`.)
- **D3 — cover the constructor default separately.** A `Orchestrator(stub_factory)` built with no
  `idle_timeout` asserts `_idle_timeout == 1800.0`, pinning `manager.py:46` against drift (R-02).
- **D4 — `0`-disables stays proven.** The existing `test_idle_timeout_zero_disables` already pins
  the `notify_idle` branch (`if self._idle_timeout > 0`). The new module additionally asserts the
  app wires `0.0` when `COSMOS3_IDLE_TIMEOUT_SECONDS=0`, so the wiring *and* the behavior are both
  covered (INV-2, failure-mode watch).
- **D5 — active `.env.example` line = code default.** Consistent with the "shown for clarity"
  block; keeps "default settings" edit-free (PRD Decision 4).

### Risks / Trade-offs
- [Partial change → drift (R-02/E-06)] → change both values + D2/D3 tests.
- [Test pins a literal, not wiring] → D2 builds through `create_app()`.
- [`0`-disables branch uncovered] → D4.
- [Accidentally editing README (R-05)] → README is forbidden; verified untouched at close.
- [`.env.example` drifts from code default] → active line equals code default; deterministic `rg`
  check compares both.
- [Reaching `_inner` couples the test to the metered wrapper] → low; the wrapper is frozen and the
  coupling is a deliberate, documented seam. If it ever changes, the test fails loudly (good).

### Migration / rollback
Value-only change; rollback = revert the two constants (and the doc/test additions). No data or
schema migration. Operators who had relied on the 10-min default can set
`COSMOS3_IDLE_TIMEOUT_SECONDS=600`.

### Open questions
None blocking. Future (non-goal) cleanup: collapse the two idle-default definitions into a single
source of truth; and the WebUI SSE heartbeat (E-08/R-03) remains a deliberate out-of-scope note.

---

## 5. Specification — capability `idle-keep-warm-default`

Normative keywords per RFC 2119. Each scenario is a candidate test case.

### Requirement: Shipped idle keep-warm default is 1800 s at both sources of truth
The application SHALL wire an idle keep-warm window of 1800 seconds when no
`COSMOS3_IDLE_TIMEOUT_SECONDS` is set, and the `Orchestrator` constructor SHALL default
`idle_timeout` to `1800.0`, so the wired path and a directly-constructed orchestrator cannot
drift (FR-1/FR-2, E-06).

#### Scenario: App wired with no timeout env
- **WHEN** the app is built via `create_app()` with `COSMOS3_IDLE_TIMEOUT_SECONDS` unset
- **THEN** the wired orchestrator's idle keep-warm window is `1800.0` seconds

#### Scenario: Orchestrator constructed without an idle_timeout argument
- **WHEN** an `Orchestrator` is constructed with only a worker factory (no `idle_timeout`)
- **THEN** its idle keep-warm window is `1800.0` seconds

### Requirement: Idle keep-warm stays operator-overridable and 0 disables eviction
The value SHALL remain governed by `COSMOS3_IDLE_TIMEOUT_SECONDS`; an explicit override SHALL be
honored, and `0` SHALL disable idle eviction (no timer scheduled), leaving the `notify_idle`
contract unchanged (FR-2, INV-2).

#### Scenario: Explicit override is honored
- **WHEN** the app is built with `COSMOS3_IDLE_TIMEOUT_SECONDS=900`
- **THEN** the wired orchestrator's idle keep-warm window is `900.0` seconds

#### Scenario: Zero disables eviction
- **WHEN** the app is built with `COSMOS3_IDLE_TIMEOUT_SECONDS=0`
- **THEN** the wired orchestrator's idle keep-warm window is `0.0`
- **AND** an idle orchestrator with `idle_timeout=0` schedules no idle timer on `notify_idle`

### Requirement: The knob is documented in .env.example consistent with the code default
`.env.example` SHALL contain `COSMOS3_IDLE_TIMEOUT_SECONDS` with a one-line comment stating it is
the idle keep-warm window in seconds (default 1800 = 30 min, `0` = never evict), and its value
SHALL equal the code default (FR-3).

#### Scenario: .env.example documents the knob
- **WHEN** `.env.example` is inspected
- **THEN** it contains `COSMOS3_IDLE_TIMEOUT_SECONDS=1800`
- **AND** an adjacent comment states the seconds meaning, the 30-min default, and `0` = never evict

### Requirement: Generation and cold-start ceilings are audited and unchanged
`LX-S1` SHALL record in `docs/evidence_map.md` that the generation-duration timeouts
(`COSMOS3_GEN_TIMEOUT` 2400 s / 7200 s) and the cold-start ceiling (`COSMOS3_PLANE_READY_TIMEOUT`
1800 s) already meet or exceed 30 minutes, and SHALL NOT change those values (FR-4, INV-3).

#### Scenario: Audit is recorded without changing the audited values
- **WHEN** `docs/evidence_map.md` is inspected after the session
- **THEN** it records the gen (2400/7200) and cold-start (1800) ceilings as ≥30 min and unchanged
- **AND** `api/jobs/gen_client.py`, `api/engines/vllm_omni/work.py`, and `api/app/main.py:177`
  retain their existing timeout values

---

## 6. Traceability

| Spec requirement | PRD | Contract | Deliverable | Test / check |
|---|---|---|---|---|
| Default 1800 at both sources | FR-1/FR-2 | Gate; INV | main.py:173, manager.py:46 | `test_app_wires_...1800`, `test_orchestrator_constructor_default...` |
| Override + 0 disables | FR-2 | INV-2 | (behavior) | `test_app_honors_override`, `test_app_wires_zero` + existing `test_idle_timeout_zero_disables` |
| `.env.example` documents knob | FR-3 | Gate | .env.example | `rg` check + structure assert |
| Gen/cold-start audit | FR-4 | Gate | evidence_map.md | `rg`/inspection; no value change |
| README untouched | FR-5/R-05 | Change Control | (none) | `git`/`rg` check |
