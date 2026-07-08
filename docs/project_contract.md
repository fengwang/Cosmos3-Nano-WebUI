# Project Contract - GPU Release Readiness and Upstream Quant Contribution

Date: 2026-07-08
Status: Active blueprint (first pass)

Compilation: two-pass. The first pass drafted from
`docs/archive/phase-1/next_phase_handoff.md`, the archived Phase-1 evidence
trail (`risk_register.md`, `evidence_map.md`, `model_setup.md`,
`release_checklist.md`, `handoff.md`), and owner decisions made while
brainstorming this blueprint. The second pass, an independent adversarial
spec review, found and fixed a gate-satisfaction contradiction between
`GATE-GPU-S4-UPSTREAM-SCOPE` and `GATE-GPU-S5-PR`, a self-defeating re-pin
sweep check, cross-references broken by the Phase-1 archive move, and
several smaller ambiguities across the pack. This document is the revised
output only.

Authority chain: read this file before implementing any Phase-2 session.
Session-specific authority comes from `docs/session_{n}_contract.yaml`. If a
session contract conflicts with this file, stop and record the conflict
before editing.

## 1. Objective

Close the three gaps deferred at the end of Phase-1: make
`deploy/vllm-omni.Dockerfile` build from public inputs, fix the published
`wfen/*` Hugging Face checkpoints so they clone and load cleanly, and either
land a decoupled FP8/NVFP4 blockwise quant contribution in
`vllm-project/vllm-omni` or record why none is needed. Prove the combined
result end to end on GPU hardware before considering any of it done.

## 2. Hard Commitments

1. **Session identity:** session contracts are `GPU-S1` through `GPU-S5`.
2. **Fresh-verification discipline:** a checkpoint or Dockerfile fix is not
   accepted as done on the strength of an already-patched local checkout. It
   must be proven from a fresh `git clone` / `hf download` / image pull.
3. **Atomic re-pin discipline:** when a Hugging Face checkpoint revision
   changes, every reference to it anywhere in this repository is updated in
   the same session — at minimum `docs/model_setup.md` §1,
   `docs/evidence_map.md`, `docs/release_checklist.md` §7, and
   `docs/eval_seed_cases.md` — verified by a whole-repository sweep, not only
   those four files. No session ends with a partially-repinned state.
4. **Upstream decoupling:** any code proposed to `vllm-project/vllm-omni`
   contains no Cosmos3-specific model, adapter, or guard code, and must not
   require the Cosmos3 model to build or pass CI.
5. **Outward-action gate:** pushing to either `wfen/*` Hugging Face repo and
   opening the upstream pull request each require an explicit owner
   go-ahead recorded immediately before that action, not merely a passing
   automated check.
6. **No API/runtime regression:** existing public API shapes, WebUI
   behavior, and non-quant vLLM-Omni runtime paths are unchanged unless a
   session contract explicitly allows it and tests cover it.
7. **External-repo blast radius:** work that happens in the
   `fengwang/vllm-omni` fork or in `vllm-project/vllm-omni` upstream is
   tracked here by reference (commit, branch, or PR URL) and is out of this
   repository's blast radius; it does not authorize edits to this
   repository's runtime source.
8. **Archive boundary:** `docs/archive/phase-1/**` is historical record and
   is not edited by Phase-2 sessions.

## 3. Invariants

- **INV-1:** No secret, token, private host, private absolute path, or model
  weight is committed to this repository or to the `vllm-omni` fork as part
  of this work.
- **INV-2:** `deploy/vllm-omni.Dockerfile` never bakes model weights;
  checkpoints stay external and are mounted by revision.
- **INV-3:** `deploy/vllm-omni.Dockerfile` installs the vLLM-Omni fork by
  immutable commit SHA, never by a mutable branch name.
- **INV-4:** A Hugging Face checkpoint fix is verified against a fresh clone
  or `hf download`, independent of any local, already-patched checkout.
- **INV-5:** `docs/model_setup.md` §1, `docs/evidence_map.md`,
  `docs/release_checklist.md` §7, and `docs/eval_seed_cases.md` agree on
  every pinned checkpoint revision at all times after a re-pin session
  closes, and no other tracked file retains the superseded revision.
- **INV-6:** Any upstream-facing quant code compiles and its tests pass
  without importing or depending on Cosmos3-specific code.
- **INV-7:** No push to an external `wfen/*` Hugging Face repo, and no
  upstream pull request, happens without a recorded owner go-ahead
  immediately preceding that action.
- **INV-8:** Every manual GPU claim records hardware, driver/CUDA context,
  checkpoint repo and revision, vLLM-Omni commit, request shape, artifact
  metadata, and pass/fail result.

## 4. Gates

- **GATE-GPU-S1-DOCKERFILE:** `deploy/vllm-omni.Dockerfile` builds from
  public inputs, serves `/v1/models`, and generates a T2I artifact on the
  target GPU; the local-image stopgap has a recorded disposition.
- **GATE-GPU-S2-CHECKPOINT:** both `wfen/*` checkpoint repos load cleanly
  from a fresh clone/download, and every in-repo pinned reference matches
  the new revisions.
- **GATE-GPU-S3-VALIDATION:** a fresh `hf download` at the `GPU-S2`
  revisions, through the `GPU-S1` image, proves FP8 and NVFP4 T2I end to end
  (direct and full-stack) with no manual workaround; a T2V attempt is
  recorded either way.
- **GATE-GPU-S4-UPSTREAM-SCOPE:** the upstream-state question is answered
  with evidence before any contribution code exists; if proceeding, an
  isolated, rebased, compiling feature branch exists with no Cosmos3-specific
  code in it.
- **GATE-GPU-S5-PR:** `precheck-pr` is clean, CI is green, DCO sign-off is
  present, and either the PR is open with a recorded owner go-ahead, or the
  session records why it did not proceed.

## 5. Session Routing

Risk classification follows the requested risk router.

| Session | Risk | Routing | Human gate |
|---|---|---|---|
| GPU-S1 Dockerfile build | high | branch_and_compare | On a build-failure class that needs a base-image change |
| GPU-S2 Checkpoint fix and re-pin | high | branch_and_compare | Before pushing to either `wfen/*` repo |
| GPU-S3 Joint validation | high | branch_and_compare | On T2I/T2V failure or a drift-D1 recurrence |
| GPU-S4 Upstream state and isolation | medium | worker_plus_reviewers | On a semantic conflict needing Cosmos3-specific judgment |
| GPU-S5 precheck-pr and PR submission | high | branch_and_compare | Mandatory, immediately before the PR is opened |

High-risk sessions require deterministic checks, sharded review over the
review axes, adversarial verification of claims, and the named human gate
before the session's done condition is accepted.

## 6. Change Control

- Do not edit outside a session contract's `blast_radius.allowed_files`.
- Do not add model weights, generated media, caches, or bulky archives to
  this repository.
- Do not edit `docs/archive/phase-1/**`.
- Do not push to a `wfen/*` Hugging Face repo, or open a pull request
  against `vllm-project/vllm-omni`, without the recorded owner go-ahead
  required by Hard Commitment 5.
- Do not change public API route shapes, request/response schemas, or WebUI
  behavior during this work.
- Treat `deploy/**`, pinned Hugging Face revisions, and the vLLM-Omni fork
  commit pin as change-controlled surfaces: any change to one requires an
  equivalent same-session, whole-repository sweep of every file that cites
  the changed pin, in the same spirit as Hard Commitment 3.

## 7. Verification Policy

- Classify failures before fixing: BUG, SPEC_GAP, AMBIGUITY, ENVIRONMENT, or
  TEST_BUG (`docs/agent_workflow/prompts/failure_arbiter.md`).
- Prefer deterministic evidence: fresh `git clone`/`hf download` output,
  `docker compose config`/`build`/`up` results, `python -m compileall`,
  targeted test runs, and `rg` sweeps for stale pins.
- GPU checks are manual, recorded gates. Record hardware, driver/CUDA
  context, checkpoint repo and revision, vLLM-Omni commit, request shape,
  artifact metadata, and result (INV-8).
- Claims in `docs/model_setup.md` and `docs/release_checklist.md` must point
  to an evidence row in `docs/evidence_map.md` or be phrased as a limitation.

## 8. Done Condition

This blueprint's session set is done when `GATE-GPU-S1-DOCKERFILE` through
`GATE-GPU-S3-VALIDATION` all pass; `GATE-GPU-S4-UPSTREAM-SCOPE` is satisfied
by a recorded, evidenced upstream-state finding (with an isolated, rebased,
compiling feature branch if that finding is "proceed"); and
`GATE-GPU-S5-PR` is satisfied either by an open, DCO-signed, CI-green pull
request or by a documented, owner-accepted finding that no pull request was
needed. `docs/risk_register.md`, `docs/evidence_map.md`, and
`docs/eval_seed_cases.md` must reflect the final state of every session that
has closed.
