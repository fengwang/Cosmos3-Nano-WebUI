<p align="center">
  <img src="misc/logo.png" alt="Cosmos3-Nano-WebUI" width="360">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-blue.svg">
  <img alt="Status: local self-hosted preview" src="https://img.shields.io/badge/status-local%20self--hosted%20preview-blue.svg">
  <a href="https://github.com/fengwang/Cosmos3-Nano-WebUI/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/fengwang/Cosmos3-Nano-WebUI/actions/workflows/ci.yml/badge.svg"></a>
</p>

<h1 align="center">Cosmos3-Nano-WebUI</h1>

<p align="center">
  A self-hostable <b>API + Web UI</b> for the Cosmos3-Nano world model —
  text/image&rarr;video (with audio), text&rarr;image, reasoning, and robot
  action / forward-dynamics — served locally from quantized <b>FP8 / NVFP4</b>
  checkpoints.
</p>

> [!NOTE]
> Built for a **trusted LAN / lab machine**: there is no application-layer auth,
> and ports bind loopback by default (LAN access is an explicit opt-in). See
> [Status & security](#status--security) for the honest posture and the per-mode
> verification status.

## What it does

Cosmos3-Nano-WebUI wraps the Cosmos3-Nano world model behind a clean HTTP API and
a Next.js web interface, so you can run generation and reasoning **on your own
machine** from publicly available quantized checkpoints. It targets a single
RTX 5090-class GPU: the weights are downloaded from Hugging Face (never committed
to Git or baked into images), and the generation engine runs in its own
container. Open the Web UI and you land directly in the Generation Studio.

## Features

Every generation / reasoning / action mode is **implemented in code and covered by
CPU tests**. Text&rarr;image (FP8 and NVFP4) is GPU-verified end to end; other GPU
inference paths are a documented manual gate.

| Capability | Endpoint(s) | Status |
|---|---|---|
| Text&rarr;image (FP8, NVFP4) | `POST /v1/generation/t2i` | Implemented · **GPU-verified¹** |
| Text&rarr;video · image&rarr;video · video+audio | `POST /v1/generation/{t2v,i2v,t2v_audio}` | Implemented · CPU-tested · GPU gate¹ |
| Reasoning | `POST /v1/reason` | Implemented · CPU-tested · GPU gate¹ |
| Robot action / forward & inverse dynamics / policy | `POST /v1/action/{forward_dynamics,inverse_dynamics,policy}` | Implemented · CPU-tested · GPU gate¹ |
| Async jobs + live progress over SSE | `POST /v1/jobs`, `GET /v1/jobs/{id}`, `.../events`, `.../artifact`, `.../trajectory`, `.../cancel` | Implemented · CPU-tested |
| Health & Prometheus metrics | `GET /v1/health/{live,ready}`, `GET /v1/metrics` | Implemented · CPU-tested |
| Web UI (generation, history, 3D / robot views) | Next.js 15 + React 19 app | Implemented · CPU-tested |

¹ GPU inference is a manual release gate (`MIG-S8`). Text&rarr;image is verified
end to end (`GPU-S3`). A recommended 720p text&rarr;video smoke has passed on both
FP8 and NVFP4, but full validation of the video / reasoning / action modes remains
the manual gate — no performance numbers are promised. See
[Status & security](#status--security) and [`docs/evidence_map.md`](docs/evidence_map.md).

## Quickstart

Local, single machine, **public inputs only** — no accounts, no API keys, no
registry images. About five minutes plus the checkpoint download.

```bash
# 1. Clone
git clone https://github.com/fengwang/Cosmos3-Nano-WebUI.git
cd Cosmos3-Nano-WebUI

# 2. Download a pinned public checkpoint (ungated; no auth). FP8 shown; NVFP4 is analogous.
pip install "huggingface_hub[cli]"
hf download wfen/Cosmos3-Nano-FP8-Blockwise \
  --revision 9bf5d6ae164688487bdb71947ccc6ebe70d12900 \
  --local-dir ./models/Cosmos3-Nano-FP8-Blockwise

# 3. (Optional) configure — the defaults work for a local run
cp .env.example .env      # edit only for LAN binding or a custom model path

# 4. Build the images (CPU) and bring up the FP8 stack
make build                # builds the api + webui images
make up-fp8               # webui :3000, api :8000, generation container

# 5. Check health, then open the Studio
make health               # GET /v1/health/ready
# → open http://localhost:3000  (you land directly in the Generation Studio)
```

There are **no keys to set**: the API ships with no authentication, and the
shipped defaults already apply a curated negative prompt and a **720p** video
default, so first outputs look right without tuning. Building the vLLM-Omni GPU
image and running GPU inference is the current **manual gate** (`MIG-S8`) —
text&rarr;image (FP8/NVFP4) is verified end to end; other modes are not yet
(see [`docs/model_setup.md`](docs/model_setup.md) and
[Status & security](#status--security)).

## Requirements

- **Inference:** Linux with an NVIDIA GPU (RTX 5090-class) and current CUDA drivers.
- **Local stacks:** Docker + Docker Compose.
- **Disk:** several GB per checkpoint (weights are downloaded, not bundled).
- **Development (optional):** Python 3.12 (`>=3.12,<3.13`) + [`uv`](https://docs.astral.sh/uv/);
  Node 22 + [`pnpm`](https://pnpm.io/) 11 — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Checkpoint setup

Weights live in **public Hugging Face repositories** and are downloaded or mounted
by you — they are never committed to Git or baked into images. Pin the revision
(not the mutable `main`).

| Purpose | Repo id | Pinned revision | Model license |
|---|---|---|---|
| Generation (FP8) | `wfen/Cosmos3-Nano-FP8-Blockwise` | `9bf5d6ae1646…` | `openmdw-1.0` |
| Generation (NVFP4) | `wfen/Cosmos3-Nano-NVFP4-Blockwise` | `5514c42b9759…` | `openmdw-1.0` |
| BF16 base (reasoning + action) | `nvidia/Cosmos3-Nano` | `fea6e03a…` | `other` |

A generation deployment serves exactly **one** of FP8 or NVFP4; reasoning and
action additionally use the BF16 base. The compose stacks wire the checkpoint
mounts for you; `.env.example` and
**[`docs/model_setup.md`](docs/model_setup.md) are the source of truth** for the
pinned revisions and licenses (shown above as a snapshot), the exact environment
variables, the per-mode compatibility matrix, the mount layout, and drift caveats.

> **Licensing.** The repository **code is MIT** (see [`LICENSE`](LICENSE)). The
> **model weights are not MIT** — the FP8/NVFP4 checkpoints are `openmdw-1.0` and
> the base is `other`. These are the model owners' licenses; review them before use.

## Troubleshooting

- **Compose can't find your `.env`.** Compose's project directory is `deploy/`, so
  a repo-root `.env` is auto-passed only via `make` (`--env-file .env`). With a
  bare `docker compose -f deploy/…`, pass `--env-file .env` or place the file at
  `deploy/.env`.
- **Can't reach it from another machine.** Ports bind loopback by default; set
  `BIND_ADDR=0.0.0.0` for LAN access — only on a trusted network.
- **One checkpoint at a time.** The FP8 and NVFP4 stacks share a fixed generation
  container name — bring up one stack at a time (`make up-fp8` xor `make up-nvfp4`).
- **Cold start.** The API starts the generation container on demand; first
  requests wait on `COSMOS3_PLANE_READY_TIMEOUT`.

## Status & security

This is an honest local self-hosted preview. It is shaped for a **trusted LAN /
lab machine**, not for untrusted or internet-facing use. Every claim below is
tracked in [`docs/evidence_map.md`](docs/evidence_map.md) and
[`docs/risk_register.md`](docs/risk_register.md).

**Verification status.**

- Text&rarr;image (FP8/NVFP4) is **GPU-verified end to end** (`GPU-S3`): fresh
  checkpoint download, from-source image, no manual workaround.
- Text&rarr;video / image&rarr;video / video+audio, reasoning, and robot action are
  **implemented and CPU-tested**; full GPU validation is a manual release gate
  (`MIG-S8`). A recommended 720p text&rarr;video smoke passed on both FP8 and
  NVFP4, but does not by itself promote those modes to "verified".

**Security posture (no auth by design).**

- **No application-layer auth.** All routes (generation, jobs, action, reasoning,
  health, metrics) are open; access control is network placement, not a
  credential.
- **Loopback by default.** Ports bind `127.0.0.1` (`BIND_ADDR`); LAN exposure is
  an explicit opt-in — set `BIND_ADDR=0.0.0.0` only on a trusted network.
- **Root-equivalent Docker socket.** The API mounts the host Docker socket to
  drive the generation container. Do not expose this container to untrusted
  callers. See [`SECURITY.md`](SECURITY.md).
- **Guardrails off by default.** The generation stack ships with content
  guardrails disabled — the `cosmos_guardrail` model is not bundled, and the
  trusted-LAN appliance runs guardrails-off by design — so generated output is
  unfiltered.

**Generation defaults & VRAM.**

- **Good output out of the box.** A curated negative prompt applies by default and
  is overridable per request and in the UI.
- **720p video default.** `1280×720` is the default for the video modes, served by
  the quantized **FP8/NVFP4** path (never the BF16 base). The shipped 49-frame
  default fits comfortably on 32 GB (measured peak ≈ 14.7 GB on FP8, ≈ 18.5 GB on
  NVFP4); FP8's fit relies on layer-wise offload and tightens at higher frame
  counts, so prefer **NVFP4** for more headroom.

## Project

- 🔒 **Security:** report vulnerabilities privately — see [`SECURITY.md`](SECURITY.md)
  (please do not open a public issue).
- 🤝 **Contributing & development:** [`CONTRIBUTING.md`](CONTRIBUTING.md) has the
  dev setup, the CPU checks that mirror CI, and the PR guidelines.
- 📜 **Code of Conduct:** [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
- ⚖️ **License:** repo code is [MIT](LICENSE); model weights carry their own
  licenses (see [Checkpoint setup](#checkpoint-setup)).
