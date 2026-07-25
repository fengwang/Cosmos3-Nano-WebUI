# AM-S4 Tasks

Coarse, dependency-ordered checklist. Each maps to spec requirements; micro-steps
(test-first) are in `plan.md`. Commit at each group's clean checkpoint.

## 1. Deterministic wiring tests (test-first, red)

- [ ] 1.1 Add `tests/deploy/test_fp8_allmodes_wiring.py`: assert (parsing
  `base.yml`+`fp8.yml`) both `vllm-omni` and `vllm-reasoner` present; both mount the FP8
  checkpoint; **no** `/models/base` target and no `Cosmos3-Nano` (non-quantized) source.
  (spec: unified-fp8-allmodes-stack)
- [ ] 1.2 Add `tests/deploy/test_no_legacy_overlay.py`: assert
  `deploy/docker-compose.reasoning.yml` is absent; `WITH_REASONING` absent from
  `api.Dockerfile`; `up-fp8-reasoning` absent from `Makefile`; BF16 env absent from
  `.env.example`. (spec: unified-fp8-allmodes-stack REMOVED reqs)
- [ ] 1.3 Add `tests/deploy/test_reasoner_util_matches_contract.py`: parse the
  `vllm-reasoner` compose command's `--gpu-memory-utilization` and assert it equals
  `CoResidencyContract().gpu_memory_utilization`. (spec: cold-start-residency-lifecycle
  MODIFIED)
- [ ] 1.4 Confirm 1.1–1.3 **fail** against the current tree (red baseline), for the
  right reasons.

## 2. Deploy surface unification (make them green)

- [ ] 2.1 Cold-start `up-fp8` (and mirror `up-nvfp4`) in `Makefile`; retire
  `up-fp8-reasoning`, the `REASON` var, and help/`.PHONY` refs.
  (spec: cold-start-residency-lifecycle ADDED)
- [ ] 2.2 Delete `deploy/docker-compose.reasoning.yml`.
- [ ] 2.3 Strip `WITH_REASONING` from `deploy/api.Dockerfile` (ARG, CUDA `base-1` stage,
  if/else) → lean/torch-free image.
- [ ] 2.4 Remove `COSMOS3_BASE_DIR`/`COSMOS3_REASONER_MODEL_DIR`/`COSMOS3_VLLM_BIN` + the
  legacy-overlay section + the BF16 base-download block from `.env.example`.
- [ ] 2.5 Clarifying comments in `base.yml`/`fp8.yml` (cold-start ownership); no wiring
  change.

## 3. Coresidency reconciliation (R-08)

- [ ] 3.1 Update the `api/engines/vllm/coresidency.py` footprint comment: FP8
  reasoner, KV-cache-dominated at 0.85 util (not ~16 GiB BF16). Keep the `0.85`
  constant. (spec: cold-start-residency-lifecycle MODIFIED)

## 4. Docs reconciliation

- [ ] 4.1 `docs/model_setup.md`: checkpoint table (BF16 base → legacy/dormant), env
  table (BF16 vars → legacy), mount layout (drop base from default), per-mode matrix
  (reasoning → FP8 container GPU-verified AM-S2; action already AM-S3), operator-setup
  steps (quantized-only). (spec: zero-bf16-setup-contract)

## 5. Verification (host-runnable)

- [ ] 5.1 `uv run pytest -m "not gpu"` green (incl. new `tests/deploy/`).
- [ ] 5.2 `docker compose -f deploy/docker-compose.fp8.yml config` → all-modes, no BF16
  mount; `docker compose -f deploy/docker-compose.nvfp4.yml config` renders.
- [ ] 5.3 `rg -n "up-fp8-reasoning|WITH_REASONING|COSMOS3_BASE_DIR"
  Makefile deploy .env.example` → only intended residue (ideally none).
- [ ] 5.4 `git diff --exit-code schemas/openapi.json` → clean (INV-8).

## 6. Review + adversarial verification

- [ ] 6.1 Sharded review (correctness/security/tests/architecture/performance/
  readability); dedupe; fix High/Critical only; re-check. → `sharded_review.md`.
- [ ] 6.2 Fresh-context adversarial verifier (contract+diff+evidence only) to falsify
  the done condition. → `adversarial_verification.md`.

## 7. GPU all-modes smoke + owner gate

- [ ] 7.1 `make down && make build && make up-fp8`; confirm cold start (only api+webui).
- [ ] 7.2 Smoke: Studio `t2i` (INV-2 baseline) → Action (agibotworld policy/FD; av ID)
  → Reasoning (`/v1/reason`, swap) → Studio again (swap back). Capture per-step peak
  VRAM (≤32 GiB, never co-resident), evict/load logs, rendered `config`.
- [ ] 7.3 Record `GPU-AM-ALLMODES-FP8` + `GPU-AM-T2I-NOREGRESS`; owner final
  all-modes/quality confirmation (`GATE-AM-S4-ORCHESTRATION` human gate).

## 8. Close-out

- [ ] 8.1 `docs/evidence_map.md` (AM-S4 audit), `docs/risk_register.md` (R-07/R-08/R-14),
  `docs/eval_seed_cases.md`, `docs/handoff.md`.
- [ ] 8.2 Verify done condition; state residual risks + AM-S5 warnings (deep dead-code
  removal, nvfp4 reasoner service, fork pin).
