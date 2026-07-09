# Session 1 - Public-Source vLLM-Omni Dockerfile Build

Contract: `docs/session_1_contract.yaml`
Risk: high
Routing: branch_and_compare

## Objective

Make `deploy/vllm-omni.Dockerfile` build a working vLLM-Omni image from public
inputs only, replacing the broken recipe with one based on the fork's
`docker/Dockerfile.cuda` pattern.

## Why This Session Exists

The post-GO GPU gate proved T2I generation works, but only through a
prebuilt local image. The public Dockerfile itself is broken:
`pip install --break-system-packages` is unsupported by the base image's pip
22.0 (Ubuntu 22.04), the `-runtime` CUDA base has no build toolchain, and the
`CMD` invokes the wrong entrypoint. An operator cloning the public repo today
cannot build a working image. This session closes that gap and retires the
build half of archived Phase-1 risk R-13
(`docs/archive/phase-1/risk_register.md`).

## In Scope

1. Rework `deploy/vllm-omni.Dockerfile` to `FROM vllm/vllm-openai:<version>`
   (a public base that already ships torch, CUDA, and vLLM), confirming the
   chosen tag supports sm_120 / Blackwell.
2. Install the pinned fork commit
   `697035018b70cef76b974a909d23371a9984c3f2` by immutable commit (for
   example `uv pip install "git+https://github.com/fengwang/vllm-omni.git@697035…"`,
   or `COPY` the pinned checkout followed by `uv pip install .`).
3. Fix the serve entrypoint to
   `vllm serve <model-dir> --omni --host 0.0.0.0 --port 8000` (plus optional
   `--init-timeout` / `--no-guardrails`), either as `CMD` or left to Compose
   `command:` per the current pattern.
4. Confirm `docker compose -f deploy/docker-compose.fp8.yml build vllm-omni`
   builds and `up` serves `/v1/models`.
5. Generate a T2I artifact on the RTX 5090 from the newly built image, using
   at least one of the FP8 or NVFP4 checkpoints (either is acceptable; this
   session does not require both). The checkpoint fix is `GPU-S2`'s job, so
   using the current (pre-fix) HF revision with the already-known local
   workaround (`docs/model_setup.md` §9) is acceptable for this smoke test;
   record that as a known limitation pending `GPU-S2`/`GPU-S3`. That
   workaround is local and non-pushed — it does not touch the `wfen/*`
   Hugging Face repos and is not an "HF checkpoint repo change" for the
   purpose of this session's Out of Scope list.
6. Disposition `deploy/docker-compose.local-image.yml`: drop it, or keep it
   only as an explicitly labeled "reuse a prebuilt image" convenience,
   distinct from the shipped path.
7. Update `docs/release_checklist.md` §6 to reflect the new build result.

## Out of Scope

- No changes to the HF checkpoint repos (`GPU-S2`).
- No changes to WebUI/API source or public API shapes.
- No Docker image publishing or registry work.
- No upstream PR work (`GPU-S4`, `GPU-S5`).

## Deliverables

- A reworked `deploy/vllm-omni.Dockerfile` that builds from public inputs.
- Build, serve, and T2I evidence recorded (exact commands, exit codes,
  artifact metadata).
- A recorded disposition for `deploy/docker-compose.local-image.yml`.
- Updated `docs/release_checklist.md` §6.

## Deterministic Checks

```bash
rtk git status --short --branch
docker compose -f deploy/docker-compose.fp8.yml build vllm-omni
docker compose -f deploy/docker-compose.fp8.yml up -d vllm-omni
curl -sf http://localhost:8000/v1/models
```

Record the actual base image tag, build duration, and any deviation from
this list explicitly; a from-source vLLM build is heavy and iterative.

## Exit Criteria

- `GATE-GPU-S1-DOCKERFILE` passes.
- The image builds from public inputs with no prebuilt cosmos3 image.
- `/v1/models` responds and a T2I artifact is generated on the RTX 5090 for
  at least one of FP8 or NVFP4 (`EV-GPU-S1-BUILD-T2I-SMOKE`).
- `docker-compose.local-image.yml` has a recorded disposition.

## Handoff

Hand off the build recipe, the base-image tag actually used, and any
sm_120-specific findings to `GPU-S3` (joint validation) and to
`docs/release_checklist.md`.
