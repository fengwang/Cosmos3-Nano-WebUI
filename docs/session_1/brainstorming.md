# GPU-S1 Brainstorming — Public-Source vLLM-Omni Dockerfile Build

Date: 2026-07-09
Contract: `docs/session_1_contract.yaml`
Status: Approved by owner (Feng), proceeding to proposal/design/specs/tasks/plan.

## Context Explored

- Read `docs/prd.md`, `docs/session_1.md`, `docs/session_1_contract.yaml`,
  `docs/project_contract.md`, `docs/evidence_map.md`, `docs/risk_register.md`,
  `docs/model_setup.md`, `docs/release_checklist.md`,
  `docs/archive/phase-1/next_phase_handoff.md`. No top-level `docs/handoff.md`
  exists yet (Phase-2 has not closed a session).
- Confirmed `deploy/vllm-omni.Dockerfile` is broken exactly as documented:
  `FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04` (no build toolchain),
  `pip install --break-system-packages "git+...@${VLLM_OMNI_REF}"` (rejected
  by pip 22 / Ubuntu 22.04 PEP 668), and a wrong `CMD`
  (`python3 -m vllm_omni.entrypoints.openai.api_server`).
- Fetched the fork's actual `docker/Dockerfile.cuda` from GitHub at the pinned
  commit `697035018b70cef76b974a909d23371a9984c3f2`:
  `ARG BASE_IMAGE=vllm/vllm-openai:v0.24.0` → `FROM ${BASE_IMAGE}` → apt-get
  `git jq` → `COPY . /app/vllm-omni` → `uv pip install --python "$(...)" .`
  → `ENTRYPOINT []`. This confirms and refines the paraphrase in
  `next_phase_handoff.md`.
- Verified this sandbox is the real Archlinux/RTX 5090 host from
  `ENVIRONMENTS.md`, not a docs-only environment: Docker 29.6.1 + Compose
  v5.1.4 work; `nvidia-smi` shows a live, idle RTX 5090 (32 GB); github.com
  and huggingface.co are reachable; 296 GB free disk.
- Confirmed both `wfen/*` checkpoints are already unpacked at
  `/data/models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise`, with the stale
  `model.safetensors.index.json` already absent (workaround pre-applied),
  and `.env` already points `COSMOS3_FP8_DIR`/`COSMOS3_NVFP4_DIR` at them by
  absolute path. No new downloads needed for this session's smoke test.
- Empirically probed sm_120 support using the already-cached
  `vllm/vllm-openai:latest` image (resolved to vLLM 0.21.0, torch
  2.11.0+cu13.0): it detects the RTX 5090 as compute capability `(12, 0)`
  and runs a real bf16 matmul on it. This is concrete evidence against R-01
  (base-image/sm_120 risk), though not yet for the exact `v0.24.0` tag the
  fork pins.
- Surveyed the local docker image cache (90 images, 660 GB) and ruled out
  several false leads: `vllm/vllm-omni:cosmos3` (27 GB, the forbidden
  prebuilt — must never be the build's base or an accidental cache hit),
  four `vllm-omni-local:*` iterations (21 GB each, dated Jul 2 + Jul 6 —
  historical manual attempts culminating in `c89089a4`, the exact proxy
  image `release_checklist.md` already documents as the one used for the
  proven T2I run), and `:session1`-tagged `cosmos3-nano-api`/`webui` images
  (45.5 GB / 287 MB) — `docker inspect`/`history` show these are dated
  2026-07-06 with a reasoning-overlay build (separate CUDA devel toolchain +
  vLLM 0.23.0 venv), i.e. leftovers from **Phase-1's own unrelated
  "session_1"**, not this `GPU-S1`. Confirmed no `docs/session_1/` artifacts
  existed yet (clean slate) and no uncommitted changes under `deploy/` or
  `docs/release_checklist.md` relative to `HEAD`.

## Clarifying Questions and Answers

1. **Execution mode** — given real Docker/GPU/network access, how much of
   the build/GPU work should run live in this session?
   → **Full live execution.** Pull the real base image, iterate the
   Dockerfile until it builds, serve it, and generate a real T2I artifact on
   the RTX 5090 in this session.
2. **Base image tag** — start from the fork's pinned `v0.24.0` (fresh
   ~20-25 GB pull) or the already-cached, already-probed `latest`
   (≈v0.21.0, zero pull cost)?
   → **`v0.24.0` first**, matching the fork exactly; fall back only if it
   fails the sm_120 probe or the fork install.
3. **`deploy/docker-compose.local-image.yml` disposition** — keep as a
   documented convenience, or drop entirely?
   → **Drop entirely.**
4. **Checkpoint coverage for the T2I smoke** — FP8 only, NVFP4 only, or
   both?
   → **Both FP8 and NVFP4** (both are already unpacked locally with the
   workaround pre-applied, so the marginal cost is low).
5. **Commit cadence** — follow this repo's demonstrated per-checkpoint
   commit convention, or stage changes and let the owner commit?
   → **Commit at each clean task checkpoint**, matching repo history.

## Approaches Considered (Dockerfile rework mechanism)

- **Approach A (chosen):** Minimal-diff fix — keep the current file's
  shape; fix exactly the three broken parts (base image →
  `vllm/vllm-openai:v0.24.0`; installer →
  `uv pip install --no-cache-dir "git+https://github.com/fengwang/vllm-omni.git@${VLLM_OMNI_REF}"`,
  falling back to plain `pip install` with no `--break-system-packages` if
  `uv` is absent; `CMD` → the confirmed `vllm serve` entrypoint). Smallest
  diff, easiest to review against the contract, matches how the file
  already tries to install (git+https).
- **Approach B (rejected):** Explicit `git clone` + `git checkout <sha>` +
  local `uv pip install .`, closer to the fork's literal `COPY .` structure.
  No functional advantage here (we don't need to iterate on fork source
  inside the image); extra layers for no benefit.
- **Approach C (rejected):** Multi-stage build (builder installs into a
  venv, final stage copies site-packages only). Shaves a small fraction off
  an image whose baseline (vllm-openai + CUDA + torch) is already tens of
  GB — not worth the added complexity/risk for a from-source ML package
  install.

## Design Decisions Reached

1. `CMD` bakes in `--init-timeout 1800` (no downside) but **not**
   `--no-guardrails` — guardrails stay on by default in the shipped image;
   `--no-guardrails` is applied only as an explicit override for this
   session's own smoke-test evidence, documented as a known limitation.
2. Verification order: (a) spike — pull `v0.24.0`, rerun the sm_120 CUDA
   probe before investing in the full install layer; (b) write the
   Dockerfile; (c) `build vllm-omni`; (d) `up` + `curl /v1/models`; (e) T2I
   against FP8, capture artifact + metadata; (f) swap the checkpoint mount
   to NVFP4 (same image — `docker-compose.base.yml` builds one shared
   `vllm-omni` image for both stacks) + T2I again; (g) sanity-check via
   `docker history`/base-layer comparison that no `vllm/vllm-omni:cosmos3`
   layer leaked in, per the contract's named adversarial case.
3. Delete `deploy/docker-compose.local-image.yml`; record the disposition in
   `release_checklist.md` §6 and `evidence_map.md`.
4. Update `release_checklist.md` §6, `evidence_map.md`, and
   `risk_register.md` (R-01 at minimum; R-09 closes since the GPU host is
   confirmed available) with the evidence this session produces.

## Outcome

Owner approved this direction verbatim ("this is good to me. proceed").
Proceeding to `docs/session_1/proposal.md`.
