# AM-S5 Plan (micro-task, TDD)

Refs: `tasks.md`, `design.md`, `specs/**`, `execution_contract.md`. Prototype (GPU-proven) in
`evidence/fork_prototype_nvfp4/`. Commit points at each clean checkpoint (owner commits, per prior pattern).

## T1 — NVFP4 reasoner patch + image
1. `mkdir deploy/vllm-reasoner/patch-nvfp4`; copy the 3 proven prototype files in (verbatim from
   `evidence/fork_prototype_nvfp4/`): `nvfp4_blockwise_w4a16_vllm.py`, `cosmos3.py`, and the assembled
   `quantization__init__.py` (stock omni `__init__` + the nvfp4 registration block).
2. Write `deploy/vllm-reasoner-nvfp4.Dockerfile` = a near-copy of `deploy/vllm-reasoner.Dockerfile` with:
   same `BASE_IMAGE`/`VLLM_OMNI_REF`; COPY the three `deploy/vllm-reasoner/patch-nvfp4/*` files to the
   vllm site (`.../quantization/nvfp4_blockwise_w4a16_vllm.py`, `.../quantization/__init__.py`,
   `.../models/cosmos3.py`); CMD `vllm serve /models/checkpoint --host 0.0.0.0 --port 8000
   --served-model-name cosmos3-reasoner --max-model-len 8192 --gpu-memory-utilization 0.85
   --quantization nvfp4_blockwise_w4a16` (no `--omni`).
3. Check: `docker build -f deploy/vllm-reasoner-nvfp4.Dockerfile -t cosmos3-nano-vllm-reasoner-nvfp4:local .` (optional GPU-time; the render tests don't need it). `make scan` clean.

## T2 — nvfp4 compose (test-first)
1. RED: write `tests/deploy/test_nvfp4_allmodes_wiring.py` (the execution-contract first test) → fails
   (no reasoner yet).
2. GREEN: add the `vllm-reasoner` service to `deploy/docker-compose.nvfp4.yml` (mirror the FP8 service:
   `build.dockerfile: deploy/vllm-reasoner-nvfp4.Dockerfile`, `image: cosmos3-nano-vllm-reasoner-nvfp4:local`,
   `container_name: cosmos3-nano-webui-vllm-reasoner`, `shm_size`, `restart:"no"`, gpu reservation,
   the `--quantization nvfp4_blockwise_w4a16` command, NVFP4 checkpoint mount) + api env
   `COSMOS3_REASONER_MAX_CONTEXT/OUTPUT: "7680"`.
3. Check: `uv run pytest tests/deploy/test_nvfp4_allmodes_wiring.py -q`; both stacks `config` exit 0.

## T3 — Makefile up-nvfp4
1. RED: add an assertion (in a deploy test or a grep check) that `up-nvfp4` stops `vllm-reasoner`.
2. GREEN: `Makefile` `up-nvfp4` guard-stop → `stop vllm-omni vllm-reasoner`.
3. Check: `make config-nvfp4` renders; the grep/test passes.

## T4 — reasoner context-cap test (extend)
1. Extend `tests/deploy/test_reasoner_context_cap_fits_model_len.py` to parametrize the nvfp4 stack too
   (caps ≤ `--max-model-len` − 512). Check green.

## T5 — .env.example note
1. Add an NVFP4 all-modes note (zero-BF16; reasoner reuses the NVFP4 checkpoint). Check `make config-nvfp4` still renders with `--env-file`.

## T6 — docs/evidence/risk/eval/handoff
1. Update `model_setup.md`, `evidence_map.md` (AM-S5 audit), `risk_register.md` (R-03/R-04), `eval_seed_cases.md`, `handoff.md`.

## Gate
1. Full `uv run pytest -m "not gpu"` green; both-stack `config`; `git diff --exit-code deploy/docker-compose.fp8.yml schemas/openapi.json` clean.
2. Sharded review → fix High/Critical → adversarial verifier.
3. Stage the per-mode NVFP4 matrix for the owner's quality gate.
