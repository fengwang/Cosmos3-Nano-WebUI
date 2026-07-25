# AM-S2 Execution Contract (as executed)

Date: 2026-07-25 · Session: AM-S2 · Gate: `GATE-AM-S2-REASONING` = **PASS**.

## Blast radius (allowed) — with the owner-authorized amendment
- Repo (per `session_2_contract.yaml`): `api/app/main.py`, `api/app/routes/reasoning.py`,
  `api/orchestrator/planes.py`, `deploy/docker-compose.base.yml`, `deploy/docker-compose.fp8.yml`,
  `deploy/vllm-reasoner.Dockerfile` (new), `deploy/vllm-reasoner/patch/**` (new), `.env.example`,
  `tests/**`, `docs/session_2/**`, `docs/{evidence_map,risk_register,eval_seed_cases,handoff}.md`.
- **Amendment (owner, 2026-07-25):** blast radius extended into the **`fengwang/vllm` fork**
  (`fp8_blockwise_w8a16_vllm.py`, `quantization/__init__.py`, `models/cosmos3.py`) — an authorized
  additional work area for the minimal quant patch. INV-4 hardened to absolute (no BF16 exception).
- Not touched (forbidden): `README.md`, `docs/walkthrough.md`, `webui/**`, `diffusers_action/**`,
  `api/app/routes/action.py`, `docker-compose.nvfp4.yml`, `schemas/openapi.json`, `docs/archive/**`,
  weights/media.

## Planned → executed changes
1. Prove zero-BF16 FP8 text (spike, pre-registered rubric) → P1/P2. ✓
2. Fork: register `--quantization fp8_blockwise_w8a16` + `cosmos3.py` mapper fix. ✓
3. Repo: reasoner container plane (`container_reasoning_spec`, factory branch, route repoint). ✓
4. Deploy: `vllm-reasoner` service + Dockerfile + patch + `.env.example`; no BF16 on the path. ✓
5. Reproducible image built + GPU-verified (P2); `t2i` non-regression (P3). ✓
6. Tests updated/added; docs; review gates; handoff. ✓

## First test (spec-derived)
`tests/api/test_reasoner_container_wiring.py::test_container_reasoning_spec_is_reasoning_http_probe`
— the factory/spec must build a REASONING **container** plane (HTTP `/v1/models` probe, empty argv),
not a subprocess (guards the contract's "stub reasoner" adversarial case).

## Checks (all green)
- `uv run pytest -m "not gpu"` → **527 passed**.
- `docker compose -f deploy/docker-compose.fp8.yml config` → renders; **no BF16 mount**; `vllm-reasoner` present.
- `git diff --exit-code schemas/openapi.json` → clean (INV-8).
- GPU: `GPU-AM-REASON-FP8` (P2, reproducible image) + `GPU-AM-T2I-NOREGRESS` (P3) + `OWNER-AM-REASON-QUALITY` PASS.

## Review axes run
correctness, tests, architecture, security, performance, readability (2 fresh-context subagents) →
`sharded_review.md`. Adversarial verifier (fresh context) → `adversarial_verification.md` = PASS.

## Adversarial verifier brief (used)
Falsify: verified-without-owner-PASS; BF16/overlay/`WITH_REASONING` still on the path; t2i regressed /
not re-run; plane-merge without a VRAM trace; stub-reasoner test. All refuted; INV-1/2/3/4/5/6/8 verified.

## Done condition (met)
`GATE-AM-S2-REASONING`: reasoning e2e on FP8 off the quantized-only checkpoint (zero BF16) ✓; `t2i`
non-regressed ✓; CPU green ✓; owner reasoning-quality PASS ✓; no BF16 base/overlay/`WITH_REASONING`
on the reasoning path ✓; residency safety net ✓; API shape unchanged ✓.
