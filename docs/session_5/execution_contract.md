# AM-S5 Execution Contract

Date: 2026-07-26 · Contract: `docs/session_5_contract.yaml` (authority). Risk: high.

## Planned file changes
- **New:** `deploy/vllm-reasoner-nvfp4.Dockerfile`; `deploy/vllm-reasoner/patch-nvfp4/{nvfp4_blockwise_w4a16_vllm,cosmos3,quantization__init__}.py`; `tests/deploy/test_nvfp4_allmodes_wiring.py` (+ maybe `test_up_nvfp4_stops_reasoner.py`).
- **Edit:** `deploy/docker-compose.nvfp4.yml` (add `vllm-reasoner` service + api reasoner caps); `Makefile` (`up-nvfp4` stop reasoner); `.env.example` (nvfp4 note); `tests/deploy/test_reasoner_context_cap_fits_model_len.py` (extend to nvfp4); `docs/{model_setup,evidence_map,risk_register,eval_seed_cases,handoff}.md`; `docs/session_5/**`.

## Allowed blast radius (from `session_5_contract.yaml`)
`deploy/docker-compose.nvfp4.yml`, `deploy/docker-compose.base.yml` (only if NVFP4-conditional shared wiring is truly needed — prefer NOT), `.env.example`, `deploy/vllm-reasoner*` (new nvfp4 image/patch), `Makefile` (bring-up only), `tests/**`, `docs/session_5/**`, `docs/{model_setup,evidence_map,risk_register,eval_seed_cases,handoff}.md`.
**Forbidden (block on touch):** `deploy/docker-compose.fp8.yml`, `schemas/openapi.json`, `webui/**`, `README.md`, `docs/walkthrough.md`, `docs/archive/**`, any weight/checkpoint/media binary, api/orchestrator Python (unless an NVFP4-specific serving bug forces it — none expected; stop + record if so).

## First test to write (failing → passing)
`tests/deploy/test_nvfp4_allmodes_wiring.py::test_nvfp4_config_has_reasoner_and_no_bf16` — render `docker compose -f deploy/docker-compose.nvfp4.yml config`; assert a `vllm-reasoner` service exists with `nvfp4_blockwise_w4a16` in its command, only the NVFP4 checkpoint model-mount, and no BF16 base path; and the omni command has NO `--enable-layerwise-offload`. (Red before 2.1, green after.)

## Checks after each task
- After any deploy edit: `docker compose -f deploy/docker-compose.nvfp4.yml config` AND `-f deploy/docker-compose.fp8.yml config` both exit 0 (FP8 non-regress).
- After each test add: `uv run pytest tests/deploy -q`.
- Continuous: `git diff --exit-code deploy/docker-compose.fp8.yml schemas/openapi.json` clean.
- Before close: full `uv run pytest -m "not gpu"` green.

## Review axes (sharded, risk high)
correctness · security · tests · architecture · performance · readability. Dedup; Critical/High need only strong evidence; Medium needs 2+ reviewers or strong evidence.

## Adversarial verifier brief
Fresh context, sees only `session_5_contract.yaml` + the diff + evidence. Try to falsify GATE-AM-S5-NVFP4:
(a) does the nvfp4 render actually include the reasoner + no BF16, or is it a mirage? (b) did any edit touch/regress the FP8 stack (forbidden)? (c) is `openapi.json` unchanged? (d) is any mode enabled-by-default without a recorded NVFP4 run + the owner gate (INV-6/INV-7)? (e) does the NVFP4 omni still forbid offload? (f) does the reasoner path carry any BF16?

## Done condition (GATE-AM-S5-NVFP4)
The AM-S4 design is applied to NVFP4; each mode is GPU-probed on NVFP4 (recorded, `evidence/P1`–`P2`) and staged for the owner's quality PASS (or a recorded owner-decided limitation — none needed technically); `t2i` (NVFP4) non-regressed (INV-2); no BF16 on the NVFP4 default path (INV-4); CPU suite green; `openapi.json` unchanged (INV-8); FP8 stack unchanged. Default-on applies only to owner-passed modes (INV-6/INV-7).
