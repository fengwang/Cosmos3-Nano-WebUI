# AM-S1 Execution Contract

Date: 2026-07-24
Derived from: `docs/session_1/design.md` + `docs/session_1_contract.yaml`.
This is the operational contract the probe loop executes against.

## Planned file changes (all within blast radius; docs-only)

| File | Change |
|---|---|
| `docs/session_1/brainstorming.md` | ✅ written |
| `docs/session_1/design.md` | ✅ written |
| `docs/session_1/execution_contract.md` | ✅ this file |
| `docs/session_1/evidence/*` | raw probe artifacts (commands + outputs, VRAM traces) |
| `docs/session_1/decision_record.md` | the deliverable (per-mode + packaging + residency decisions) |
| `docs/session_1/sharded_review.md` | sharded review results (risk=high) |
| `docs/session_1/adversarial_verification.md` | fresh-context falsification pass |
| `docs/evidence_map.md` | resolve S-A/S-C/S-E direction; confirm E-06; append AM-S1 execution audit |
| `docs/risk_register.md` | advance R-01/R-02 (and R-04/R-08 notes if surfaced) |
| `docs/eval_seed_cases.md` | harvest EV-AM-SPIKE-DECISION-RECORDED, EV-AM-CPU-SUITE-GREEN |
| `docs/handoff.md` | new (first handoff of phase-5) |

## Allowed blast radius (from the session contract)

**Allowed:** `docs/session_1/**`, `docs/evidence_map.md`, `docs/risk_register.md`,
`docs/eval_seed_cases.md`, `docs/handoff.md`.
**Forbidden (hard stop if tempted):** any `api/**`; any `deploy/**`, `Makefile`,
`.env.example`; `tools/checkpoint_prep/**` (evaluate, never modify); `README.md`,
`docs/walkthrough.md`, `docs/images/**`; `schemas/openapi.json`; `docs/archive/**`;
any weight/checkpoint/media file. Throwaway GPU **containers** are permitted
(runtime only, `--rm`); they are not repo files.

## First evidence to capture (the spike's "first test")

**P1 — E-06 against the pinned checkpoint.** It is cheap, no-GPU, and load-bearing
for the whole action branch. Success criterion (frozen): the pinned FP8
`transformer` safetensors expose **zero** `action_*` keys and the BF16 base exposes
them. This is the first artifact written to `docs/session_1/evidence/`.

## Checks to run after each probe

- After **every** probe: append the raw artifact to `docs/session_1/evidence/` and
  the one-line rubric verdict; confirm no forbidden file was touched
  (`git status --porcelain` shows only allowed paths).
- After any GPU probe: `nvidia-smi` shows the probe container removed and VRAM
  returning toward idle (no leak); `docker ps` shows no stray probe container left
  running unless intentionally resident for the next probe.
- Before closing: re-run the two deterministic checks —
  `uv run pytest -m "not gpu"` (must stay green) and
  `rg -n "action_" api/engines/diffusers_action/loader.py` (premise unchanged).

## Failure classification (before any fix)

Every probe failure is classified with the Failure Arbiter
(`docs/agent_workflow/prompts/failure_arbiter.md`) as BUG / SPEC_GAP / AMBIGUITY /
**ENVIRONMENT** / TEST_BUG **before** acting. For a spike, most probe failures are
either ENVIRONMENT (image/dep/timeout) or genuine **findings** (e.g. D1 blocks P6,
omni exposes no chat) — a *finding* is recorded as the rubric verdict, **not**
fixed. Product code is never edited (docs-only blast radius). Arbiter results, if
any, go to `docs/session_1/failure_arbiter.md`.

## Review axes to run at the end (risk = high → sharded review)

correctness · security · tests · architecture · performance · readability — applied
to the *decision record + evidence* (are the verdicts actually backed by the
captured evidence; is any claim over-stated; is the anti-conflation rule honored;
is any forbidden edit present; is the packaging recipe sound). Save to
`docs/session_1/sharded_review.md`. Fix High/Critical only, then re-check.

## Adversarial verifier brief (fresh context)

Give a fresh-context verifier ONLY: `docs/session_1_contract.yaml`, the diff, and
`docs/session_1/evidence/*` + `decision_record.md`. Its job: **falsify** that
`GATE-AM-S1-SPIKE` is satisfied. Specific attacks (from the contract's
`adversarial_cases`):
1. Is any "works" verdict backed only by "server loaded" (feasibility↔quality
   conflation)?
2. Is E-06 *assumed* rather than re-confirmed against the actual downloaded
   checkpoint?
3. Did any permanent production edit sneak in (blast-radius breach)?
4. Does the decision omit the `(c)` fallback for action?
5. Is any VRAM/headroom claim asserted without an `nvidia-smi` trace?
Save to `docs/session_1/adversarial_verification.md`; classify any failure with the
Arbiter.

## Concrete done condition (GATE-AM-S1-SPIKE)

All true:
1. Per-mode `(a)`/`(c)` decision recorded **for reasoning and action**, each with
   captured evidence against the pre-registered rubric.
2. Zero-BF16 action packaging decided (bundle vs alternative); **E-06 confirmed
   against the pinned checkpoint** (P1 artifact).
3. Residency implication (swap vs plane-merge) recorded **with `nvidia-smi`
   samples** (P7 artifact).
4. `uv run pytest -m "not gpu"` green; no forbidden file modified.
5. `docs/evidence_map.md` reflects resolved S-A/S-C/S-E + the AM-S1 audit block.
6. **Owner (Feng) has signed off** on the chosen paths — the human gate; the agent
   presents evidence + decisions and does not self-certify this line.
