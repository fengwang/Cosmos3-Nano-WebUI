# Session 6 Brainstorming - Local-Build Docker and Compose Migration

Date: 2026-07-07
Session: MIG-S6
Risk: high · Routing: worker_plus_reviewers · Gate: `GATE-MIG-S6-DOCKER`

## Problem

Public users need a repeatable local deployment path, but the first milestone
publishes no Docker images and must never bake model weights into images. Docker
and Compose must therefore be buildable from public code and configurable model
mounts, consume the pinned public vLLM-Omni fork from `MIG-S2`, and render/scan
clean. No `deploy/` tree exists yet (S5 handoff, `EV-MIG-COMPOSE-RENDER`), so this
session is greenfield for deployment assets. Application code is **out of blast
radius** (`api/**`, `webui/**`), so the deployment must honor the runtime contract
as-imported, not adapt code to the deployment.

## Context explored

The imported code already encodes the deployment contract this session must honor:

- **WebUI → API.** `webui/lib/proxy.ts` / `proxyFetch.ts`: a server-side BFF proxy
  reads `API_INTERNAL_URL` (default `http://api:8000`) and injects
  `COSMOS3_API_KEY`. `next.config.mjs` sets `output: "standalone"` → a slim CPU
  server bundle. The browser never talks to the API directly.
- **API → vLLM-Omni container.** `api/engines/vllm_omni/endpoints.py` bakes in the
  Compose contract: service URL `http://vllm-omni:8000` (`COSMOS3_VLLM_OMNI_URL`)
  and container name `cosmos3-nano-webui-vllm-omni` (`COSMOS3_GEN_CONTAINER`),
  checkpoint label `COSMOS3_CHECKPOINT_LABEL` ∈ {`fp8`,`nvfp4`}.
- **API controls that container's lifecycle over the Docker socket.**
  `api/orchestrator/container.py` `DockerCliController` runs `docker start/stop/
  inspect <name>` (fixed argv, operator-config name, never request-derived). So the
  api container needs the Docker CLI + socket access.
- **API reasoning is an in-container `vllm serve` subprocess.**
  `default_worker_factory` (`api/app/main.py`) launches the reasoner as a
  `SubprocessPlaneWorker` (`COSMOS3_VLLM_BIN`, port `COSMOS3_VLLM_PORT=8765`), so
  reasoning needs torch + vLLM (0.23.0) + GPU + the BF16 base mount **inside the api
  image**. Generation and reasoning share the single GPU, serialized by the
  orchestrator (evict-before-load).
- **Checkpoints (S4 `docs/model_setup.md`).** FP8 `wfen/Cosmos3-Nano-FP8-Blockwise`
  and NVFP4 `wfen/Cosmos3-Nano-NVFP4-Blockwise` (pinned revisions, `openmdw-1.0`);
  BF16 base `nvidia/Cosmos3-Nano` for reasoning/action. Env: `COSMOS3_MODEL_DIR`,
  `COSMOS3_CHECKPOINT_LABEL`, `COSMOS3_REASONER_MODEL_DIR`, `COSMOS3_BASE_ACTION_DIR`.
  Drift **D1**: the in-process `diffusers_*` engines cannot load the current public
  checkpoints; the **default** generation engine is `vllm_omni` (a container), whose
  real serving is an `S6`/`S8` gate.
- **vLLM-Omni pin (S2).** Branch `mig-s2-cosmos3-quant-pin` and tag
  `cosmos3-nano-webui-mig-s2` on `git@github.com:fengwang/vllm-omni.git`, commit
  `697035018b70cef76b974a909d23371a9984c3f2`. Install:
  `pip install "git+https://github.com/fengwang/vllm-omni.git@cosmos3-nano-webui-mig-s2"`.
- **Local environment.** Docker 29.6.1, Compose 5.1.4 (`include:`/profiles OK),
  NVIDIA runtime present + RTX 5090 (driver 610.43.02). Renders, scans, and
  CPU-scale builds are runnable here; GPU inference remains the S8 gate.

> Note: `session_N/specs/*.md` and `R-15`/`D-1` mentions inside the code comments
> use the **original private project's** numbering (breadcrumbs preserved by the
> curated import), not this migration's `MIG-S{n}`. The authoritative contract is
> the code itself, cross-checked against `docs/model_setup.md`.

## Approaches considered (the four forks + resolution)

### Fork A — API image weight vs. reasoning support
The api image must control the gen container (docker CLI + socket) and, to serve
**reasoning**, also carry torch + vLLM + GPU + the BF16 base mount.
- **A1 Full runtime image** — always heavy (torch cu128 + vLLM 0.23.0 + oracle +
  docker CLI). Full surface out of the box; multi-GB build.
- **A2 Lean generation-only** — always torch-free; fast build; reasoning simply
  cannot run in the shipped stack.
- **A3 Lean default + `WITH_REASONING` build ARG** — default torch-free (full
  *generation* surface via the vLLM-Omni container, fast CPU build that satisfies
  the deterministic `docker build` check); opt-in ARG adds the CUDA+vLLM layer for
  in-container reasoning, validated at the S8 GPU gate.
- **DECISION → A3.** Best fit for "local build first milestone": the required
  `docker build -f deploy/api.Dockerfile` check passes fast and honestly, the
  generation surface is complete, and reasoning is a documented, renderable opt-in
  rather than a silent omission.

### Fork B — Docker access for gen-container control
- **B1 Raw `/var/run/docker.sock` bind-mount** (+ docker CLI in the image).
- **B2 `tecnativa/docker-socket-proxy`** exposing only start/stop/inspect.
- **DECISION → B1 (confined).** Matches the code's accepted design and is simplest
  for a local milestone; the `DockerCliController` is already fixed-argv /
  operator-config-name confined. The privilege is recorded as a risk row; the
  socket-proxy is noted as a future hardening (candidate for S7/S8).

### Fork C — Checkpoint mount default convention
- **C1 Repo-relative `./models/<Repo>`** — self-contained, obvious placeholder,
  git-ignored.
- **C2 Absolute `/data/models/<Repo>`** — matches `model_setup.md`/`ENVIRONMENTS.md`.
- **C3 `/path/to/<Repo>`** — clearly non-real; must be overridden before `up`.
- **DECISION → C1.** No absolute paths in the rendered config (strongest
  private-path posture), and it is directly runnable once the operator downloads
  weights into `./models/`. `.env.example` documents overriding to any absolute
  mount.

### Fork D — GPU smoke scope this session
- **D1 Render + build + scans; defer GPU inference to S8.**
- **D2 Also attempt real GPU smoke now** (download FP8, heavy build, run t2i/t2v).
- **DECISION → D1.** GPU inference is formally the S8 gate; S6 delivers renderable/
  buildable/scannable assets and hands S8 exact smoke commands. Avoids multi-GB
  downloads + long heavy builds while keeping S6 focused. The RTX 5090's presence is
  recorded so S8 can execute here.

## Secondary decisions (recommended, presented and approved)

- **Compose structure.** A shared `deploy/docker-compose.base.yml` (webui + api +
  vllm-omni skeleton) plus thin `deploy/docker-compose.fp8.yml` and `.nvfp4.yml`
  that `include:` the base and set only the two differing values
  (`COSMOS3_CHECKPOINT_LABEL` + the checkpoint mount). Each renders standalone under
  a single `-f`, matching the contract's check commands exactly, with minimal
  duplication.
- **Gen-container lifecycle.** Compose creates/starts `vllm-omni` with
  `restart: "no"`; the api orchestrator owns start/stop thereafter. `api` does not
  hard-depend on vllm-omni health (cold start can be long; the orchestrator's
  `COSMOS3_PLANE_READY_TIMEOUT` governs readiness).
- **Reasoning overlay.** `deploy/docker-compose.reasoning.yml` — a small, clearly
  marked optional overlay adding the api GPU reservation + BF16 base mount +
  `COSMOS3_VLLM_BIN`. It renders now; its GPU runtime is the S8 gate. (Owner
  approved including it.)
- **Ports.** `webui` `${WEBUI_PORT:-3000}:3000`; `api` `${API_PORT:-8000}:8000`
  (health/smoke); `vllm-omni` internal-only.
- **Context hygiene.** `.dockerignore` excludes `.git`, `.venv`, `node_modules`,
  `.next`, `__pycache__`, `docs`, `references`, `models/`, and all weight/media
  globs → small context + impossible to bake weights (R-06).

## Validated design (approved 2026-07-07)

Three Dockerfiles (`deploy/{webui,api,vllm-omni}.Dockerfile`); a shared compose base
with FP8/NVFP4 stacks via `include:` and an optional reasoning overlay; `.dockerignore`,
`.env.example`, and a `Makefile` for build/up/down/health/smoke/scan. Weights are
external repo-relative mounts; the vLLM-Omni fork is consumed by immutable tag/commit;
the api reaches the daemon via a confined docker socket. Deterministic gate = FP8+NVFP4
`compose config` render + private-ref + weight-copy scans + api/webui `docker build`;
the vLLM-Omni image build and all GPU inference are the documented S8 gate.

Done condition: `GATE-MIG-S6-DOCKER` passes with local-build Compose ready for README
documentation (S7) and exact GPU-smoke commands handed to S8.
