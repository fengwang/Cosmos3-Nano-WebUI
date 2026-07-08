# GPU-S1 Proposal — Public-Source vLLM-Omni Dockerfile Build

Date: 2026-07-09
Input: `docs/session_1/brainstorming.md`

## Motivation

The public `deploy/vllm-omni.Dockerfile` cannot build a working image today:
it targets a `-runtime` CUDA base with no build toolchain, uses a
`pip install --break-system-packages` flag pip 22 (Ubuntu 22.04) rejects,
and invokes the wrong serve entrypoint. The only proof that Cosmos3-Nano
works on GPU (the post-GO gate) used a prebuilt local image
(`vllm-omni-local:c89089a4`), not this repository's own build recipe — so an
operator cloning the public repo today cannot reproduce that result. This
retires the build half of archived Phase-1 risk R-13 and unblocks
`GPU-S2`/`GPU-S3`, which both assume a working from-source image exists.

## Agreed Changes

From `docs/session_1/brainstorming.md`:

1. Rework `deploy/vllm-omni.Dockerfile`: base image
   `FROM vllm/vllm-openai:v0.24.0` (matching the fork's own
   `docker/Dockerfile.cuda`), fork installed via
   `uv pip install "git+https://github.com/fengwang/vllm-omni.git@697035018b70cef76b974a909d23371a9984c3f2"`
   (immutable-SHA pin, INV-3), `CMD` fixed to the confirmed
   `vllm serve <dir> --omni --host 0.0.0.0 --port 8000 --init-timeout 1800`
   entrypoint. Guardrails stay **on** by default; `--no-guardrails` is used
   only as an explicit override for this session's own smoke test.
2. Execute the full verification chain live on the RTX 5090 in this
   session: sm_120 probe on `v0.24.0` → `docker compose build vllm-omni` →
   `up` + `/v1/models` → T2I on FP8 → T2I on NVFP4 → confirm no
   `vllm/vllm-omni:cosmos3` layer leaked into the build.
3. Delete `deploy/docker-compose.local-image.yml` (no replacement — the
   owner chose "drop entirely" over "keep as documented convenience").
4. Update `docs/release_checklist.md` §6, `docs/evidence_map.md`, and
   `docs/risk_register.md` (R-01, R-09) with the fresh evidence produced.
5. Commit at each clean task checkpoint, matching this repo's established
   per-session convention.

## Capabilities

### New Capabilities

None — this session fixes an existing, already-specified build path; it
does not introduce a new product capability.

### Modified Capabilities

- **`vllm-omni-docker-build`** — `deploy/vllm-omni.Dockerfile` currently
  fails to build (broken base image + installer flag). Requirement changes
  to: builds successfully from public inputs only, with the fork pinned by
  immutable commit SHA, and never bakes model weights into the image.
- **`vllm-omni-serve-entrypoint`** — the built image currently starts the
  wrong process (`python3 -m vllm_omni.entrypoints.openai.api_server`).
  Requirement changes to: the image serves the OpenAI-compatible
  `vllm serve --omni` entrypoint on port 8000, answers `/v1/models`, and
  generates a valid T2I artifact for both FP8 and NVFP4 checkpoints.

### Removed Capabilities

- **`local-image-override`** (`deploy/docker-compose.local-image.yml`) — the
  "reuse a prebuilt image" stopgap compose override. Reason: PRD Owner
  Decision 8 requires this session to disposition the stopgap rather than
  leave it as a de facto path; the owner chose removal over keeping it as a
  documented convenience. Migration: none needed — the file is untracked
  (never shipped); operators who want to reuse a prebuilt image write their
  own override following the pattern in `deploy/docker-compose.base.yml`.

## Impact

- **Files:** `deploy/vllm-omni.Dockerfile` (rework),
  `deploy/docker-compose.local-image.yml` (delete),
  `docs/release_checklist.md` §6, `docs/evidence_map.md`,
  `docs/risk_register.md` (evidence/status updates).
- **Docker images:** a new `cosmos3-nano-vllm-omni:local` build (via
  `docker-compose.base.yml`); no registry publishing.
- **No impact** to `api/**`, `webui/**`, `schemas/**`, public API shapes, or
  the `wfen/*` Hugging Face repos — all explicitly out of scope and outside
  the session's blast radius.
- **Downstream sessions:** `GPU-S3` (joint validation) inherits the base
  image tag and any sm_120-specific findings; `docs/release_checklist.md`
  §6 becomes the reference point for "does the public build work."
