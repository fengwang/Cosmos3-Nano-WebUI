# PRD - GPU Release Readiness and Upstream Quant Contribution

Date: 2026-07-08
Status: Draft blueprint (revised after adversarial review), documentation first
Owner: Feng
Related: `docs/project_contract.md`, `docs/evidence_map.md`,
`docs/risk_register.md`, `docs/eval_seed_cases.md`,
`docs/session_{1..5}.md`, Phase-1 record in `docs/archive/phase-1/`
(see `docs/archive/phase-1/next_phase_handoff.md` for the deep-study input
to this blueprint).

## 1. Problem

Cosmos3-Nano-WebUI shipped as a public beta / research preview with an
owner-ratified GO (`docs/archive/phase-1/handoff.md`), and a post-GO gate
proved GPU text-to-image (T2I) generation end to end for both FP8 and NVFP4
on an RTX 5090. That proof used a prebuilt local image and checkpoints with a
manual local fix, not the public, from-source, reproducible path. Three gaps
were deferred deliberately at the release gate and block a clean, fully
public deployment:

- The public `deploy/vllm-omni.Dockerfile` does not build from public inputs.
  It uses `pip install --break-system-packages`, which the base image's pip
  22.0 (Ubuntu 22.04) rejects; the `-runtime` CUDA base has no build
  toolchain; and its `CMD` invokes the wrong entrypoint.
- The published `wfen/Cosmos3-Nano-FP8-Blockwise` and
  `wfen/Cosmos3-Nano-NVFP4-Blockwise` Hugging Face checkpoints do not
  clone or load cleanly: a stale top-level `model.safetensors.index.json`
  references non-existent shards, and small config/tokenizer files are
  LFS-tracked, so a plain `git clone` leaves them as unresolved pointers.
- FP8/NVFP4 blockwise quantization support exists only in the
  `fengwang/vllm-omni` fork, not in the upstream `vllm-project/vllm-omni`
  project, so every operator depends on a single-maintainer fork rather than
  community-reviewed code.

## 2. Goal

Close all three gaps so that an operator can clone, build, download, and
serve Cosmos3-Nano-WebUI with no manual workarounds, and so the FP8/NVFP4
blockwise quant loaders are available to the broader vLLM-Omni community
through a clean, decoupled upstream contribution. Concretely: a public,
from-source Docker build of vLLM-Omni; Hugging Face checkpoints that clone
and load cleanly, with every in-repo pinned reference kept in sync; a
recorded, evidenced end-to-end validation on GPU hardware; and either an
open, DCO-signed, CI-green pull request against `vllm-project/vllm-omni`, or
a documented finding that upstream already covers the contribution.

This is a documentation-and-blueprint pass only. It defines the sessions,
contracts, and gates that later development sessions execute one at a time;
it does not itself change application code, Dockerfiles, or published
checkpoints.

## 3. Owner Decisions

These decisions are binding for this blueprint and for the sessions it
defines:

1. Session IDs are `GPU-S1` through `GPU-S5`.
2. Phase-1's contract pack (`prd.md`, `project_contract.md`,
   `risk_register.md`, `evidence_map.md`, `eval_seed_cases.md`), its
   `handoff.md` and `next_phase_handoff.md`, its `session_{1..8}.md` /
   `session_{1..8}_contract.yaml` / `session_{1..8}/` artifacts, and its
   `eval_corpus/mig_s*.md` entries move to `docs/archive/phase-1/` and are
   not edited further. `docs/model_setup.md`, `docs/release_checklist.md`,
   and `docs/agent_workflow/**` stay at the top level and are edited in
   place by Phase-2 sessions.
3. Task B (checkpoint fix) is scoped to the top-level weight index and LFS
   tracking only. The HF repos' dev-scratch drift (`_s2_*.md`,
   `producer_provenance.json`, `load_quantized.py`,
   `assets/FP8-Examples/**`, benchmark PNGs) is out of scope this pass.
4. LFS rule for the HF checkpoint repos: files larger than 10 MB, or any
   non-plain-text file (`.safetensors`, `.png`, `.jpg`/`.jpeg`, `.mp3`,
   `.mp4`, `.webm`, `.pt`/`.pth`/`.ckpt`, …), use Git LFS. Small plain-text
   files (`.json`, `.txt`, `.md`, `.jinja`, tokenizer files) use regular Git
   so they resolve on a plain `git clone`.
5. Task C (upstream contribution) is scoped to the model-agnostic FP8/NVFP4
   blockwise quant loaders only, decoupled from Cosmos3-specific model code,
   and must not require the Cosmos3 model or break existing upstream
   functionality.
6. `GPU-S3`'s joint validation targets a T2I pass as the MUST-level bar and
   attempts a small text-to-video (T2V) smoke as a SHOULD; `t2v_audio`,
   `i2v`, `forward_dynamics`, full `reasoning` validation, and 720p video are
   Non-Goals for this phase (see §6).
7. `GPU-S5` (opening the upstream PR) requires an explicit owner go-ahead
   recorded immediately before the PR is opened. A passing `precheck-pr`
   gate and green CI are necessary but not sufficient on their own.
8. The untracked `deploy/docker-compose.local-image.yml` stopgap is
   dispositioned inside `GPU-S1` (dropped, or kept only as an explicitly
   documented "reuse a prebuilt image" convenience) rather than left as the
   de facto serving path.

## 4. Requirements

Requirement keywords follow RFC 2119. A claim that is not yet verified at
blueprint time is written as a verification task or session gate, not as a
shipped capability.

### Functional

- **FR-1 (MUST)** `deploy/vllm-omni.Dockerfile` builds a working vLLM-Omni
  image from public inputs only (no `vllm/vllm-omni:cosmos3` prebuilt),
  installing the pinned fork commit `697035018b70cef76b974a909d23371a9984c3f2`
  by immutable commit SHA.
- **FR-2 (MUST)** The image built under FR-1 serves `/v1/models` and
  generates a valid T2I artifact on the target GPU (RTX 5090, sm_120) using
  the confirmed entrypoint (`vllm serve <checkpoint-dir> --omni --host
  0.0.0.0 --port 8000 …`).
- **FR-3 (MUST)** Both `wfen/Cosmos3-Nano-FP8-Blockwise` and
  `wfen/Cosmos3-Nano-NVFP4-Blockwise` have their stale top-level
  `model.safetensors.index.json` removed and `.gitattributes`/LFS tracking
  corrected per the Owner Decision 4 rule, verified against a fresh clone or
  `hf download` rather than an already-patched local checkout.
- **FR-4 (MUST)** Every in-repo pinned-revision reference is updated to the
  new Hugging Face revisions in the same session that changes them, verified
  by a whole-repository sweep — at minimum `docs/model_setup.md` §1,
  `docs/evidence_map.md`, `docs/release_checklist.md` §7, and
  `docs/eval_seed_cases.md` — with no stale pin left anywhere else either.
- **FR-5 (MUST)** `GPU-S3` proves, with a fresh `hf download` at the new
  revisions through the `GPU-S1` image, that FP8 and NVFP4 load and generate
  a T2I artifact with no manual index removal or LFS-pointer workaround.
- **FR-6 (SHOULD)** `GPU-S3` attempts a small T2V smoke on at least one
  checkpoint. If infeasible within the session's scope or hardware budget,
  the session records why and routes it to the Non-Goals follow-up list
  rather than dropping it silently.
- **FR-7 (MUST)** `GPU-S4` records, with evidence, whether
  `vllm-project/vllm-omni` `main` already implements FP8/NVFP4 blockwise or
  ModelOpt-native quant detection before any upstream-facing code is written.
- **FR-8 (MUST)** If a contribution proceeds, it contains only model-agnostic
  quant loader code decoupled from Cosmos3-specific model, adapter, or guard
  code, and does not require the Cosmos3 model to build or pass CI.
- **FR-9 (MUST)** An upstream pull request is not opened unless it is
  DCO-signed, passes the fork's `precheck-pr` skill and the upstream
  `pre-commit` / `build_wheel` CI, and has an explicit, separately recorded
  owner go-ahead immediately before submission.
- **FR-10 (MUST)** No production dependency, public API shape, or existing
  non-quant vLLM-Omni runtime path regresses as a result of `GPU-S1` through
  `GPU-S5` work.

### Non-Functional

- **NFR-1 (MUST)** No secret, token, private host, private absolute path, or
  model weight is committed to this repository or to the `vllm-omni` fork as
  part of this work.
- **NFR-2 (MUST)** Every release-blocking recommendation in
  `docs/project_contract.md` has an evidence row in `docs/evidence_map.md` or
  is marked speculative with a named re-verification gate.
- **NFR-3 (MUST)** Pushing to the `wfen/*` Hugging Face repos and opening the
  upstream pull request are each preceded by an explicit, recorded human
  decision gate, since both are outward-visible and not fully reversible.
- **NFR-4 (MUST)** Every manual GPU check records hardware, driver/CUDA
  context, checkpoint repo and revision, vLLM-Omni commit, request shape,
  artifact metadata, and pass/fail result.
- **NFR-5 (SHOULD)** Where a `GPU-S#` session closes out a specific Phase-1
  risk (for example `R-03`, `R-05`, `R-13` in
  `docs/archive/phase-1/risk_register.md`), the Phase-2 risk register records
  the closure with a pointer to the archived row.

## 5. Acceptance Criteria

This blueprint's scope is done only when all are true:

1. `docs/archive/phase-1/` contains the full Phase-1 contract pack, handoff
   docs, session artifacts, and `mig_s*` eval-corpus entries; the top level
   holds the fresh `GPU-S#` contract pack plus the untouched living docs
   (`model_setup.md`, `release_checklist.md`, `agent_workflow/**`).
2. `docs/prd.md`, `docs/project_contract.md`, `docs/risk_register.md`,
   `docs/evidence_map.md`, and `docs/eval_seed_cases.md` exist in their
   Phase-2 form, and `docs/session_{1..5}.md` /
   `docs/session_{1..5}_contract.yaml` exist for `GPU-S1`..`GPU-S5`.
3. `deploy/vllm-omni.Dockerfile` builds and serves from public inputs alone;
   the local-image stopgap is explicitly dispositioned, not silently left as
   the de facto path.
4. Both Hugging Face checkpoint repos load cleanly from a fresh clone or
   download; every pinned reference in this repo matches the new revisions.
5. A fresh end-to-end T2I run (and a recorded T2V attempt) exists against the
   from-source image and the fixed checkpoints, with no manual workaround.
6. `GPU-S4` has a recorded, evidenced answer to "does upstream already have
   this" before any contribution code exists.
7. Either a DCO-signed, CI-green pull request is open on
   `vllm-project/vllm-omni`, or a documented reason exists for why no pull
   request was needed. This question is never left both unanswered and
   unrecorded.
8. `docs/risk_register.md`, `docs/evidence_map.md`, and
   `docs/eval_seed_cases.md` reflect the final state of every session that
   has closed, with pointers back to any Phase-1 risk a session advances or
   closes.

## 6. Non-Goals

- Dev-scratch cleanup (drift D3) on the `wfen/*` Hugging Face repos.
- Full GPU validation of `t2v_audio`, `i2v`, `forward_dynamics`, and
  `reasoning`, and any 720p video validation (peak VRAM exceeds 32 GB on the
  target GPU). Only a best-effort small T2V smoke is in scope, per FR-6.
- `R-16` (`docs/archive/phase-1/risk_register.md`) `docker-socket-proxy`
  hardening and the non-loopback exposure policy. This stays deferred
  post-beta hardening.
- Any change to public API route shapes, request/response schemas, or WebUI
  behavior.
- Publishing Docker images to a registry. Local build remains the supported
  path.
- Writing or editing application, Dockerfile, or checkpoint content during
  this blueprint-authoring pass. This PRD and its companion documents define
  sessions; they do not execute them.

## 7. Session Plan

| # | Session | Risk | Primary gate |
|---|---|---|---|
| 1 | Public-source vLLM-Omni Dockerfile build | high | `GATE-GPU-S1-DOCKERFILE` |
| 2 | HF checkpoint index/LFS fix and re-pin sweep | high | `GATE-GPU-S2-CHECKPOINT` |
| 3 | Joint validation on RTX 5090 (from-source image + fixed checkpoints) | high | `GATE-GPU-S3-VALIDATION` |
| 4 | Upstream state check and quant-patch isolation/rebase | medium | `GATE-GPU-S4-UPSTREAM-SCOPE` |
| 5 | `precheck-pr` gate and upstream PR submission | high | `GATE-GPU-S5-PR` |
