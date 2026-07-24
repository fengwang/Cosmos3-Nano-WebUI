# Session 5 (AM-S5) - Extend + GPU-Verify on NVFP4

Contract: `docs/session_5_contract.yaml`
Risk: high
Routing: branch-and-compare per mode (a/c; kernel fallback) + adversarial verifier + owner per-mode quality gate

## Objective

Extend the verified FP8 all-modes design (`AM-S4`) to the **NVFP4** stack and
GPU-verify Studio, Reasoning, and Action on NVFP4, off the quantized-only NVFP4
checkpoint, handling the newer 4-bit Blackwell kernel risk. Each mode is enabled by
default on NVFP4 only after it passes on NVFP4 (owner quality PASS); a mode that
cannot be served on NVFP4 off quantized weights is an explicit, documented owner
decision (INV-7), not a hidden gap. `t2i` (NVFP4) stays non-regressed.

## Why This Session Exists

NVFP4 is the phase's largest residual unknown. NVFP4 `t2i` works today via a Marlin
FP4 kernel that repacks weights on CUDA after load and deliberately forbids
layer-wise offload (`deploy/docker-compose.nvfp4.yml:15-20`), but the LM (reasoning)
and action inference paths on 4-bit NVFP4 are unproven (`docs/evidence_map.md` S-D,
R-04), and 4-bit quantization is the riskiest case for reasoning **quality** (S-B,
R-03). Isolating NVFP4 to its own session (after the whole vertical is proven on
FP8, PRD Decision 7) keeps it the only new variable.

## In Scope

1. **Apply the `AM-S4` all-modes design to the NVFP4 stack.** Reasoning and action
   served off the quantized-only NVFP4 checkpoint by the same mechanism chosen for
   FP8 (option a/c), with no BF16 base (INV-4).
2. **Handle NVFP4 kernel reality per mode.** Where the NVFP4 4-bit path cannot
   serve reasoning or action (kernel/support gap, S-D), attempt the `(c)` fallback;
   if still infeasible, record an explicit owner decision and document the
   NVFP4-format limitation (INV-7) — the FP8 stack is unaffected.
3. **GPU-verify each mode on NVFP4** (`GPU-AM-ALLMODES-NVFP4`): Studio, Reasoning,
   Action, with on-demand swaps; `t2i` (NVFP4) non-regressed
   (`GPU-AM-T2I-NOREGRESS`, INV-2).
4. **Owner quality gate per mode on NVFP4** (`OWNER-AM-REASON-QUALITY`,
   `OWNER-AM-ACTION-QUALITY`): the owner runs custom prompts on the NVFP4 stack and
   records verdicts; only PASS modes are enabled by default on NVFP4 (INV-6/INV-7).
   Record NVFP4 VRAM footprints (NVFP4 has no offload; ~16.3 GiB resident for gen).
   CPU suite green.

## Out of Scope

- Any change to the FP8 stack's verified behavior (regressions there block).
- `README.md` / `docs/walkthrough.md` prose (that is `AM-S6`).
- Introducing `diffusers` `t2v` (INV-3); auth/guardrails/network changes; new API
  schema shapes unless authorized (INV-8).
- Forcing a mode onto NVFP4 if hardware/kernels cannot support it — that becomes a
  documented owner decision, not a workaround that risks `t2i` or correctness.

## Deliverables

- NVFP4 all-modes deployment: each mode either GPU-verified (owner PASS) and
  default-on, or a recorded owner-decided NVFP4 limitation.
- `GPU-AM-ALLMODES-NVFP4` + `GPU-AM-T2I-NOREGRESS` (NVFP4) recorded with evidence
  fields; NVFP4 owner quality verdicts recorded.
- `docs/evidence_map.md` / `docs/risk_register.md` updated (R-03/R-04 resolved to a
  per-mode NVFP4 outcome); CPU suite green.

## Checks

```bash
uv run pytest -m "not gpu"                                   # green
docker compose -f deploy/docker-compose.nvfp4.yml config     # all-modes wiring; no BF16 mount
# GPU: one `make up-nvfp4` → per-mode verification; t2i (NVFP4) non-regressed; VRAM captured.
```

## Exit Criteria

- `GATE-AM-S5-NVFP4` passes: the `AM-S4` design is applied to NVFP4; each mode is
  GPU-verified on NVFP4 (owner PASS) or its limitation is a recorded owner decision
  (INV-7); `t2i` (NVFP4) non-regressed (INV-2); no BF16 on the NVFP4 default path
  (INV-4); CPU suite green.
- Default-on applies only to modes that passed on NVFP4 (INV-6/INV-7).

## Handoff

Record for `AM-S6`: the final per-mode, per-format (FP8 / NVFP4) verification
matrix — exactly which modes passed the owner gate on which format — so the README
status table and `docs/walkthrough.md` reflect only what is real, and any
NVFP4-format limitation is documented honestly.
