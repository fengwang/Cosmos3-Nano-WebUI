# Session Handoff

## State Snapshot

- Session: MIG-S6, Local-Build Docker and Compose Migration
- Branch: WebUI repo `session-6` (local commits only; not pushed)
- Last commit at close: `docs(s6): adversarial verification (PASS), evidence/risk/eval updates, handoff`
- Deliverables added (all within the amended `allowed_files`):
  - **Dockerfiles:** `deploy/api.Dockerfile` (lean `python:3.12-slim` + Docker CLI default;
    `--build-arg WITH_REASONING=1` → CUDA 12.8 base + `oracle` extra + `vllm==0.23.0`),
    `deploy/webui.Dockerfile` (`node:22` → Next standalone runner),
    `deploy/vllm-omni.Dockerfile` (CUDA 12.8 + the pinned fork; render-only, build is S8).
  - **Compose:** `deploy/docker-compose.base.yml` + `deploy/docker-compose.fp8.yml` /
    `.nvfp4.yml` (via Compose `include:`) + `deploy/docker-compose.reasoning.yml` (overlay).
  - **Config:** `.dockerignore`, `.env.example`, `Makefile`.
  - **Docs:** `docs/session_6/**` (refining pack + `failure_arbiter.md` (FA-1/FA-2) +
    `sharded_review.md` + `adversarial_verification.md`), `docs/evidence_map.md`,
    `docs/risk_register.md` (R-06/R-13 updated, **R-16 added**), `docs/eval_seed_cases.md`,
    `docs/eval_corpus/mig_s6_*.md` (3 seeds), this handoff.
  - **Contract:** `docs/session_6_contract.yaml` (`allowed_files` amendment — **owner review**).
- Environment variables (full surface in `.env.example`; semantics in `docs/model_setup.md`):
  - Wiring (match baked-in code): `API_INTERNAL_URL=http://api:8000`,
    `COSMOS3_VLLM_OMNI_URL=http://vllm-omni:8000`,
    `COSMOS3_GEN_CONTAINER=cosmos3-nano-webui-vllm-omni`, `COSMOS3_GEN_ENGINE=vllm_omni`.
  - Checkpoint: `COSMOS3_CHECKPOINT_LABEL` (fp8|nvfp4), `COSMOS3_MODEL_DIR=/models/checkpoint`
    (in-container), host binds `COSMOS3_FP8_DIR`/`COSMOS3_NVFP4_DIR`/`COSMOS3_BASE_DIR`
    (default `../models/<Repo>` == `<repo>/models/<Repo>`).
  - Reasoning (overlay): `COSMOS3_VLLM_BIN`, `COSMOS3_REASONER_MODEL_DIR=/models/base`.
  - Deploy: `COSMOS3_API_KEY` (empty=auth off), `BIND_ADDR=127.0.0.1`, `WEBUI_PORT=3000`,
    `API_PORT=8000`.
- vLLM-Omni pin (from `MIG-S2`): `git@github.com:fengwang/vllm-omni.git`, tag
  `cosmos3-nano-webui-mig-s2` == **commit `697035018b70cef76b974a909d23371a9984c3f2`**
  (the Dockerfile pins the immutable commit). Install:
  `pip install "git+https://github.com/fengwang/vllm-omni.git@<commit>"`.
- Checks run (host: Docker 29.6.1, Compose 5.1.4, NVIDIA runtime + RTX 5090 present):
  - `docker compose -f deploy/docker-compose.fp8.yml config` and `…nvfp4…` = **exit 0,
    0-byte stderr** (no unset-var warning), 3 services, correct label; reasoning overlay
    renders on a stack.
  - Weight-copy `rg` over `deploy/` = **clean**; `uv run python tests/test_private_ref_scan.py`
    = **clean (0 findings)**; contract private-path `rg` over `deploy .env.example Makefile
    .dockerignore docs/session_6` = **clean**.
  - `docker build -f deploy/api.Dockerfile` (lean) = **exit 0** (258 MB, torch-free, `docker`
    client 28.5.2 present, `import app.main` OK); `docker build -f deploy/webui.Dockerfile`
    = **exit 0** (287 MB, `server.js` + static present).
  - `.env` auto-load, `BIND_ADDR` override, and `COSMOS3_FP8_DIR` override all verified in render.
  - Sharded review (5 axes): C-1/H-1/H-2 + Lows fixed; no unresolved High/Critical.
  - Fresh-context adversarial verifier: **PASS** (reproduced all checks; refuted all 4
    adversarial cases; confirmed the scans have teeth via planted failures).
- Checks NOT run (out of scope / deferred):
  - `deploy/vllm-omni.Dockerfile` build (heavy CUDA/GPU) → `MIG-S8`.
  - All GPU inference (t2v/t2v_audio/i2v/t2i/forward_dynamics/reasoning/jobs-SSE/artifacts)
    → `MIG-S8` manual gates (`EV-MIG-GPU-*`); RTX 5090 is present here for S8 to use.
  - The GitHub-hosted Actions run (no push); no CI job guards `deploy/` yet (see T-1).
- Current status: **`GATE-MIG-S6-DOCKER` is satisfied.** Local-build Compose renders clean
  with external configurable mounts, no private paths, no baked weights; the fork is pinned
  by immutable commit; api + webui build from public inputs; GPU is a recorded S8 gate.

## Narrative Context

S6 was greenfield for deployment (`deploy/` did not exist). The imported code fixes the
topology and could not be changed (out of blast radius): the WebUI BFF proxies to
`http://api:8000`; the api proxies generation to the `vllm-omni` container and drives its
lifecycle over the Docker socket (`DockerCliController`); the api serves reasoning as an
in-container `vllm serve` subprocess. We shipped a lean torch-free api image (full generation
surface via the vLLM-Omni container) with an opt-in `WITH_REASONING` build, a Next standalone
WebUI, and a render-only vLLM-Omni image pinned to the immutable `MIG-S2` commit. Weights are
external `:ro` bind-mounts with repo-relative defaults; ports bind loopback by default. The
sharded review caught a build that installed no vLLM (fixed) and an operator-`.env` that was
silently ignored (fixed); a self-catch (the failure-arbiter doc re-tripped the scanner) was
fixed and seeded.

## Decision Log

| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| api image | Lean default + `WITH_REASONING` ARG | Always-heavy / always-lean | Fast honest `docker build`; full generation surface; reasoning opt-in | `design.md` D-1 |
| Gen-container control | Raw `/var/run/docker.sock`, confined | socket-proxy now | Matches code's accepted design; simplest for local; proxy → S7/S8 | `design.md` D-6; R-16 |
| Checkpoint mounts | Repo-relative `../models/<Repo>` (`:ro`) | Absolute / `/path/to` | No absolute/private path in committed files; runnable after download | `design.md` D-5 |
| Compose structure | Shared base + `include:` fp8/nvfp4 + overlay | Two standalone / base+override 2×`-f` | DRY; each renders standalone under one `-f` (matches the check) | `design.md` D-4 |
| Gen-container lifecycle | `restart:"no"`, no health `depends_on` | Compose-managed health gate | Orchestrator owns start/stop; cold start via `COSMOS3_PLANE_READY_TIMEOUT` | `design.md` D-7 |
| vLLM-Omni pin | Immutable **commit** SHA | Mutable tag / branch | Bit-reproducible; closes the "mutable pin" adversarial case (S-2) | INV-3; `sharded_review` S-2 |
| Port binding | `BIND_ADDR=127.0.0.1` default | `0.0.0.0` default | Auth-off + docker.sock ⇒ loopback-by-default is safer for beta | `sharded_review` S-3; R-16 |
| GPU scope | Render + build + scans; defer GPU to S8 | Real GPU smoke now | GPU is the S8 gate; avoid multi-GB downloads/heavy builds | `session_6.md`; INV-8 |

## Next Priority Queue

1. **`MIG-S7` (README + hygiene):** re-run `tests/test_private_ref_scan.py` over
   README/hygiene; keep model license (`openmdw-1.0`) separate from repo MIT (base id
   `nvidia/Cosmos3-Nano`). Document the exact local-build commands from `Makefile`/`.env.example`
   and the loopback-by-default + `COSMOS3_API_KEY` note. **Fix X-1** (WebUI sends
   `Authorization: Bearer`, API checks `X-API-Key` — enabling the key currently breaks the
   proxy; both files are product code, out of S6 radius). Consider the `.gitignore` hygiene
   gap (root `.gitignore` still doesn't cover `__pycache__/`/`.venv/`/`node_modules/`).
2. **`MIG-S8` (release gate / GPU):** build `deploy/vllm-omni.Dockerfile`; **confirm the fork's
   real OpenAPI serve entrypoint** (the `CMD` is a best-effort guess, overridable via Compose
   `command:`); run the `EV-MIG-GPU-*` manual gates on the RTX 5090 (record hardware, driver,
   checkpoint revision, vLLM-Omni commit, request shape, artifact metadata); validate the
   `WITH_REASONING` image's torch/vLLM/CUDA compatibility and the evict/reload GPU dance;
   resolve **R-05** and **D1** (does the default `vllm_omni` container actually load the public
   FP8 **and** NVFP4 checkpoints); review SHA-pinning CI actions + `docker:28-cli`/`uv` digests.
3. **Durable `deploy/` gate (T-1):** add a render-only + weight-copy + private-path CI job for
   `deploy/`/`.env.example`, and extend the scanner's `SCAN_ROOTS`. Both touch `.github/**` /
   `tests/**` (out of S6 radius) → needs a contract amendment; owner for S7/S8.

## Warnings And Gotchas

- **Compose project dir = `deploy/`.** Run compose from the repo root as
  `docker compose -f deploy/docker-compose.<stack>.yml …`; `..` = repo root (build context)
  and `../models` = `<repo>/models`. A repo-root `.env` is auto-loaded only via the `Makefile`
  (which passes `--env-file .env`) or an explicit `--env-file`/`deploy/.env` — plain `docker
  compose -f deploy/...` looks for `deploy/.env` (see `mig_s6_compose_env_projectdir`).
- **Enabling `COSMOS3_API_KEY` breaks the WebUI→API proxy** today (Bearer vs `X-API-Key`, X-1)
  — pre-existing, fix in a session that can touch `webui/`/`api/`.
- **vLLM-Omni image + GPU are unproven** here: the serve `CMD` is an S8-verify guess; the image
  build is heavy/CUDA (S8). Do not claim in-process/GPU generation until S8 records it.
- **Docker-socket privilege (R-16):** the api container is root-equivalent on the host via the
  socket. Confined by the fixed-argv `DockerCliController` + loopback ports; `docker-socket-proxy`
  + requiring the API key before non-loopback exposure are S7/S8 hardening.
- **Files future sessions must not casually edit:** `api/**` and `webui/**` product code and
  `schemas/openapi.json` (INV-9 public API shape); `pyproject.toml`/`uv.lock` pins. Do not name
  private paths/hosts in scanned docs; do not use an absolute example path outside `/path/to/…`
  (the scanner's only sanctioned placeholder — `/mnt/…`, `/home/<user>`, `/Users/…`,
  `/data/home…` are flagged).
- **Deferred risks:** R-05 (CPU-CI-green-while-GPU-broken) → S8; R-13 vLLM-Omni image build → S8;
  R-16 socket hardening → S7/S8; D1 checkpoint load → S8; T-1 deploy/ CI gate → S7/S8.
- **Contract note:** `session_6_contract.yaml` `allowed_files` was amended (add
  `docs/handoff.md`, `docs/eval_corpus/**`, `docs/session_6_contract.yaml`) — **owner may
  review/keep** (mirrors S4 FA-4 / S5 D10).

## Eval Seeds

- New regression candidates (added to `docs/eval_corpus/`):
  - `mig_s6_scan_doc_selfmatch.md` — a scan-finding write-up is itself scanned; quote flagged
    literals in a non-matchable form and re-run the scan over the whole tree after authoring docs.
  - `mig_s6_compose_env_projectdir.md` — a repo-root `.env` is ignored when compose files live in
    a subdir (project dir = that subdir); a render check passes on defaults and masks the drop.
  - `mig_s6_reasoning_build_missing_dep.md` — a build variant advertised a dep its `--extra`
    didn't provide; "build succeeds" ≠ capability present.
- Instruction-update candidates (REVIEW.md / project contract template): (a) subdir-compose ⇒
  document `--env-file`/`--project-directory`; (b) verify a build variant's resolved deps match
  its advertised capability; (c) re-run the committed scanner over the whole tree after writing
  docs, including scan-finding write-ups.
