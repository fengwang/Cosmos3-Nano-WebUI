# Session 2 (AM-S2) - Reasoning Enabled + GPU-Verified on FP8 (zero-BF16)

Contract: `docs/session_2_contract.yaml`
Risk: high
Routing: worker + sharded review + adversarial verifier + independent `t2i`-non-regression check + owner quality gate

## Objective

Make **Reasoning** (`/v1/reason`) run end to end on the FP8 stack off the
**quantized-only** checkpoint — no BF16 base mount, no `docker-compose.reasoning.yml`
overlay, no `WITH_REASONING` build — by the mechanism `AM-S1` selected (option (a):
route reasoning to the `vllm-omni` container's chat endpoint; or option (c): a
side-by-side reasoner residency pointed at the quantized checkpoint). Re-verify the
`t2i` path is not regressed, and obtain the owner's manual quality PASS.

## Why This Session Exists

Reasoning is the mode most likely to reach zero-BF16 (it is a language-model
surface a vLLM OpenAI server speaks natively, and the quantized checkpoint ships a
chat template — `docs/evidence_map.md` E-02/E-03), and today it is not runnable in
the default stack at all (E-04/E-05). Proving reasoning first, on the safe FP8
format, establishes the zero-BF16 serving pattern that `AM-S3`/`AM-S4` build on. It
is high risk because it changes the serving/orchestration seam that the one verified
mode (`t2i`) shares.

## In Scope

1. **Serve reasoning off the quantized FP8 checkpoint** by the `AM-S1` mechanism:
   - option (a): point `/v1/reason` at the `vllm-omni` container's chat completions
     (retiring the separate BF16 `vllm` subprocess for this stack); or
   - option (c): run the reasoner as its own residency plane pointed at the
     quantized checkpoint dir (`COSMOS3_REASONER_MODEL_DIR` → the quantized mount),
     still evict-before-load against generation (INV-5).
2. **Remove the reasoning BF16 dependency** from this path: no BF16 base mount, no
   overlay, no `WITH_REASONING` default build (INV-4). If option (a) collapses
   Studio+Reasoning into one resident model, record the VRAM trace proving it stays
   OOM-free (INV-5, `coresidency.py` `handoff_ok`/`within_budget`); otherwise keep
   the swap.
3. **Preserve the residency safety net + API shape.** A different-mode request
   still preempts; `schemas/openapi.json` shape unchanged unless authorized (INV-8);
   the WebUI Reasoning tab (`/chat`) works unchanged (E-12).
4. **GPU-verify + `t2i` non-regression.** Run `/v1/reason` end to end on the 5090
   (`GPU-AM-REASON-FP8`); re-run the `t2i` smoke (`GPU-AM-T2I-NOREGRESS`, INV-2).
5. **Owner quality gate.** The owner runs custom reasoning prompts and records a
   verdict (`OWNER-AM-REASON-QUALITY`); PASS is required to promote reasoning to
   "verified"/default-eligible (INV-6). Keep the CPU suite green
   (`EV-AM-CPU-SUITE-GREEN`), updating any test that pinned the old reasoner wiring.

## Out of Scope

- Action (that is `AM-S3`) and the final default-on orchestration merge (that is
  `AM-S4`) — this session may use a transitional/minimal wiring to run reasoning;
  `AM-S4` makes the clean default.
- NVFP4 (that is `AM-S5`).
- Editing `README.md` or `docs/walkthrough.md` (that is `AM-S6`).
- Any BF16 reintroduction as a default (INV-4); any `diffusers` `t2v` change (INV-3).

## Deliverables

- Reasoning served off the quantized-only FP8 checkpoint by the chosen mechanism,
  with the BF16 reasoner dependency removed from this path.
- `GPU-AM-REASON-FP8` and `GPU-AM-T2I-NOREGRESS` recorded with evidence fields; the
  owner's `OWNER-AM-REASON-QUALITY` verdict recorded.
- Any VRAM-trace evidence if a plane-merge was adopted (INV-5).
- `docs/evidence_map.md` / `docs/risk_register.md` updated (R-03/R-05/R-08 progress);
  CPU suite green.

## Checks

```bash
uv run pytest -m "not gpu"                                   # green; updated wiring tests
docker compose -f deploy/docker-compose.fp8.yml config       # no BF16 base mount on the reasoning path
git diff schemas/openapi.json                                # empty unless authorized (INV-8)
# GPU: /v1/reason end-to-end off quantized FP8; t2i smoke re-passes (evidence captured).
```

## Exit Criteria

- `GATE-AM-S2-REASONING` passes: reasoning runs end to end on FP8 off the
  quantized-only checkpoint; `t2i` smoke re-passes (INV-2); CPU suite green; the
  owner's reasoning-quality verdict is recorded **PASS** (INV-6).
- No BF16 base / overlay / `WITH_REASONING` on the reasoning path (INV-4); the
  residency safety net holds (INV-5); API shape unchanged (INV-8).

## Handoff

Record for `AM-S3`/`AM-S4`: the exact reasoning wiring adopted (option a/c),
whether Studio+Reasoning share one resident model or swap, the reasoner's env/mount
surface now that BF16 is gone, and the owner quality verdict. Note any transitional
wiring `AM-S4` must finalize into the default stack.
