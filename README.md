<p align="center">
  <img src="misc/logo.png" alt="Cosmos3-Nano-WebUI" width="360">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-blue.svg">
  <img alt="Status: beta / research preview" src="https://img.shields.io/badge/status-beta%20%2F%20research%20preview-orange.svg">
  <a href="https://github.com/fengwang/Cosmos3-Nano-WebUI/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/fengwang/Cosmos3-Nano-WebUI/actions/workflows/ci.yml/badge.svg"></a>
</p>

<h1 align="center">Cosmos3-Nano-WebUI</h1>

<p align="center">
  A self-hostable <b>API + Web UI</b> for the Cosmos3-Nano world model —
  text/image&rarr;video (with audio), text&rarr;image, reasoning, and robot
  action / forward-dynamics — served locally from quantized <b>FP8 / NVFP4</b>
  checkpoints.
</p>

> [!WARNING]
> **Beta / research preview.** This project is not intended for production or
> untrusted, internet-facing use. Text&rarr;image (FP8/NVFP4) is GPU-verified; every
> other GPU inference path has **not** yet been verified in this public repository
> — it is a manual release gate (see [Limitations](#limitations--beta-status)).
> Runtime, hardware, and performance statements below are described as
> capabilities-present, not proven results except where marked verified.

## What is this?

Cosmos3-Nano-WebUI wraps the Cosmos3-Nano world model behind a clean HTTP API and a
Next.js web interface so you can run generation and reasoning **on your own machine**
from publicly available quantized checkpoints. It is designed to run locally on a
single RTX 5090-class GPU, with the model weights downloaded from Hugging Face (never
committed to Git or baked into images) and the generation engine running in its own
container.

The repository is a curated public migration: API, WebUI, schemas, tests, tools, and
local-build Docker/Compose. CPU checks run in GitHub Actions; GPU inference is a
documented manual gate for the first beta.

## Features

Every generation/reasoning/action mode is **implemented in code and covered by CPU
tests**. Text&rarr;image (FP8 and NVFP4) is now GPU-verified end to end, from a fresh
checkpoint download through the from-source image, with no manual workaround; every other
GPU inference path remains unverified in this repo (manual gate — see
[Limitations](#limitations--beta-status)).

| Capability | Endpoint(s) | Status |
|---|---|---|
| Text&rarr;image (FP8, NVFP4) | `POST /v1/generation/t2i` | Implemented · **T2I-verified¹** |
| Text&rarr;video · image&rarr;video · video+audio | `POST /v1/generation/{t2v,i2v,t2v_audio}` | Implemented · GPU-unverified¹ |
| Reasoning | `POST /v1/reason` | Implemented · GPU-unverified¹ |
| Robot action / forward & inverse dynamics / policy | `POST /v1/action/{forward_dynamics,inverse_dynamics,policy}` | Implemented · GPU-unverified¹ |
| Async jobs + live progress over SSE | `POST /v1/jobs`, `GET /v1/jobs/{id}`, `.../events`, `.../artifact`, `.../trajectory`, `.../cancel` | Implemented · CPU-tested |
| Health & Prometheus metrics | `GET /v1/health/{live,ready}`, `GET /v1/metrics` | Implemented · CPU-tested |
| Web UI (generation, history, 3D / robot views) | Next.js 15 + React 19 app | Implemented · CPU-tested |

¹ GPU inference is a manual release gate (`MIG-S8`); see [`docs/evidence_map.md`](docs/evidence_map.md).
A best-effort NVFP4 text&rarr;video smoke also passed, but does not itself upgrade the
`t2v` row above — see [Limitations](#limitations--beta-status).

## Quickstart

Local, single machine. Uses **public inputs only** — no private hosts, no registry
images.

```bash
# 1. Clone
git clone https://github.com/fengwang/Cosmos3-Nano-WebUI.git
cd Cosmos3-Nano-WebUI

# 2. Download a public checkpoint (ungated; no auth). FP8 shown; NVFP4 is analogous.
pip install "huggingface_hub[cli]"
hf download wfen/Cosmos3-Nano-FP8-Blockwise \
  --revision 9bf5d6ae164688487bdb71947ccc6ebe70d12900 \
  --local-dir ./models/Cosmos3-Nano-FP8-Blockwise

# 3. (Optional) configure — the defaults work for a local run
cp .env.example .env      # edit for auth (COSMOS3_API_KEY), LAN binding, or custom paths

# 4. Build the API + WebUI images (CPU) and bring up the FP8 stack
make build                # builds api + webui images
make up-fp8               # webui :3000, api :8000, generation container

# 5. Check health / open the UI
make health               # GET /v1/health/ready
# Web UI → http://localhost:3000
```

> [!NOTE]
> The generation service runs the Cosmos3-Nano checkpoint inside the **vLLM-Omni
> container**, which uses a CUDA image and a GPU. Building that image and running GPU
> inference is the current **manual gate** (`MIG-S8`) — text&rarr;image (FP8/NVFP4) is
> verified end to end from public inputs; other generation modes are not yet verified
> here. See [`docs/model_setup.md`](docs/model_setup.md) and
> [Limitations](#limitations--beta-status).

## Requirements

- **Inference:** Linux with an NVIDIA GPU (RTX 5090-class) and current CUDA drivers.
- **Local stacks:** Docker + Docker Compose.
- **Development:** Python 3.12 (`>=3.12,<3.13`) + [`uv`](https://docs.astral.sh/uv/);
  Node 22 + [`pnpm`](https://pnpm.io/) 11.
- **Disk:** several GB per checkpoint (weights are downloaded, not bundled).

## Checkpoint setup

Weights live in **public Hugging Face repositories** and are downloaded or mounted by
you — they are never committed to Git or baked into images. Pin the revision (not the
mutable `main`).

| Purpose | Repo id | Pinned revision | Model license |
|---|---|---|---|
| Generation (FP8) | `wfen/Cosmos3-Nano-FP8-Blockwise` | `9bf5d6ae1646…` | `openmdw-1.0` |
| Generation (NVFP4) | `wfen/Cosmos3-Nano-NVFP4-Blockwise` | `5514c42b9759…` | `openmdw-1.0` |
| BF16 base (reasoning + action) | `nvidia/Cosmos3-Nano` | `fea6e03a…` | `other` |

A generation deployment serves exactly **one** of FP8 or NVFP4; reasoning and action
additionally use the BF16 base. Point `COSMOS3_MODEL_DIR` / `COSMOS3_CHECKPOINT_LABEL`
at the checkpoint you serve.

> **Licensing.** The repository **code is MIT** (see [`LICENSE`](LICENSE)). The **model
> weights are not MIT** — the FP8/NVFP4 checkpoints are `openmdw-1.0` and the base is
> `other`. These are the model owners' licenses; review them before use.

**[`docs/model_setup.md`](docs/model_setup.md) is the source of truth** for the pinned
revisions and licenses above (shown here as a snapshot), plus every environment variable,
the per-mode compatibility matrix, mount layout, and drift caveats.

## Development

The commands below mirror the CPU-only CI in
[`.github/workflows/ci.yml`](.github/workflows/ci.yml).

```bash
# API (Python) — torch-free CPU environment
uv python install 3.12
uv sync --frozen --group test-cpu
uv run ruff check api tests
uv run pytest -m "not gpu"          # CPU suite (GPU-marked tests excluded)

# WebUI (from webui/)
cd webui && pnpm install --frozen-lockfile
pnpm build && pnpm lint && pnpm typecheck && pnpm test
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full workflow. GPU-marked tests run
only with `COSMOS3_ENABLE_GPU_TESTS=1 uv run pytest -m gpu` on supported hardware.

## Limitations & beta status

This is an honest early beta. Known limits, each tracked in
[`docs/risk_register.md`](docs/risk_register.md) and
[`docs/evidence_map.md`](docs/evidence_map.md):

- **GPU inference is unverified here, except text&rarr;image.** t2i (FP8 and NVFP4) is
  GPU-verified end to end — fresh checkpoint download, from-source image, no manual
  workaround, direct and full-stack (`GPU-S3`, 2026-07-09; see
  [`docs/evidence_map.md`](docs/evidence_map.md)). t2v/t2v_audio/i2v, reasoning, and action
  are implemented and CPU-tested, but no full GPU run, throughput, or quality result is
  claimed for them — that is the `MIG-S8` manual release gate. A best-effort NVFP4 t2v
  smoke passed but does not constitute full t2v validation. No performance numbers are
  promised.
- **Default engine is the vLLM-Omni container.** The imported in-process `diffusers`
  engine cannot load+verify the *current* public checkpoints as-is (drift **D1**);
  generation runs through the vLLM-Omni container, whose end-to-end compatibility is part
  of the same manual gate.
- **vLLM-Omni image build is heavy (CUDA).** It installs a pinned public fork commit; its
  build and exact serve entrypoint are confirmed at the manual gate.
- **Auth is off by default.** Set `COSMOS3_API_KEY` to require an `X-API-Key` on the
  generation, jobs, action, and reasoning routes — health and metrics stay open (the
  WebUI forwards it end to end). The API container mounts the
  host Docker socket to drive the generation container — ports bind `127.0.0.1` by
  default; keep it that way until you have enabled auth and network controls (R-16).
- **NVFP4 model card is a stub** upstream — use [`docs/model_setup.md`](docs/model_setup.md)
  for setup context.
- **Not published to a registry.** Images are built locally; there are no prebuilt images
  in this milestone.

## Troubleshooting

- **Compose can't find your `.env`.** Compose's project directory is `deploy/`, so a
  repo-root `.env` is auto-passed only via `make` (`--env-file .env`). With a bare
  `docker compose -f deploy/…`, pass `--env-file .env` or place the file at `deploy/.env`.
- **Can't reach it from another machine.** Ports bind loopback by default; set
  `BIND_ADDR=0.0.0.0` (and enable `COSMOS3_API_KEY`) for LAN access.
- **One checkpoint at a time.** The FP8 and NVFP4 stacks share a fixed generation
  container name — bring up one stack at a time (`make up-fp8` xor `make up-nvfp4`).
- **Cold start.** The API starts the generation container on demand; first requests wait
  on `COSMOS3_PLANE_READY_TIMEOUT`.

## Project hygiene

- 🔒 **Security:** report vulnerabilities privately — see [`SECURITY.md`](SECURITY.md)
  (please do not open a public issue).
- 🤝 **Contributing:** [`CONTRIBUTING.md`](CONTRIBUTING.md).
- 📜 **Code of Conduct:** [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
- ⚖️ **License:** repo code is [MIT](LICENSE); model weights carry their own licenses
  (see [Checkpoint setup](#checkpoint-setup)).
- ✅ **Release readiness:** [`docs/release_checklist.md`](docs/release_checklist.md).
