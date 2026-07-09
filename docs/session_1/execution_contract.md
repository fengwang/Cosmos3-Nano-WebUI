# GPU-S1 Execution Contract

Date: 2026-07-09
Session contract: `docs/session_1_contract.yaml` (risk: high, routing:
branch_and_compare)

## Planned File Changes

- `deploy/vllm-omni.Dockerfile` — rework (base image, fork install, CMD).
- `deploy/docker-compose.local-image.yml` — delete.
- `docs/release_checklist.md` — §6 evidence update.
- `docs/evidence_map.md` — new evidence rows.
- `docs/risk_register.md` — R-01/R-09 status updates.
- `docs/session_1/**` — this planning pack (already written) +
  `sharded_review.md`, `adversarial_verification.md`, `failure_arbiter.md`
  (only if needed) added as the session proceeds.
- `docs/handoff.md`, `docs/eval_corpus/*` — session close.

## Allowed Blast Radius

Exactly `session_1_contract.yaml`'s `blast_radius.allowed_files`:
`deploy/vllm-omni.Dockerfile`, `deploy/docker-compose*.yml`,
`deploy/docker-compose.local-image.yml`, `docs/session_1/**`,
`docs/release_checklist.md`, `docs/evidence_map.md`,
`docs/risk_register.md`. Forbidden: `api/**`, `webui/**`, `schemas/**`,
`.github/**`, any model weight or generated media file, and the `wfen/*`
Hugging Face repos. No file outside this list will be edited without
stopping to flag it first.

## First Test to Write

There is no unit-test harness for a Dockerfile; the first check is the
sm_120 spike (Plan Step 1) — a manual GPU verification gate, run before any
file changes, gating whether `v0.24.0` is even viable as the base image.
The first check with a pass/fail tied to a file change is Plan Step 3:
`docker compose -f deploy/docker-compose.fp8.yml build vllm-omni` exits 0
against the rewritten Dockerfile.

## Checks to Run After Each Task

- After the Dockerfile rewrite: `docker compose -f
  deploy/docker-compose.fp8.yml build vllm-omni` (exit 0) +
  `docker history`/layer-ID diff against `vllm/vllm-omni:cosmos3`.
- After `up`: `curl -sf http://localhost:8000/v1/models` → HTTP 200.
- After each T2I request: valid image artifact + recorded evidence fields
  (INV-8: hardware, driver/CUDA, checkpoint revision, vLLM-Omni commit,
  request shape, artifact metadata, pass/fail).
- After deleting the local-image file: `git status --short` shows it gone,
  not merely untracked.
- After doc edits: `rg` sweep for the old (broken) Dockerfile recipe and
  for the deleted file's name, to confirm no other doc still references
  them as current.
- Full deterministic check list from `session_1_contract.yaml`, re-run once
  at the end against the final committed state.

## Review Axes (risk = high → mandatory sharded review)

correctness, security, tests, architecture, performance — per
`session_1_contract.yaml` and `docs/agent_workflow/prompts/sharded_review.md`.
Each reviewer is read-only and reports severity, evidence, violated
contract clause (if any), smallest safe fix, and confidence. Fix
Critical/High findings only before re-checking; Medium needs 2+ reviewers
or strong evidence; Nits are optional.

## Adversarial Verifier Brief

Fresh context; sees only `session_1_contract.yaml`, `docs/project_contract.md`,
the diff, and `docs/session_1/`'s recorded evidence — not this
implementation conversation. Its job: try to falsify the claim that
`GATE-GPU-S1-DOCKERFILE` is satisfied. Specifically probe the contract's
four named adversarial cases:

1. Did the build actually avoid the cached `vllm/vllm-omni:cosmos3` prebuilt
   (not just claim to)?
2. Does the chosen base tag support sm_120 at *runtime* (a real kernel
   launch), not only at pull/compile time?
3. Does the serve entrypoint work for NVFP4 as well as FP8, not just one?
4. Is `docker-compose.local-image.yml`'s disposition actually recorded (file
   gone + reason documented), not silently left in place?

## Done Condition

`GATE-GPU-S1-DOCKERFILE` passes: `deploy/vllm-omni.Dockerfile` builds from
public inputs only (no cosmos3 prebuilt layer), the built image serves
`/v1/models`, and generates a valid T2I artifact on the RTX 5090 for both
FP8 and NVFP4 checkpoints; `deploy/docker-compose.local-image.yml` is
removed with a recorded reason; `docs/release_checklist.md` §6,
`docs/evidence_map.md`, and `docs/risk_register.md` reflect this evidence.
Sharded review and adversarial verification both complete with no
unresolved Critical/High finding.
