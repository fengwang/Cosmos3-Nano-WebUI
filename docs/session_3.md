# Session 3 (AM-S3) - Action Enabled + GPU-Verified on FP8 (zero-BF16)

Contract: `docs/session_3_contract.yaml`
Risk: high
Routing: worker + sharded review + adversarial verifier + checkpoint-integrity probe + owner quality gate

## Objective

Make **Action** (`/v1/action/{forward_dynamics,inverse_dynamics,policy}`) run end
to end on the FP8 stack off a **quantized-only** checkpoint, and obtain the owner's
manual quality PASS — without regressing `t2i`. Because the quantized checkpoint
ships **without** action tensors (`docs/evidence_map.md` E-06), zero-BF16 action
requires either bundling the small bf16 `action_*` adapters into the quantized
checkpoint (E-17, via `tools/checkpoint_prep/`) or the `AM-S1` `(c)` fallback — with
any residual BF16 dependency made an explicit owner decision (INV-4), never a silent
default.

## Why This Session Exists

Action is the hardest mode for zero-BF16: it is not a serving toggle but a
**checkpoint-packaging** problem (E-06), and it may not be servable by `vllm-omni`
at all (E-07, R-02). Getting it right needs its own high-risk session with a
checkpoint-integrity gate and the owner's quality verdict on trajectories.

## In Scope

1. **Zero-BF16 action checkpoint (if `AM-S1` chose bundling).** Use
   `tools/checkpoint_prep/` (`mutation`/`rewrite`/`safetensors_io`) to bundle the
   bf16 `action_*` adapters (`action_modality_embed`, `action_proj_in/out`) into a
   **re-exported** FP8 checkpoint; run `integrity_probe` (`EV-AM-CHECKPOINT-INTEGRITY`);
   pin a **new immutable revision** and record it in `docs/model_setup.md` (NFR-5);
   never mutate in place or repoint `main` (R-10).
2. **Serve action** by the `AM-S1` mechanism (option (a) via `vllm-omni` if
   feasible; else option (c): the `diffusers_action` graft as its own residency
   plane, still evict-before-load, INV-5), pointed at the quantized(-bundled)
   checkpoint rather than the BF16 base (`COSMOS3_BASE_ACTION_DIR` retired/redirected).
3. **Re-verify `t2i`** against the (possibly new) checkpoint revision
   (`GPU-AM-T2I-NOREGRESS`, INV-2) — a re-export must not corrupt generation.
4. **GPU-verify action** end to end for the v1-scope embodiments (agibotworld 29-D
   `policy`/`forward_dynamics`; av 9-D `inverse_dynamics`) through the Action tab's
   3D/2D viewer (`GPU-AM-ACTION-FP8`).
5. **Owner quality gate.** The owner inspects trajectories/artifacts and records a
   verdict (`OWNER-AM-ACTION-QUALITY`); PASS required to promote (INV-6). CPU suite
   green, updating any `test_action_*` that pinned the old base-dir graft.

## Out of Scope

- Reasoning (`AM-S2`) and the default-on merge (`AM-S4`).
- NVFP4 (`AM-S5`); `README.md`/`docs/walkthrough.md` (`AM-S6`).
- Deleting the dormant `diffusers` `gen_worker` path unless it actively conflicts
  (R-11) — not a required cleanup.
- Committing any checkpoint/weights (weights stay external; only the pinned
  revision id is recorded, NFR-1).

## Deliverables

- Action served off a quantized-only checkpoint on FP8; if re-exported, a new
  pinned revision recorded in `docs/model_setup.md` with an integrity-probe pass.
- `GPU-AM-ACTION-FP8` and a re-run `GPU-AM-T2I-NOREGRESS` recorded; the owner's
  `OWNER-AM-ACTION-QUALITY` verdict recorded.
- `docs/evidence_map.md` / `docs/risk_register.md` updated (R-01/R-02/R-10 progress);
  CPU suite green.

## Checks

```bash
uv run pytest -m "not gpu"                                   # green; updated action wiring tests
uv run python -m tools.checkpoint_prep ...                   # re-export + integrity probe (if bundling)
rg -n "COSMOS3_BASE_ACTION_DIR|action_" api/engines/diffusers_action/loader.py
# GPU: action end-to-end off quantized(-bundled) FP8; t2i smoke re-passes at the new revision.
```

## Exit Criteria

- `GATE-AM-S3-ACTION` passes: action runs end to end on FP8 off a quantized-only
  checkpoint; if a checkpoint was re-exported, a new revision is pinned + integrity
  probed and `t2i` re-verified against it; the `t2i` smoke re-passes (INV-2); CPU
  suite green; the owner's action-quality verdict is recorded **PASS** (INV-6).
- Any residual BF16 dependency is an explicit, recorded owner decision, not a
  silent default (INV-4).

## Handoff

Record for `AM-S4`: the action serving mechanism, the checkpoint revision now in
use (and whether it superseded the generation checkpoint or is a separate mount),
the env/mount surface with `COSMOS3_BASE_ACTION_DIR` retired/redirected, and the
owner quality verdict. Note whether the dormant `diffusers` path was left in place.
