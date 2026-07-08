# GPU-S1 Design — Public-Source vLLM-Omni Dockerfile Build

Date: 2026-07-09
Input: `docs/session_1/proposal.md`

## Context

`deploy/vllm-omni.Dockerfile` is the only unbuildable Dockerfile in
`deploy/` (`api.Dockerfile` and `webui.Dockerfile` already build from public
inputs, per `MIG-S6`/S8 evidence). It fails at three independent points: a
`-runtime` CUDA base with no compiler toolchain, a `pip` flag Ubuntu
22.04's system pip rejects, and a guessed serve entrypoint that was never
the fork's real one. The one working proof of GPU inference
(`release_checklist.md` "GPU gate exercised") used a hand-built local image,
not this file — so the gap is entirely reproducibility, not feasibility.
This session runs on the actual target hardware (RTX 5090, confirmed via
`nvidia-smi` and a live sm_120 CUDA probe), so "verified" here means
executed, not just written.

Constraints: `docs/session_1_contract.yaml`'s `blast_radius` (only
`deploy/vllm-omni.Dockerfile`, `deploy/docker-compose*.yml`,
`docs/session_1/**`, `docs/release_checklist.md`, `docs/evidence_map.md`,
`docs/risk_register.md`), and `docs/project_contract.md`'s invariants
INV-1/2/3 (no secrets or weights baked in; immutable-SHA fork pin) apply
without exception.

## Goals / Non-Goals

**Goals:**
- `deploy/vllm-omni.Dockerfile` builds a working vLLM-Omni image using only
  public inputs (no `vllm/vllm-omni:cosmos3` prebuilt).
- The built image serves `/v1/models` and generates a valid T2I artifact on
  the RTX 5090 for **both** FP8 and NVFP4 (contract MUST-bar is "at least
  one"; this session targets both because the marginal cost is low and it
  retires the FP8/NVFP4-asymmetry adversarial case outright).
- `deploy/docker-compose.local-image.yml` is removed and the removal is
  recorded with a reason.
- `docs/release_checklist.md` §6, `docs/evidence_map.md`, and
  `docs/risk_register.md` reflect the fresh evidence.

**Non-Goals** (see `docs/session_1.md` Out of Scope):
- Fixing the `wfen/*` Hugging Face checkpoints themselves (`GPU-S2`) — this
  session reuses the already-known, already-applied local workaround.
- Any WebUI/API source or public API shape change.
- Docker image publishing/registry work.
- Upstream PR work (`GPU-S4`/`GPU-S5`).
- `t2v`/`i2v`/`reasoning`/720p validation (PRD §6 Non-Goals).

## Decisions

1. **Base image: `vllm/vllm-openai:v0.24.0`, verified empirically before
   committing to it.** This is the exact tag the fork's own
   `docker/Dockerfile.cuda` pins, so it's the least likely to hit a
   vLLM-internals/vllm-omni API mismatch. Because it isn't cached locally,
   the first implementation step is a cheap spike — pull it and rerun the
   same CUDA-capability probe already run successfully against the cached
   `latest` (≈v0.21.0) tag — before spending time on the full fork install
   layer. If the probe fails, fall back to a tag already confirmed
   sm_120-capable on this hardware (`latest`) rather than guessing blind.

2. **Install mechanism: single-line `uv pip install git+https://…@<sha>`,
   not a separate clone+checkout.** (Approach A from brainstorming.) The
   fork's own Dockerfile uses `COPY . + uv pip install .` because it's built
   from within a checkout of their repo; that mechanic doesn't apply to a
   consumer repo like this one. `pip`/`uv` installing directly from a
   `git+https://…@<immutable-sha>` ref is the standard, equivalent pattern,
   keeps the immutable-SHA pin (INV-3) in exactly one place, and is the
   smallest diff from the current (broken) file. If `uv` isn't on the
   image's `PATH`, fall back to plain `pip install --no-cache-dir` — the
   vllm-openai image ships its own Python, not Ubuntu's
   externally-managed one, so the original PEP 668 failure is base-image
   specific and shouldn't recur either way.

3. **`CMD` fixed to the confirmed entrypoint, guardrails on by default.**
   `["vllm", "serve", "/models/checkpoint", "--omni", "--host", "0.0.0.0",
   "--port", "8000", "--init-timeout", "1800"]`. `--init-timeout` is baked
   in (no downside for a model this size). `--no-guardrails` is
   deliberately **not** baked into the shipped default — it changes runtime
   safety behavior for every operator who builds this image, and the
   contract doesn't ask for that change. It's applied only as a one-off
   `docker compose run`/exec-time override for this session's own T2I
   evidence capture (documented as a known limitation: guardrails-on needs
   the gated `nvidia/Cosmos-1.0-Guardrail` model + `HF_TOKEN`, neither of
   which this smoke test provisions).

4. **Verification is live and ordered to fail cheaply first:** sm_120 probe
   (~1 min, no new pull if it fails fast) → Dockerfile write → `build` →
   `up` + `/v1/models` → FP8 T2I → swap checkpoint mount to NVFP4 (same
   image; `docker-compose.base.yml` builds one shared `vllm-omni` image, so
   no rebuild) → NVFP4 T2I → `docker history`/base-layer check that no
   `vllm/vllm-omni:cosmos3` layer is present. This ordering surfaces a
   base-image-class failure (the contract's named human-gate trigger)
   before the expensive from-source install runs.

5. **`deploy/docker-compose.local-image.yml`: delete, no replacement.**
   Owner's explicit choice over "keep as documented convenience." The file
   was never tracked, so removal is a no-op for anyone who already cloned
   the repo; it only prevents the file from ever landing in a commit.

6. **Commit at each clean task checkpoint**, matching this repo's
   established per-session git history pattern (confirmed via `git log`).

## Risks / Trade-offs

- **[Risk]** `v0.24.0` doesn't support sm_120, only an older/newer tag does
  → **Mitigation:** cheap probe-first ordering (Decision 1/4); this is also
  the contract's explicitly named human gate ("on a build-failure class
  that needs a base-image change") — if the probe fails, stop and report
  before picking a replacement tag rather than silently swapping it.
- **[Risk]** The build silently reuses a layer from the locally-cached
  `vllm/vllm-omni:cosmos3` prebuilt (27 GB, already present) → **Mitigation:**
  explicit post-build check comparing the new image's base layers against
  that prebuilt's layer IDs; this is a named adversarial case in
  `session_1_contract.yaml`.
- **[Risk]** `uv pip install .` of vllm-omni transitively pulls a different
  vLLM version than the base image ships, partially negating the
  "matches the fork's tested pairing" rationale for choosing `v0.24.0` →
  **Mitigation:** accept and record whatever vllm-omni's own dependency
  resolution does; this is exactly what "based on the fork's own recipe"
  means in practice, and the fork already validated this pairing.
- **[Risk]** FP8 T2I passes but NVFP4 silently fails on the same served
  image (named adversarial case) → **Mitigation:** both are tested this
  session (Proposal §Agreed Changes item 4), not just the contract's
  minimum of one.
- **[Risk]** A ~20-25 GB fresh pull plus a from-source vLLM-Omni build is
  slow (handoff notes cite 15-40 min historically) → **Mitigation:**
  accepted cost; disk has 296 GB free; only paid once per tag attempted.
- **[Risk]** GPU is a real, shared piece of hardware, not a disposable CI
  runner → **Mitigation:** confirmed idle (0% util, only Xorg) before
  starting; one container at a time; clean up (`docker compose down`)
  between FP8 and NVFP4 runs and at session end.

## Migration Plan

There is no running production system to migrate — this fixes a build
recipe that has never successfully produced a shippable image. Rollout is:
verify live in this session (build → serve → T2I) before any commit lands;
each git commit corresponds to one clean, checked task. Rollback, if a
change proves wrong after committing, is an ordinary `git revert` on the
`GPU-S1` branch — nothing external (no registry push, no HF push, no
upstream PR) is touched, so nothing outside this repository needs
unwinding. Downstream consumers (`GPU-S2` checkpoint fix,
`GPU-S3` joint validation) start from whatever base-image tag and recipe
this session's evidence records — that record is the actual "migration"
artifact for later sessions.

## Open Questions

- Exact transitive dependency behavior of `uv pip install .` for
  `vllm-omni` against the `v0.24.0` base (does it reinstall vLLM/torch, and
  if so how much extra time/bandwidth does that cost?) — unknown until the
  build actually runs; will be recorded as evidence rather than assumed.
- Whether `v0.24.0` needs any apt packages beyond `git` (the fork's own
  Dockerfile also installs `jq`, presumably for its own scripts we don't
  invoke) — resolved empirically during the build; not blocking the design.

Both are implementation-time findings, not decisions the design needs to
pre-resolve.
