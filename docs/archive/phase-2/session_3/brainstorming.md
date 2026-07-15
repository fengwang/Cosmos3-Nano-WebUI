# Session 3 Brainstorming - Joint Validation on RTX 5090

Date: 2026-07-09
Branch: `GPU-S3` (off `GPU-S2`)

## Objective

Prove FP8 and NVFP4 T2I end to end on the RTX 5090 using the `GPU-S1` from-source
image and `GPU-S2`'s freshly downloaded, fixed checkpoints, with no manual
workaround, and attempt a small T2V smoke. See `docs/session_3.md` and
`docs/session_3_contract.yaml` for the authoritative scope.

## Context Explored

- Read `docs/prd.md`, `docs/session_3.md`, `docs/session_3_contract.yaml`,
  `docs/project_contract.md`, `docs/evidence_map.md`, `docs/handoff.md`,
  `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/model_setup.md`,
  the `Makefile`, and the `docs/session_2/**` pack (precedent for structure and
  probe style).
- `git status`/`git log`: clean tree on `GPU-S2`; `GPU-S1` and `GPU-S2` each
  closed their own gate; neither is merged into `phase-2` yet.
- Live environment probes, run before any planning, to answer "can this
  session actually execute the validation, not just plan it":
  - `nvidia-smi`: RTX 5090 idle (0% util, 15 MiB used, no contending process).
  - `docker ps -a` / `docker compose version`: Docker 29.6.1 / Compose 5.1.4
    present and functional; no containers currently running.
  - `hf auth whoami` → `user=wfen`, matching the checkpoint org
    (`wfen/Cosmos3-Nano-{FP8,NVFP4}-Blockwise`); `HF_TOKEN` is set.
  - `df -h /workspace`: 1.2 TB free — no disk-space concern for a ~100 GB
    fresh download (existing stale copies under `/data/models/Cosmos3-Nano-*`
    total ~239 GB and are left untouched; they are not this session's fresh
    download target).
  - `docker images`: `cosmos3-nano-vllm-omni:local` (20.9 GB) and
    `vllm/vllm-openai:v0.24.0` (20.4 GB) already cached from `GPU-S1`.
  - `docker compose -f deploy/docker-compose.fp8.yml config`: renders cleanly;
    the `vllm-omni` service bind-mounts `models/Cosmos3-Nano-FP8-Blockwise`
    relative to the repo root (this directory does not exist yet — today's
    fresh download creates it).
  - `.env` already has a 32-character `COSMOS3_API_KEY` configured, usable for
    the full-stack `X-API-Key` check without any new provisioning.
  - Conclusion: live execution (real `hf download`, real `docker compose up`,
    real GPU generation) is feasible from this session, matching `GPU-S1`'s
    and `GPU-S2`'s own precedent of executing real checks rather than only
    planning them. `project_contract.md` §5's routing table confirms the human
    gate for `GPU-S3` is conditional ("on T2I/T2V failure or a drift-D1
    recurrence"), not a blanket pre-approval gate — so proceeding straight to
    execution once the contract-derived plan is written is consistent with the
    project's own routing, not a deviation from it.

## Clarifying Questions Resolved

1. **R-10 (guardrails-on path) scope.** `docs/risk_register.md` assigns R-10
   "Owner Session: `GPU-S3`", but `docs/session_3.md`'s in-scope list and
   `project_contract.md`'s `GATE-GPU-S3-VALIDATION` text are both silent on
   guardrails. **Decision: out of scope.** This session runs with
   `--no-guardrails`, the same as `GPU-S1`. R-10 stays open in
   `docs/risk_register.md` for a later session with provisioned
   `nvidia/Cosmos-1.0-Guardrail` access.
2. **Probe tooling structure.** Three shapes were considered: (a) one
   end-to-end orchestrator script, (b) small focused, independently-runnable
   probes per task plus a lightweight aggregator, (c) a shell-only runbook
   with no dedicated verification code. **Decision: (b).** Each task gets its
   own probe that separates the side-effecting action from a pure check of
   the result, so a late failure (e.g. the T2V smoke) never requires re-running
   or risks corrupting already-recorded, already-passed evidence for earlier
   tasks. This also lines up with the Task Loop's one-task-at-a-time
   checkpoints and with the ACD (Actions/Calculations/Data) split from the
   functional-thinking skill.

## Validated Design

### Task sequencing

T2I evidence (both checkpoints, both direct and full-stack) is fully recorded
*before* the T2V smoke is attempted, because `session_3_contract.yaml`'s own
`failure_modes_to_watch` flags that VRAM pressure from a T2V attempt could
destabilize T2I evidence collected in the same session.

1. **T1 — Fresh checkpoint download.** `hf download` both `wfen/*` repos at
   the pinned `GPU-S2` revisions (FP8 `9bf5d6ae164688487bdb71947ccc6ebe70d12900`,
   NVFP4 `5514c42b9759739f545e0d0dee453db8d8525fbc`) into
   `models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise` (repo-root-relative, matching the
   compose bind-mount). Verify no unresolved LFS pointers and no stale
   `model.safetensors.index.json` landed in the fresh download.
2. **T2 — Confirm the `GPU-S1` image is current.** Check that
   `cosmos3-nano-vllm-omni:local` actually reflects the current
   `deploy/vllm-omni.Dockerfile` rather than a stale cache; rebuild only if
   the check shows drift.
3. **T3/T4 — Direct vLLM-Omni T2I**, FP8 then NVFP4, sequential (the compose
   overlays share a fixed container name, so one stack runs at a time via
   `make down` between them).
4. **T5/T6 — Full-stack T2I** through the api (`X-API-Key` -> job ->
   artifact), FP8 then NVFP4.
5. **T7 — T2V smoke**, best-effort, direct-only (`session_3.md` does not
   require full-stack for T2V): NVFP4 attempted first for VRAM headroom,
   falling back to FP8 or recording a scoped-out reason if neither fits in
   32 GB.
6. **T8 — Evidence and doc updates** (not a probe): aggregate evidence into
   `docs/evidence_map.md`, close/update rows in `docs/eval_seed_cases.md`,
   upgrade per-mode markings in `docs/model_setup.md`,
   `docs/release_checklist.md`, and `README.md`, update
   `docs/risk_register.md`, write `docs/handoff.md`.

### Probe architecture (`docs/session_3/probes/`)

- `lib.py` — pure calculations only: an `EvidenceRecord` data shape (hardware,
  driver/CUDA, checkpoint repo+revision, vLLM-Omni commit, request shape,
  artifact metadata, pass/fail, notes) plus pure checkers
  (`check_no_lfs_pointers`, `check_valid_image`, `check_job_terminal`). No
  side effects — testable without touching the GPU.
- `run_checkpoint_fetch.py`, `run_direct_t2i.py --checkpoint {fp8,nvfp4}`,
  `run_fullstack_t2i.py --checkpoint {fp8,nvfp4}`,
  `run_t2v_smoke.py --checkpoint {fp8,nvfp4}` — each is the action (download /
  compose lifecycle / HTTP calls), each calls the pure checkers, each writes
  its own `evidence_*.json` fragment. Independently re-runnable.
- `aggregate.py` — pure merge of all fragments into `probes/evidence.json` +
  `probes/summary.md`, matching `GPU-S2`'s deliverable shape.

### Evidence flow

`probes/evidence.json` is the single source of truth. Every doc update
(`evidence_map.md`, `eval_seed_cases.md`, `model_setup.md`,
`release_checklist.md`, `README.md`) is derived from it, never the reverse —
matching `project_contract.md` §7's "claims must point to an evidence row"
rule.

### Failure routing

Per `project_contract.md` §5, the human gate for `GPU-S3` fires "on T2I/T2V
failure or a drift-D1 recurrence":

- A T2I failure (either checkpoint, direct or full-stack) or a drift-D1
  recurrence -> stop, classify with the Failure Arbiter, bring it to the
  owner before deciding next steps.
- A T2V failure -> recorded as a known limitation per `session_3.md`'s SHOULD
  wording (not a MUST); reported, but does not block the session.

## Approved

Design approved by the owner in this session's conversation. Proceeding to
the proposal/design/spec/tasks/plan/execution-contract pack.
