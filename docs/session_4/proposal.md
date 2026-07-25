# AM-S4 Proposal — Orchestration Simplification + Default-On (FP8)

Date: 2026-07-25
Extracted from: `docs/session_4/brainstorming.md` (owner-approved design, 2026-07-25).

## 1. Motivation

AM-S2/S3 proved reasoning and action run off the quantized-only FP8 checkpoint and
already fold their wiring into `docker-compose.base.yml`/`fp8.yml`. But the deploy
surface still ships (a) a latent **boot co-load OOM** — `docker compose up -d` starts
both heavy containers at once — and (b) a **legacy BF16 subprocess-reasoning surface**
(`docker-compose.reasoning.yml`, the `WITH_REASONING` build split, `up-fp8-reasoning`,
BF16 env) that contradicts the zero-BF16 posture. AM-S4 makes "all modes, on by
default, one command" the real, honest posture by making `make up-fp8` cold-start the
heavy planes (orchestrator-owned, never co-resident) and by deleting the legacy BF16
surface, then proving it with a full all-modes GPU smoke.

## 2. Specific changes agreed

1. **Cold-start `make up-fp8`** (and mirror `up-nvfp4`): `up -d --no-start` → idempotent
   `stop vllm-omni vllm-reasoner` → `start api webui`. Only api+webui run at boot; the
   orchestrator starts a heavy plane on first request and evict-before-loads on swap.
   The orchestrator/FSM code is unchanged.
2. **Delete the legacy BF16 surface:** remove `deploy/docker-compose.reasoning.yml`;
   strip `WITH_REASONING` (ARG, CUDA `base-1` stage, if/else) from `deploy/api.Dockerfile`
   so the api image is purely lean/torch-free; remove `up-fp8-reasoning` + the `REASON`
   var from `Makefile`; remove `COSMOS3_BASE_DIR`/`COSMOS3_REASONER_MODEL_DIR`/
   `COSMOS3_VLLM_BIN` + the legacy-overlay section + the BF16 base-download block from
   `.env.example`.
3. **Coresidency R-08 reconciliation:** update the stale `coresidency.py` comment (the
   ~26 GiB is an FP8 reasoner, KV-cache-dominated at 0.85 util — not ~16 GiB BF16
   weights); keep the `0.85` constant (matches the live compose reasoner command).
4. **Deterministic zero-BF16 wiring tests** (pure-file, no docker/GPU): assert no BF16
   mount in `base.yml`+`fp8.yml`; both `vllm-omni` and `vllm-reasoner` present; the
   reasoner's `--gpu-memory-utilization` equals the coresidency contract; `reasoning.yml`
   absent.
5. **Reconcile `docs/model_setup.md`** to require only the quantized checkpoint(s) for
   all modes; demote the BF16 base to legacy/dormant; reasoning row → FP8 reasoner
   container, GPU-verified FP8 (AM-S2).
6. **Docs/evidence/risk updates + handoff** at close; **full all-modes FP8 GPU smoke**
   (agent-driven) + owner confirmation.

## 3. Capabilities

Each capability below gets a spec file under `docs/session_4/specs/`. Every listed
requirement is realized by deterministic checks and/or the GPU smoke.

### New capabilities
- **cold-start-residency-lifecycle** — `make up-fp8` brings up all three modes with the
  heavy planes created-but-stopped and orchestrator-owned; a mode swap evicts-before-loads;
  the two heavy planes never co-reside. (Spec: `specs/cold-start-residency-lifecycle.md`.)

### Modified capabilities
- **unified-fp8-allmodes-stack** — the FP8 deploy surface is a single all-modes,
  zero-BF16 stack: `make up-fp8` == all modes; `reasoning.yml`/`WITH_REASONING`/
  `up-fp8-reasoning`/BF16 env removed; `config` has no BF16 mount; nvfp4 stays
  renderable. (Spec: `specs/unified-fp8-allmodes-stack.md`.)
- **zero-bf16-setup-contract** — `docs/model_setup.md` requires only the quantized
  checkpoint(s) for every default mode; the BF16 base is legacy/dormant-only. (Spec:
  `specs/zero-bf16-setup-contract.md`.)

## 4. Impact

- **Deploy:** `deploy/docker-compose.base.yml` (comment/clarify), `docker-compose.fp8.yml`
  (comment), delete `docker-compose.reasoning.yml`, `api.Dockerfile` (strip
  `WITH_REASONING`), `Makefile` (cold-start + retire `up-fp8-reasoning`),
  `.env.example` (drop BF16 env).
- **Code:** `api/engines/vllm/coresidency.py` (R-08 comment only). No orchestrator FSM
  change; **no** public-API/route/schema change (INV-8). The dormant `diffusers_action`
  graft (R-11) and the dead BF16-subprocess-reasoning Python are untouched (deferred).
- **Tests:** add `tests/deploy/` wiring tests; no existing test should break (the
  deleted deploy artifacts are not referenced by any test — verified by `rg`).
- **Docs:** `docs/model_setup.md`; `docs/session_4/**`; `docs/{evidence_map,risk_register,
  eval_seed_cases,handoff}.md`.
- **Dependencies:** none added/removed. The api image *drops* its optional CUDA/torch
  build variant (net simplification).
- **Deferred (surfaced, not hidden):** deep dead-code removal (AM-S5), public fork pin
  (NFR-5 follow-up), nvfp4 reasoner service (AM-S5).
