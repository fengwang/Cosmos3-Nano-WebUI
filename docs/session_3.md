# Session 3 - Joint Validation on RTX 5090

Contract: `docs/session_3_contract.yaml`
Risk: high
Routing: branch_and_compare

## Objective

With `GPU-S1`'s from-source image and `GPU-S2`'s fixed checkpoints, prove
that a fresh `hf download` at the new revisions loads and generates T2I end
to end with no manual workaround, and attempt a small T2V smoke.

## Why This Session Exists

`GPU-S1` and `GPU-S2` each close their own half of the problem, but the
combined claim — a fresh operator following only the README gets a working,
from-source, publicly-checkpointed deployment — has never been proven
together. This session retires archived risk R-13's "proxy image, not
pinned-commit build" caveat and confirms drift D1
(`docs/archive/phase-1/risk_register.md`) stays resolved after `GPU-S2`'s
fix.

## In Scope

1. Fresh `hf download` of both checkpoints at the new (`GPU-S2`) revisions
   into a clean local directory.
2. Build or pull the `GPU-S1` from-source image if not already cached; run
   it against the freshly downloaded checkpoints.
3. Direct vLLM-Omni T2I generation on the RTX 5090 for FP8 and for NVFP4.
4. Full-stack T2I generation through the api (`X-API-Key` -> job ->
   artifact).
5. Best-effort small T2V smoke on at least one checkpoint (PRD FR-6, SHOULD).
6. Update `docs/model_setup.md`, `docs/release_checklist.md`, and
   `README.md` per-mode markings (for example upgrading "GPU-unverified" to
   "T2I-verified" where warranted) and close out the relevant not-yet-run
   eval cases.

## Out of Scope

- `t2v_audio`, `i2v`, `forward_dynamics`, and `reasoning` validation (PRD
  Non-Goals).
- 720p video (peak VRAM exceeds 32 GB on the target GPU).
- Any Dockerfile or HF-repo change — this session only consumes `GPU-S1` and
  `GPU-S2` output.

## Deliverables

- Recorded evidence (hardware, driver/CUDA context, checkpoint repo and
  revision, vLLM-Omni commit, request shape, artifact metadata, pass/fail)
  for FP8 and NVFP4 T2I, both direct and full-stack.
- A recorded T2V attempt: pass, fail, or explicitly scoped out with a
  reason.
- Updated per-mode markings in `docs/model_setup.md`,
  `docs/release_checklist.md`, and `README.md`.

## Deterministic Checks

```bash
nvidia-smi
hf download wfen/Cosmos3-Nano-FP8-Blockwise --revision <GPU-S2 sha>
hf download wfen/Cosmos3-Nano-NVFP4-Blockwise --revision <GPU-S2 sha>
docker compose -f deploy/docker-compose.fp8.yml up -d
curl -sf http://localhost:8000/v1/models
```

Record every T2I/T2V request with its prompt or fixture name, seed,
dimensions, and resulting artifact path — the same evidence fields as
Phase-1's `EV-MIG-GPU-*` cases
(`docs/archive/phase-1/eval_seed_cases.md`).

## Exit Criteria

- `GATE-GPU-S3-VALIDATION` passes.
- FP8 and NVFP4 T2I are proven end to end (direct and full-stack) on the
  from-source image and freshly downloaded checkpoints.
- The T2V attempt is recorded either way.
- No manual index-removal or LFS-pointer workaround was needed.

## Handoff

Hand off the final evidence bundle to `docs/evidence_map.md` and
`docs/eval_seed_cases.md`; hand off any newly discovered drift to a new risk
row in `docs/risk_register.md`.
