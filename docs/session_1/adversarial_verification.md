# LX-S1 Adversarial Verification

Date: 2026-07-24 · Verifier: fresh-context, read-only subagent (did not see the implementation
conversation; saw only the contract, the working-tree diff, and repository evidence). Task: try to
**falsify** the `GATE-LX-S1-TIMEOUT` done condition.

## Falsification checklist — result

| # | Probe | Result | Evidence |
|---|---|---|---|
| 1 | Default 1800 at BOTH sources (no drift)? | PASS | `api/app/main.py:175` `"1800"`; `api/orchestrator/manager.py:46` `1800.0`; no third definition. |
| 2 | Test pins the APP-WIRED value, not a literal (non-hollow)? | PASS | Reverted `main.py` fallback to `600` → `test_app_wires_idle_keepwarm_default_1800` **failed** (`600.0 == 1800.0`); restored. A wiring regression is genuinely caught. |
| 3 | Override + 0-disabled tested and working (INV-2)? | PASS | `override→900.0`; `0→0.0`; `0`-schedules-no-timer with slot forced resident (guard `if self._idle_timeout > 0 …`). |
| 4 | `.env.example` consistent with the code default (no drift)? | PASS | `.env.example:20-23` documents `=1800`, "matches the code default". |
| 5 | Audit recorded without changing audited values? | PASS | `docs/evidence_map.md` LX-S1 audit; `gen_client.py` 2400 / `work.py` 7200 / `main.py:179` 1800 all unchanged (not in the diff). |
| 6 | Any other timeout / schema / route changed (INV-3)? | PASS | `git diff` on `gen_client.py`, `engines/vllm_omni/work.py`, `routes/reasoning.py`, `schemas/openapi.json`, `api/app/routes/` → empty. |
| 7 | `uv run pytest -m "not gpu"` actually green? | PASS | Ran it: **523 passed, 1 warning** (pre-existing httpx/Starlette deprecation), exit 0. Private-ref scan CLI → "clean (0 findings)". |
| 8 | `README.md` untouched (R-05)? | PASS | `git diff README.md` empty; not in `git status`. |
| 9 | Anything outside the blast radius; is the archive scrub effective? | PASS (+ governance note) | Only `docs/archive/phase-3/session_4/plan.md` is out of the declared radius — an owner-authorized one-line scrub (execution_contract §2.1). Verified minimal (`numstat 1 1`), the replacement char is U+2026 (confirmed via `ord()`), the leaked path is gone from `docs/`, and the scan is clean. |

## Verdict

**SESSION VERDICT: PASS** — the verifier could not falsify any part of the done condition. It
tamper-tested the suite (injected a 600 regression, saw the headline test fail, restored, and
confirmed `git status` returned to the exact pre-tamper state).

Governance note (non-blocking, recorded): editing `docs/archive/**` contradicts the literal
blast-radius / Change-Control text; it is an owner-authorized exception (§2.1) that is minimal,
effective, and reduces a real pre-existing INV-1 leak rather than introducing one. The gate and
done condition do not reference the archive file, so this does not falsify the gate.
