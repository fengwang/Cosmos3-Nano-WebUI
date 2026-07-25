# AM-S4 Execution Contract

Date: 2026-07-25. Derived from `session_4_contract.yaml` + the approved `design.md`.
This is the binding pre-implementation contract for the Ralph loop.

## Planned file changes

**Edit**
- `Makefile` — cold-start `up-fp8`/`up-nvfp4`; retire `up-fp8-reasoning` + `REASON`.
- `deploy/api.Dockerfile` — strip `WITH_REASONING` → single lean/torch-free stage.
- `.env.example` — remove `COSMOS3_BASE_DIR`/`COSMOS3_REASONER_MODEL_DIR`/
  `COSMOS3_VLLM_BIN` + legacy-overlay section + BF16 base-download block.
- `deploy/docker-compose.base.yml`, `deploy/docker-compose.fp8.yml` — clarifying
  comments only (no wiring change).
- `api/engines/vllm/coresidency.py` — R-08 footprint comment only (keep `0.85`).
- `docs/model_setup.md` — zero-BF16 all-modes reconciliation.
- `docs/{evidence_map,risk_register,eval_seed_cases,handoff}.md` — at close.

**Delete**
- `deploy/docker-compose.reasoning.yml`.

**Add**
- `tests/deploy/test_fp8_allmodes_wiring.py`,
  `tests/deploy/test_no_legacy_overlay.py`,
  `tests/deploy/test_reasoner_util_matches_contract.py`.
- `docs/session_4/**` (this pack + `sharded_review.md`, `adversarial_verification.md`,
  `evidence/**` as produced).

## Allowed blast radius (from session_4_contract.yaml)

Allowed: `deploy/docker-compose.base.yml`, `deploy/docker-compose.fp8.yml`,
`deploy/docker-compose.reasoning.yml` (delete), `deploy/api.Dockerfile`,
`deploy/vllm-omni.Dockerfile` (only if smoke requires), `Makefile`, `.env.example`,
`api/app/main.py`, `api/orchestrator/**`, `api/engines/**`, `docs/model_setup.md`,
`tests/**`, `docs/session_4/**`, `docs/evidence_map.md`, `docs/risk_register.md`,
`docs/eval_seed_cases.md`, `docs/handoff.md`.

Forbidden: `README.md`, `docs/walkthrough.md`, `docs/images/**`, any `webui/**`
(unless the smoke surfaces a bug, R-12, owner-authorized), `schemas/openapi.json`
(INV-8), `docs/archive/**`, any weight/checkpoint/generated-media file.

Expected actual touch set is narrower than allowed (no `api/app/main.py` or
orchestrator FSM change is anticipated — cold-start needs none).

## First test to write

`tests/deploy/test_no_legacy_overlay.py` — it is **red** against the current tree
(overlay/`WITH_REASONING`/`up-fp8-reasoning`/BF16 env all still present) and turns green
exactly when the deploy unification is complete. It is the tightest spec→test binding
for the core deliverable.

## Checks after each task

- After each edit: the smallest relevant `uv run pytest tests/deploy -q` (or the
  specific unit file).
- After Task 2/3: `docker compose -f deploy/docker-compose.fp8.yml config` (no BF16
  mount) + nvfp4 render.
- After Task 4: full `uv run pytest -m "not gpu"`.
- Gate set (Task 5): `uv run pytest -m "not gpu"`;
  `docker compose -f deploy/docker-compose.fp8.yml config`;
  `rg -n "up-fp8-reasoning|WITH_REASONING|COSMOS3_BASE_DIR" Makefile deploy .env.example`;
  `git diff --exit-code schemas/openapi.json`.

## Review axes (Task 6)

correctness, security, tests, architecture, performance, readability. High risk →
run all; Critical/High findings with concrete evidence are fixed regardless of consensus;
Medium needs 2+ reviewers or strong evidence; Nits optional.

## Adversarial verifier brief

Fresh context; sees only `session_4_contract.yaml`, the diff, and `docs/session_4/**`
evidence — **not** this conversation. Its job: falsify "GATE-AM-S4-ORCHESTRATION is
satisfied". Must probe, at minimum:
1. Does a BF16 mount or `WITH_REASONING=1` survive anywhere in the default `make up-fp8`
   path? (INV-4)
2. Can both heavy containers still co-load at boot? (cold-start correctness)
3. Is `t2i` re-verified after the change, or only asserted? (INV-2)
4. Is any mode enabled-by-default that did not pass its AM-S2/S3 gate? (INV-7)
5. Does `coresidency.py` still document a BF16 reasoner while runtime is quantized? (R-08)
6. Does the rendered config match the runtime (no "removed in docs, needed at runtime")?
7. Did `schemas/openapi.json` change without authorization? (INV-8)

## Done condition (GATE-AM-S4-ORCHESTRATION)

`make up-fp8` serves all three modes off the quantized-only FP8 checkpoint with no BF16
required; overlay + `WITH_REASONING` default split removed; `docker compose … config`
shows no BF16 mount and an all-modes wiring; full all-modes FP8 GPU smoke passes with
correct on-demand swaps (never co-resident, ≤32 GiB); `t2i` non-regressed (INV-2); CPU
suite green; `schemas/openapi.json` unchanged (INV-8); only AM-S2/S3-passed modes are
default-on (INV-7); owner gives the final all-modes/quality confirmation.

## Failure Arbiter

Classify before fixing: BUG / SPEC_GAP / AMBIGUITY / ENVIRONMENT / TEST_BUG. Record any
invocation in `docs/session_4/failure_arbiter.md`. Never patch product code before the
failure has a category.
