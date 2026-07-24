# Session 4 (AM-S4) - Orchestration Simplification + Default-On (FP8)

Contract: `docs/session_4_contract.yaml`
Risk: high
Routing: worker + sharded review + adversarial verifier + full all-modes GPU smoke + owner confirmation

## Objective

Collapse the three deploy postures into a clean default so a plain `make up-fp8`
brings up **all three modes** — Studio, Reasoning, Action — off the quantized-only
FP8 checkpoint, with the orchestrator swapping residency on demand. Remove the
`docker-compose.reasoning.yml` overlay dependency and the `WITH_REASONING` build
split from the default path, and reconcile `Makefile`, `.env.example`, `deploy/**`,
and `docs/model_setup.md` so **no BF16 base is required**. Prove it with a full
all-modes GPU smoke; keep `t2i` non-regressed.

## Why This Session Exists

`AM-S2` and `AM-S3` prove each mode runs off quantized-only weights, possibly via
transitional wiring. This session makes "all modes, on by default, one command" the
real, documented posture — the heart of the owner's "simplify the orchestration"
goal (PRD Decision 2). It runs after per-mode verification precisely so it never
enables a mode that does not work (`docs/project_contract.md` §two-pass item 6,
INV-7, R-07).

## In Scope

1. **Unify the FP8 stack to all-modes-by-default.** Fold the reasoning/action
   wiring from `AM-S2`/`AM-S3` into the default `docker-compose.fp8.yml` /
   `docker-compose.base.yml`; `make up-fp8` alone serves all three modes
   (`EV-AM-NO-OVERLAY-DEFAULT`).
2. **Remove the BF16 surface from the default path.** No BF16 base bind-mount in
   the rendered config; the default `api` image builds without `WITH_REASONING=1`;
   retire or clearly demote `up-fp8-reasoning`, `COSMOS3_BASE_DIR`,
   `COSMOS3_REASONER_MODEL_DIR`→BF16, and `COSMOS3_BASE_ACTION_DIR`→BF16 in
   `.env.example`/`Makefile`/`deploy/**` (INV-4, `EV-AM-ZERO-BF16-WIRING`).
3. **Reconcile `docs/model_setup.md`** so the setup contract requires only the
   quantized checkpoint(s) for all modes (dropping the "reasoning/action also need
   the BF16 base" instruction), reflecting the `AM-S2`/`AM-S3` reality and any new
   pinned action-bundled revision (NFR-5). (README prose stays for `AM-S6`.)
4. **Preserve the residency safety net.** The full all-modes deployment honors
   evict-before-load and the VRAM budget; a request for a different mode preempts
   without OOM; if Studio+Reasoning share one resident model, the OOM-free trace is
   recorded (INV-5). Update the `coresidency.py` documented footprints if the
   BF16-reasoner assumption no longer holds (R-08).
5. **Full all-modes GPU smoke** on a single `make up-fp8` (`GPU-AM-ALLMODES-FP8`):
   Studio, Reasoning, and Action each work; on-demand swaps succeed; `t2i`
   non-regressed (`GPU-AM-T2I-NOREGRESS`, INV-2). CPU suite green.

## Out of Scope

- NVFP4 (that is `AM-S5`) — though this session should keep the nvfp4 stack
  buildable/renderable, it is not GPU-verified here.
- `README.md` / `docs/walkthrough.md` prose (that is `AM-S6`).
- Any `diffusers` `t2v` routing (INV-3); any auth/guardrails/network change.
- New public API routes/schema shapes unless explicitly authorized (INV-8).

## Deliverables

- A single `make up-fp8` that serves all three modes off the quantized-only FP8
  checkpoint, with no BF16 base required and the overlay/`WITH_REASONING` default
  split removed.
- `docs/model_setup.md` reconciled to the zero-BF16 all-modes reality.
- `GPU-AM-ALLMODES-FP8` + `GPU-AM-T2I-NOREGRESS` recorded; the rendered
  `docker compose … config` showing no BF16 mount captured as evidence.
- `docs/evidence_map.md` / `docs/risk_register.md` updated (R-07/R-08/R-14); CPU
  suite green.

## Checks

```bash
uv run pytest -m "not gpu"                                   # green
docker compose -f deploy/docker-compose.fp8.yml config       # all-modes wiring; no BF16 mount
rg -n "up-fp8-reasoning|WITH_REASONING|COSMOS3_BASE_DIR" Makefile deploy .env.example
git diff schemas/openapi.json                                # empty unless authorized (INV-8)
# GPU: one `make up-fp8` → Studio + Reasoning + Action all work; swaps OK; t2i non-regressed.
```

## Exit Criteria

- `GATE-AM-S4-ORCHESTRATION` passes: `make up-fp8` = all three modes; overlay +
  `WITH_REASONING` default split removed; `Makefile`/`.env.example`/`deploy/**`/
  `docs/model_setup.md` reconciled to require no BF16; `config` shows no BF16 mount;
  full all-modes FP8 smoke passes; `t2i` non-regressed (INV-2); CPU suite green.
- Only modes that passed their `AM-S2`/`AM-S3` gates are enabled by default (INV-7).

## Handoff

Record for `AM-S5`: the unified FP8 all-modes design (compose/env/orchestrator
shape) as the template to extend to NVFP4; the residency model (swap vs merge) and
its VRAM evidence; the checkpoint revision(s) in use. Record for `AM-S6`: the final
per-mode FP8 verification status to reflect in the README and the setup facts now
that BF16 is gone from the default path.
