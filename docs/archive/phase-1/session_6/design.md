# Session 6 Design - Local-Build Docker and Compose Migration

Date: 2026-07-07
Session: MIG-S6
Risk: high · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S6-DOCKER`

## Context

No `deploy/` tree exists (S5 handoff). The imported code fixes the deployment
contract: the WebUI BFF proxies to `http://api:8000` (`API_INTERNAL_URL`,
`COSMOS3_API_KEY`); the api proxies generation to the `vllm-omni` service
(`http://vllm-omni:8000`) and drives its lifecycle over the Docker socket
(`DockerCliController` → `docker start/stop/inspect cosmos3-nano-webui-vllm-omni`);
the api serves **reasoning** as an in-container `vllm serve` subprocess (torch +
vLLM 0.23.0 + GPU + BF16 base). Generation and reasoning share one GPU, serialized
by the orchestrator. Checkpoints are external (S4 `docs/model_setup.md`); the
vLLM-Omni pin is the immutable `MIG-S2` tag `cosmos3-nano-webui-mig-s2`
(`697035018b70…`). Governing invariants: INV-2 (no baked/committed weights), INV-3
(fork consumed by pinned commit/tag), INV-4 (configurable operator mounts, no
private defaults), INV-1 (no private paths/hosts), INV-9/INV-10 (no API-shape or
repo-dependency change). `api/**` and `webui/**` are **out of blast radius**.

## Goals / Non-Goals

**Goals.** (1) FP8 and NVFP4 Compose stacks that render under a single `-f` with
configurable public mounts and no private paths or baked weights; (2) Dockerfiles
that build local images from public inputs (api lean + webui built here; vLLM-Omni
rendered, build deferred); (3) the vLLM-Omni fork consumed by immutable tag/commit;
(4) local build/up/down/health/smoke/scan commands; (5) exact GPU-smoke commands and
caveats handed to S8.

**Non-Goals.** Registry push; runtime weight auto-download; GPU GitHub Actions;
README rewrite (handoff notes only); any `api/**` / `webui/**` change; proving GPU
inference (S8).

## Decisions

- **D-1 · Three images; api multi-stage lean-default + `WITH_REASONING`.**
  `deploy/api.Dockerfile` builds a torch-free FastAPI + Docker-CLI image by default
  (`python:3.12-slim`, base `dependencies` only, `uvicorn app.main:app`). It fully
  serves the generation surface (generation runs in the vLLM-Omni container). A
  `--build-arg WITH_REASONING=1` selects a CUDA base and installs the `oracle` extra
  + vLLM so the in-container reasoner subprocess works. *Alternative:* always-heavy
  (rejected — slow/fragile `docker build` check, weights-adjacent bulk for a
  generation-only default); *Alternative:* always-lean (rejected — reasoning could
  never run in the shipped stack, understating the surface).
- **D-2 · WebUI standalone runner.** `deploy/webui.Dockerfile` multi-stage on
  `node:22`: install (frozen) → `pnpm build` (uses the committed `schema.d.ts`) →
  copy `.next/standalone` + `.next/static` + `public` into a slim runner, `node
  server.js`. Talks only to `http://api:8000`. CPU-buildable here.
- **D-3 · vLLM-Omni image from the immutable pin.** `deploy/vllm-omni.Dockerfile`
  FROM a CUDA 12.8 base (RTX 5090 / sm_120), installs
  `git+https://github.com/fengwang/vllm-omni.git@cosmos3-nano-webui-mig-s2` (INV-3),
  serves the mounted checkpoint on `:8000`, readiness `/v1/models`. The serve
  entrypoint is parameterized (`command:` + env) because the fork CLI is unverified
  on this host; exact command is an S8-verify item. This image is **not** in the
  deterministic `docker build` checks (heavy/GPU) — it renders in Compose; build +
  run are the S8 gate. *Alternative:* pin by branch (rejected — mutable, violates
  INV-3); *Alternative:* build it here (rejected — multi-GB/GPU, out of S6 scope).
- **D-4 · Compose = shared base + `include:` stacks.**
  `docker-compose.base.yml` defines `webui`, `api`, `vllm-omni` once;
  `docker-compose.fp8.yml` / `.nvfp4.yml` each `include:` it and override only
  `COSMOS3_CHECKPOINT_LABEL` + the vLLM-Omni checkpoint mount. Each renders complete
  under a single `-f` (matches the contract's `-f deploy/docker-compose.fp8.yml
  config`). *Alternative:* two standalone files (rejected — duplication drifts);
  *Alternative:* base + override needing two `-f` (rejected — breaks the single-`-f`
  check command).
- **D-5 · External mounts, repo-relative defaults (INV-4).** vLLM-Omni bind-mounts
  `${COSMOS3_FP8_DIR:-./models/Cosmos3-Nano-FP8-Blockwise}` (NVFP4 analogously) at a
  fixed in-container path; `COSMOS3_MODEL_DIR` points there. Inline `${VAR:-default}`
  makes `config` render cleanly with no unset-var warnings and **no absolute/private
  path** (INV-1). `.env.example` documents overriding to any absolute mount and lists
  the full `COSMOS3_*` surface from `docs/model_setup.md`.
- **D-6 · Confined docker-socket privilege.** The api service bind-mounts
  `/var/run/docker.sock:/var/run/docker.sock` and the image ships the Docker CLI, so
  `DockerCliController` can start/stop the gen container. Access is confined by the
  code (fixed verbs, operator-config name, no shell). Recorded as a risk; socket-
  proxy noted as future hardening. *Alternative:* socket-proxy now (deferred — extra
  service for a local milestone; revisit S7/S8).
- **D-7 · Gen-container lifecycle owned by the orchestrator.** Compose creates the
  `vllm-omni` service with `restart: "no"` and container name
  `cosmos3-nano-webui-vllm-omni`; the api orchestrator does `docker start` on acquire
  and `docker stop` on evict. `api` does **not** `depends_on` vllm-omni health (cold
  start / PTX-JIT can exceed minutes; `COSMOS3_PLANE_READY_TIMEOUT` governs). This
  matches the imported FSM without code change.
- **D-8 · Reasoning as an optional overlay.** `docker-compose.reasoning.yml` adds the
  api GPU reservation + BF16 base mount + `COSMOS3_VLLM_BIN`; used as `-f base -f
  stack -f reasoning`. Keeps the default stacks lean/generation-focused (D-1);
  renders now, GPU runtime is the S8 gate.
- **D-9 · Weight/path safety by construction (INV-2, R-06).** `.dockerignore`
  excludes `.git`, `.venv`, `node_modules`, `.next`, `__pycache__`, `docs`,
  `references`, `models/`, and all `*.safetensors|pt|pth|ckpt` + media globs, so no
  broad `COPY` can bake weights and the build context stays small. Dockerfiles copy
  only the specific source trees they need (`api/`, `schemas/` for api; `webui/` for
  webui) — never `COPY . .` of the repo root.
- **D-10 · GPU device requests render without a GPU.** vLLM-Omni (and the reasoning
  overlay's api) declare
  `deploy.resources.reservations.devices: [{driver: nvidia, count: all,
  capabilities: [gpu]}]`. This is valid Compose that `config` renders on a
  GPU-less box; actual scheduling is a runtime/S8 concern.

## Risks / Trade-offs

- **Heavy api build if `WITH_REASONING=1` on the CPU render box** → the deterministic
  check builds the **default lean** target only; the heavy target is documented and
  its GPU validation is S8. Classify a heavy-build timeout as `ENVIRONMENT`, never a
  code fix.
- **vLLM-Omni serve entrypoint unverified locally** → parameterized `command:`/env +
  explicit S8-verify item; render does not depend on the command being runtime-correct.
- **Docker-socket privilege = root-equivalent on the api container** → confined
  controller + risk row + socket-proxy hardening noted; acceptable for a local
  milestone, flagged for S7/S8.
- **External mount layout vs HF artifact layout (failure mode)** → mount the
  checkpoint **root** dir (self-contained per S4) and set `COSMOS3_MODEL_DIR` to it;
  `.env.example` shows the exact `huggingface-cli download --local-dir` target.
- **Build context too large (failure mode)** → `.dockerignore` (D-9) + narrow COPYs;
  verify context size during implementation.
- **Public base image drift (failure mode)** → pin base images by explicit
  major/minor tag (e.g. `python:3.12-slim`, `node:22-slim`, `nvidia/cuda:12.8.*`);
  digest-pinning noted as an S8 hardening.

## Migration Plan

1. `.dockerignore` + `.env.example` (establish context hygiene + env surface).
2. `webui.Dockerfile`; build it (`docker build -f deploy/webui.Dockerfile`).
3. `api.Dockerfile` (lean default); build it; document the `WITH_REASONING` path.
4. `vllm-omni.Dockerfile` (render-only; consume the pin).
5. `docker-compose.base.yml`, then `.fp8.yml` / `.nvfp4.yml` (via `include:`), then
   the reasoning overlay; render each after writing.
6. `Makefile` targets wrapping the above.
7. Full deterministic checks → classify failures → sharded review → adversarial
   verification → handoff + eval seeds.

Rollback: all additions are isolated new files under `deploy/`, plus root
`.dockerignore`/`.env.example`/`Makefile`; reverting removes the deployment surface
without touching runtime source, schemas, or CI.

## Open Questions

- **Exact vLLM-Omni serve command / port flag.** Unverified on this host (fork CLI).
  Parameterized now; S8 confirms and updates `command:`/`.env.example`.
- **api liveness while the orchestrator stops vllm-omni.** Compose `restart: "no"` +
  no health-`depends_on` is the plan; S8 confirms the evict/reload dance under load.
- **Digest-pinning base images.** Deferred to S8 release hardening (with CI action
  SHA-pinning already flagged in the S5 handoff).
