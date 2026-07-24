# Session 1 (LX-S1) - Idle Keep-Warm: 10 min → 30 min

Contract: `docs/session_1_contract.yaml`
Risk: low
Routing: single_agent (single agent + deterministic checks + one review)

## Objective

Make a single RTX 5090 comfortable with default settings by extending the
**idle keep-warm** timeout from 10 to 30 minutes, so the resident generation
plane survives a normal think-and-iterate loop instead of being evicted and
cold-reloaded. Change the shipped default of `COSMOS3_IDLE_TIMEOUT_SECONDS`
from 600 to 1800 at both of its sources of truth, surface the knob in
`.env.example`, and record the audit that generation and cold-start ceilings
already cover ≥30-min work. Runs first; does not touch `README.md`.

## Why This Session Exists

After a generation job finishes, the orchestrator starts an idle timer and
evicts the resident plane (a process-group kill that frees VRAM) if no new job
arrives within `COSMOS3_IDLE_TIMEOUT_SECONDS`, default **600 s**
(`api/app/main.py:173`; `api/orchestrator/manager.py` `notify_idle` →
`_on_idle_timeout` → `_try_idle_evict`, `docs/evidence_map.md` E-01/E-02). A
user who generates a clip, watches it, and tweaks the prompt more than ten
minutes later pays a full cold start again. On a single 5090 that iteration
loop is the normal workflow, so the default punishes the intended use.

The originating request framed this as a "video-generation timeout," but the
generation-duration timeouts are already 40 min–2 h (`COSMOS3_GEN_TIMEOUT`,
E-03) and the cold-start ceiling is already 30 min (`COSMOS3_PLANE_READY_TIMEOUT`,
E-04). The idle keep-warm is the knob that actually causes the "cold reload
after I pause" pain (PRD §1.1). This session raises **only** the idle keep-warm
default and audits the rest. It is **low** risk: a single constant at two
aligned definitions, no schema or route change, host-testable without a GPU.

## In Scope

1. **Change the shipped default.** Set `COSMOS3_IDLE_TIMEOUT_SECONDS`'s fallback
   from `"600"` to `"1800"` at `api/app/main.py:173`.
2. **Align the second definition.** Set the `Orchestrator` constructor default
   `idle_timeout: float = 600.0 → 1800.0` at `api/orchestrator/manager.py:46`,
   so a directly-constructed orchestrator (tests, future callers) cannot drift
   from the wired default (E-06, `R-02`).
3. **Surface the knob.** Add `COSMOS3_IDLE_TIMEOUT_SECONDS` to `.env.example`
   with a one-line comment: idle keep-warm window in seconds, default 1800
   (30 min), `0` = never evict — consistent with the code default (E-07).
4. **Prove it.** Add/extend a CPU unit test that the app built with no timeout
   env wires an idle timeout of 1800; an explicit override is honored; `0`
   disables eviction (no timer scheduled). Follow the orchestrator's existing
   injected-timer test style — no GPU.
5. **Record the audit.** In `docs/evidence_map.md`, confirm the
   generation-duration timeouts (2400 s / 7200 s) and the cold-start ceiling
   (1800 s) already meet or exceed 30 min, so the idle change is the one that
   serves the goal (E-03/E-04, FR-4). Do not change those values.

## Out of Scope

- Any timeout other than `COSMOS3_IDLE_TIMEOUT_SECONDS`
  (`COSMOS3_GEN_TIMEOUT`, `COSMOS3_PLANE_READY_TIMEOUT`,
  `COSMOS3_REASONER_TIMEOUT`, the WebUI SSE `heartbeatTimeoutMs`).
- Editing `README.md` (owned by `LX-S2`) or any WebUI file.
- Any public API schema/route change; any GPU work or GPU smoke.
- Changing the `notify_idle` semantics, the eviction mechanism, network
  binding, auth posture, checkpoints, or the vLLM-Omni pin.

## Deliverables

- `COSMOS3_IDLE_TIMEOUT_SECONDS` default = 1800 at both `api/app/main.py` and
  `api/orchestrator/manager.py`, with the knob documented in `.env.example`.
- A CPU unit test pinning the app-wired idle default (1800), an override, and
  the `0`-disables case.
- The generation/cold-start audit recorded in `docs/evidence_map.md`, and the
  30-min behavior noted for the `LX-S2` README status callout in the handoff.

## Deterministic Checks

```bash
rg -n "COSMOS3_IDLE_TIMEOUT_SECONDS" api/app/main.py .env.example   # expect: 1800 default + documented
rg -n "idle_timeout" api/orchestrator/manager.py                     # expect: default 1800.0
uv run pytest -m "not gpu"                                           # incl. the new idle-default test
```

## Exit Criteria

- `GATE-LX-S1-TIMEOUT` passes.
- The app wires a 1800 s idle keep-warm with no env set; an override is
  honored; `0` disables eviction (`EV-LX-IDLE-DEFAULT-1800`).
- `.env.example` documents the knob consistently (`EV-LX-ENV-EXAMPLE-DOC`).
- The generation/cold-start audit is recorded (`EV-LX-TIMEOUT-AUDIT`); no other
  timeout, schema, or route changed.
- The CPU suite is green (`EV-LX-CPU-SUITE-GREEN`); `README.md` is untouched.

## Handoff

Record, for `LX-S2`, that the idle keep-warm default is now 30 min so the
README status callout can state it accurately. Confirm no README edit was made
(the shared-surface guard, `R-05`). Note the WebUI SSE heartbeat (`R-03`, E-08)
remains a deliberately out-of-scope future consideration.
