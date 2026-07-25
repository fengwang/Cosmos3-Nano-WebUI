# AM-S4 Brainstorming — Orchestration Simplification + Default-On (FP8)

Date: 2026-07-25
Owner: Feng
Session: AM-S4 (high risk). Inputs: `docs/prd.md`, `docs/project_contract.md`,
`docs/session_4.md` + `docs/session_4_contract.yaml`, `docs/evidence_map.md`,
`docs/risk_register.md`, `docs/handoff.md` (AM-S3 close).

## 1. Context (as discovered, not assumed)

AM-S2 and AM-S3 already did the *wiring*:

- Reasoning is a **separate `vllm-reasoner` container** (`ContainerPlaneWorker`,
  `Plane.REASONING`) serving TEXT off the **same quantized FP8 checkpoint** via a
  vLLM-fork `--quantization fp8_blockwise_w8a16` (zero BF16). It is already declared
  in `deploy/docker-compose.fp8.yml` and built by `make up-fp8`
  (`deploy/vllm-reasoner.Dockerfile` + a reproducible 3-file COPY-patch under
  `deploy/vllm-reasoner/patch/`).
- Action rides the **same resident omni model** (`Plane.GENERATION`, Studio+Action
  plane-merge) via the video-API `action_mode`; no new plane, no BF16.
- The orchestrator already owns container start/stop through `DockerCliController`
  (`docker start|stop <fixed-name>`), and the single-slot FSM
  (`manager.py`/`residency.py`) evicts-before-loads.

So `docker-compose.base.yml` + `fp8.yml` are **already an all-modes, zero-BF16
wiring** (`config` shows only the FP8 checkpoint mount).

### The real crux — a latent boot co-load hazard

`restart: "no"` governs only *auto-restart*; it does **not** stop
`docker compose up -d` from *starting* a service. So today `make up-fp8`
(`docker compose … up -d`) would start **all four** containers, co-loading
`vllm-omni` (~14.7 GiB) **and** `vllm-reasoner` (~26 GiB) → **OOM on the 32 GiB
5090**. The orchestrator boots with a *cold slot* and never stops
compose-started containers, so it cannot rescue this. This is exactly the residual
the AM-S3 handoff flagged ("the orchestrator must own their start/stop so they
never co-load"). Fixing boot lifecycle is the heart of AM-S4.

**Net:** AM-S4 = (1) fix boot lifecycle so `make up-fp8` never co-loads,
(2) delete the legacy BF16 surface, (3) reconcile `docs/model_setup.md`,
(4) full all-modes GPU smoke. **Not** net-new wiring.

## 2. Confirmed intent (interview-me, owner-confirmed 2026-07-25)

- **Outcome:** one `make up-fp8` brings up Studio + Reasoning + Action off the
  quantized-only FP8 checkpoint; the orchestrator swaps the two heavy planes so they
  never co-load/OOM.
- **Success:** `make up-fp8` **cold-starts** (only api+webui run; heavy containers
  created-but-stopped; orchestrator starts each on first request, evict-before-load on
  swap); full all-modes GPU smoke passes with correct swaps; `t2i` non-regressed; CPU
  suite green; `config` shows no BF16 mount; legacy BF16 surface deleted;
  `model_setup.md` reconciled.
- **Constraints:** INV-2/4/5/7/8; blast radius only; no diffusers `t2v`; keep nvfp4
  renderable; keep the reproducible COPY-patch (defer public fork pin);
  `schemas/openapi.json` unchanged.
- **Out of scope:** NVFP4 GPU-verify (AM-S5); README/walkthrough (AM-S6); webui
  (unless the smoke surfaces a bug); auth/guardrails/network.

## 3. Approaches considered + decisions

### Boot-lifecycle mechanism → **A (chosen)**

- **A. `up --no-start` + idempotent guard-stop + start light services.** Zero
  orchestrator code change (its cold-slot model already fits); robust across re-runs;
  compose service names.
  ```makefile
  up-fp8:
  > $(COMPOSE) $(FP8) up -d --no-start
  > $(COMPOSE) $(FP8) stop vllm-omni vllm-reasoner
  > $(COMPOSE) $(FP8) start api webui
  ```
- B. Compose `profiles` on heavy services — profiled services aren't *created* by
  `up`, so `docker start <name>` fails; needs an extra `create`. Rejected.
- C. Orchestrator stops both heavy containers at api-startup — leaves a boot-time
  co-load race. Rejected.

Owner picked **A (cold-start)** over pre-warming generation: simpler, no new failure
surface, aligned with "orchestrator owns start/stop". Trade: first request of any
mode pays a one-time model load (~30–90 s); idle keep-warm (30 min) amortizes within a
session.

### Cleanup depth → **A (chosen)**

- **A. Deploy-level delete + minimal Python.** Delete the *deploy* legacy
  (`reasoning.yml`, `WITH_REASONING`, `up-fp8-reasoning`, BF16 env); touch Python only
  for the R-08 coresidency comment + new wiring tests. Leave the deeper dead
  BF16-*subprocess*-reasoning code (`reasoning_spec`/`ReasonerConfig`/
  `server_launch_argv`/`build_reasoner`) — it anchors the coresidency VRAM contract +
  edge tokenizer and belongs to AM-S2's serving-path; removing it cascades into ~5
  test files (R-14 blast-radius-bleed). Surfaced as an explicit AM-S5 follow-up.
- B. Deep clean too — cleaner end-state, materially more churn/risk, steals AM-S2 work.

Owner-approved deletions were exactly the deploy-level set → **A**. Deep clean is a
documented, not hidden, deferral.

### Fork pin → keep reproducible COPY-patch, defer public pin (owner default kept).
### GPU smoke → agent drives; owner gives the final all-modes/quality confirmation.

## 4. Validated design (summary)

§1 Boot lifecycle (cold-start, orchestrator unchanged). §2 Delete legacy BF16 surface
(`reasoning.yml`, `WITH_REASONING`, `up-fp8-reasoning`, BF16 env; api image → lean
torch-free). §3 Coresidency R-08 comment + deterministic wiring tests (no BF16 mount;
all-modes services; reasoner `--gpu-memory-utilization` == contract). §4 Reconcile
`model_setup.md` to zero-BF16 all-modes. §5 nvfp4 stays renderable; nvfp4 reasoning
errors honestly (AM-S5). §6 GPU all-modes smoke (Studio→Action→Reasoning swap→Studio;
peak VRAM ≤ 32 GiB, never co-resident; `t2i` non-regress). §7 Risks: cold-start
latency (accepted), stale-running-container (guard-stop), deep dead code (deferred),
nvfp4 reasoning gap (honest), config↔runtime drift (closed by §3 test).

Full architecture/rationale: `design.md`. Testable requirements: `specs/`.

## 5. Explicitly deferred (out of AM-S4)

- NVFP4 GPU-verify + nvfp4 reasoner service (AM-S5).
- Deep removal of the dead BF16-subprocess-reasoning Python (AM-S5 follow-up).
- Public `fengwang/vllm` fork pin (keep the reproducible COPY-patch; NFR-5 follow-up).
- README "See it in action" + `docs/walkthrough.md` (AM-S6).
