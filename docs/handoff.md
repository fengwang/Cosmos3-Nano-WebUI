# Session Handoff

## State Snapshot
- Session: **AM-S1** — Feasibility Spike (FP8), Phase-5 "All-Modes". Risk high.
- Branch: `fea/eanble-reasoning-action-phase-5-session-1`
- Last commit: `52feab3` (phase-5 blueprint). **AM-S1 deliverables are uncommitted**
  (docs-only; commit scoped to `docs/**` when desired).
- Changed files: **new** `docs/session_1/**` (brainstorming, design,
  execution_contract, decision_record, sharded_review, adversarial_verification,
  `evidence/P1,P2,P3,P5,P7`); **updated** `docs/evidence_map.md`,
  `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/handoff.md`.
  *(Not this session: ` M misc/logo.png`, `?? docs/archive/phase-4/` — pre-existing.)*
- Checks run: `uv run pytest -m "not gpu"` → **523 passed** (start + close + adversarial
  re-run); `rg action_ …/diffusers_action/loader.py`; live FP8 `vllm-omni` GPU probes
  (reasoning chat, action WS surface, VRAM traces); dependency-free safetensors header
  scans; HF range-read of the pinned public rev; the real repo `merge_state_dicts`.
- Checks not run: full GPU action **trajectory** (AM-S3 quality gate); **NVFP4**
  (AM-S5); reasoning **text-tower elicitation** (AM-S2); a `t2i` non-regression smoke
  (no serving path changed — deferred to the first enablement session).
- Current status: **GATE-AM-S1-SPIKE PASSES** (owner-signed 2026-07-24).

## Narrative Context
AM-S1 probed whether `vllm-omni` can serve reasoning + action off the quantized-only
FP8 checkpoint. It found the blueprint's **action premise (E-06) stale**: the
quantized checkpoints (deployed + pinned public + NVFP4) **already bundle** the BF16
`action_*` adapters via the prior **P6-S5 `checkpoint_prep mutate`**, so zero-BF16
action *packaging* is done. The **real blocker is reasoning**: the omni
`/v1/chat/completions` serves **images, not text**, so zero-BF16 reasoning is
**unproven**. Action's omni **robot surface exists** (`/v1/realtime/robot/openpi`)
but is **unwired**, and the in-process `(c)` graft is **broken** (collides on the
now-present tensors). Owner signed off; **AM-S2 investigates the omni text-tower**
for reasoning, **AM-S3 wires action via the omni robot policy** (`(a)`) with the
fixed `(c)` graft as fallback.

## Decision Log
| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| Reasoning mechanism | `(c)` side-car; zero-BF16 **unproven** | `(a)` omni chat | omni chat = image-gen, not text (P3) | S-A, R-15 |
| Action mechanism | `(a)` omni robot policy + `(c)` fallback | `(c)`-primary / `(a)`-only | `(a)` enables Studio+Action merge; `(c)` needs a code fix (P5) | S-C, R-02 |
| Zero-BF16 action packaging | **GO, already done** (P6-S5 mutate) | new re-export | adapters already bundled; E-06 refuted (P1/P2) | S-E, R-01 |
| Reasoning zero-BF16 approach | investigate omni text-tower first (AM-S2) | accept BF16 side-car now | keep the hard goal alive; side-car is the documented fallback | R-15, INV-4 |
| Does AM-S1 fold into AM-S2? | **No** | Yes | the spike produced **no** reasoning wiring (omni doesn't serve text) | handoff §8 |

## Next Priority Queue
1. **AM-S2 (reasoning, FP8):** investigate eliciting **text** from the quantized
   understanding/text tower (a `vllm-omni` fork modality flag, or serving the text
   tower on a separate engine). If unproven, record an explicit **BF16-reasoner
   side-car** owner decision (INV-4 exception, documented at the gate). Re-verify
   `t2i` non-regression; owner reasoning-quality gate.
2. **AM-S3 (action, FP8):** wire the omni `/v1/realtime/robot/openpi` policy to the
   checkpoint's **own** action weights (option `(a)`; Studio+Action plane-merge —
   **VRAM-verify** it stays in budget). Keep a **fixed** `(c)` graft as fallback:
   reconcile `api/engines/diffusers_action/loader.py` (stop grafting `action_*` from
   the BF16 base — the checkpoint has them; drop/adjust the stale
   `GEN_TOWER_QUANTIZED=505`). Bridge the API shape (WebUI REST `/v1/action/*` ↔ omni
   WS openpi). Re-verify `t2i`; owner action-quality gate.
3. **Serving-code reconciliation** (residual of R-01): the loader's docstring +
   base-graft + `505` constant all predate the P6-S5 mutation and are now wrong;
   folded into AM-S3.

## Warnings And Gotchas
- **Environment:** the deployed FP8 checkpoint is at on-disk rev `4e181f9`; the
  blueprint's pinned public `9bf5d6ae` is **not** in the local clone's git history
  (the repo was rebuilt) but **is** on HF and **also** carries the action adapters.
- **Known failing behavior (not a test):** the in-process `diffusers_action` loader
  is **broken** against the current checkpoint (key collision) — invisible to the CPU
  suite (torch-free imports). AM-S3 must fix before `(c)` can serve.
- **Deferred risks:** **R-15** (zero-BF16 reasoning unproven — the phase's main open
  risk); Studio+Action plane-merge VRAM is **projected, unmeasured**; **D1** (in-process
  loader `505 ≠ 216`, revision-independent).
- **Files future sessions must not casually edit:** AM-S1 touched only `docs/**`. Do
  **not** sweep `misc/logo.png` (pre-existing, unrelated working-tree change) into any
  commit — scope an AM-S1 commit to `docs/**`.

## Eval Seeds
- Missed check: E-06 (marked *High confidence*) was **code-derived**, never validated
  against the artifact → **EV-AM-PREMISE-VS-ARTIFACT** (inspect real bytes for any
  checkpoint/binary claim).
- New regression test candidate: **EV-AM-CHAT-IS-IMAGE** (omni `/v1/chat/completions`
  returns images; never record "reasoning works" from HTTP 200 / a loaded server).
- Instruction update candidate: a feasibility spike MUST inspect the real
  artifact/bytes for a checkpoint claim, not trust a code-derived premise; and MUST
  hold the feasibility↔quality line (endpoint-exists / loads ≠ works).
