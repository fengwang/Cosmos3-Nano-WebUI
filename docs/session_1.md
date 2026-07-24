# Session 1 (AM-S1) - Feasibility Spike (FP8): can vllm-omni serve Reasoning + Action off quantized-only?

Contract: `docs/session_1_contract.yaml`
Risk: high
Routing: branch-and-compare (option a vs c, per mode) + evidence capture + owner decision gate

## Objective

Resolve the phase's pivotal unknowns on the RTX 5090, against the **FP8**
quantized checkpoint, before any production wiring is built:

1. Does `vllm serve --omni` on the quantized checkpoint answer
   `/v1/chat/completions` with coherent output (option (a) for **reasoning**)?
2. Can `vllm-omni` serve **action**, or must action use a side-by-side backend
   (option (c))?
3. Confirm the **action-tensor gap** (the quantized checkpoint ships without
   `action_*` tensors, `docs/evidence_map.md` E-06) against the real checkpoint,
   and decide the **zero-BF16 action packaging path** (bundle adapters via
   `tools/checkpoint_prep/` vs an alternative).

Output is an **owner-approved decision record**, not shipped production code. A
throwaway/dev wiring (manual `docker exec`, a scratch route, `curl`) is acceptable
— the goal is evidence and a decision, so `AM-S2`/`AM-S3` build the right thing
once.

## Why This Session Exists

The whole architecture branches on these answers (`docs/project_contract.md`
§two-pass items 1–3). Option (a) — `vllm-omni` serves everything — is the owner's
preference (PRD Decision 4) and is *plausible* for reasoning because `vllm-omni`
is an OpenAI server and the quantized checkpoint ships a chat template (E-02/E-03),
but it is **unproven**, and it is doubtful for action, which is not a standard
OpenAI surface (E-07). Meanwhile zero-BF16 action is not a serving toggle at all —
it needs the small bf16 `action_*` adapters bundled into the quantized checkpoint
(E-06/E-17). Committing `AM-S2`/`AM-S3` to a mechanism before knowing these would
risk building the wrong thing. This session buys that knowledge cheaply.

## In Scope

1. **Reasoning probe.** On the running FP8 `vllm-omni` container, attempt
   `/v1/chat/completions` (and whatever the fork's `--omni` server exposes) off the
   quantized transformer; capture whether it loads, responds, and is coherent.
   Compare against the current separate-`vllm`-subprocess reasoner behavior (E-04)
   and reproduce the "reasoning not currently working" report (E-05).
2. **Action probe.** Determine whether `vllm-omni` exposes any action-capable
   surface; if not, characterize the `(c)` fallback (the existing
   `diffusers_action` graft as its own residency plane).
3. **Action-tensor gap confirmation + packaging spike.** Verify E-06 against the
   real FP8 checkpoint (no `action_*` tensors). Evaluate `tools/checkpoint_prep/`
   (`mutation`, `rewrite`, `safetensors_io`, `integrity_probe`) for bundling the
   bf16 adapters into a re-exported checkpoint; produce a go/no-go + rough recipe.
4. **VRAM reality.** Record footprints: quantized generation resident; a
   quantized-transformer chat server resident; whether Studio+Reasoning could share
   one resident model (option (a) collapsing two planes into one) or must still
   swap (`docs/evidence_map.md` E-08, INV-5).
5. **Decision record.** Write the per-mode `(a)`/`(c)` decision, the zero-BF16
   action packaging decision, and the residency implication into the `AM-S1`
   working doc and `docs/evidence_map.md` (resolving S-A/S-C/S-E direction); get
   owner sign-off.

## Out of Scope

- Production wiring of reasoning/action (that is `AM-S2`/`AM-S3`).
- NVFP4 (that is `AM-S5`); this spike is FP8-only (PRD Decision 7).
- The owner's final *quality* verdict on reasoning/action output — this session
  establishes *feasibility*; quality PASS is gated in `AM-S2`/`AM-S3`.
- Editing `README.md`, `docs/walkthrough.md`, or any WebUI file.
- Committing any re-exported checkpoint or weights (weights stay external, NFR-1).

## Deliverables

- An `AM-S1` decision record (working doc) with: reasoning `(a)`/`(c)`, action
  `(a)`/`(c)`, zero-BF16 action packaging path (bundle vs alternative), the
  residency implication (swap vs possible plane-merge), and captured evidence
  (commands, responses, VRAM samples).
- `docs/evidence_map.md` updated: S-A/S-C/S-E direction resolved to a chosen path;
  E-06 confirmed against the real checkpoint; an `AM-S1` execution audit block.
- Owner sign-off recorded (the human decision gate).

## Checks

```bash
# Feasibility is demonstrated by running commands on the 5090; capture their output.
# Deterministic host checks for this session:
uv run pytest -m "not gpu"                       # unchanged baseline stays green
rg -n "action_" api/engines/diffusers_action/loader.py   # re-confirm the E-06 gap premise
```

GPU probe evidence (reasoning chat off quantized FP8; action serving attempt; VRAM
samples) is captured as artifacts/notes, per the evidence fields.

## Exit Criteria

- `GATE-AM-S1-SPIKE` passes: a per-mode `(a)`/`(c)` decision and a zero-BF16 action
  packaging decision are recorded, the action-tensor gap is confirmed against the
  real checkpoint, and the **owner has signed off** on the chosen paths.
- `docs/evidence_map.md` reflects the resolved directions (S-A/S-C/S-E) and the
  audit; the CPU baseline is still green.

## Handoff

Record, for `AM-S2`/`AM-S3`: the chosen mechanism per mode; the zero-BF16 action
packaging recipe (or the explicit owner decision if bundling is deferred); the
residency implication (does Studio+Reasoning swap or share one model); and any
`vllm-omni` fork capability/limitation discovered. Flag whether `AM-S1` should fold
forward into `AM-S2` (if the spike already produced most of the reasoning wiring).
