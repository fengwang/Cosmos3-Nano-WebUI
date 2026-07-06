# Session 2 Brainstorming - vLLM-Omni Patch Rebase And Public Pin

Date: 2026-07-06
Session: MIG-S2
Risk: high
Status: Approved by owner

## Context Read

Read before editing:

- `docs/prd.md`
- `docs/session_2.md`
- `docs/session_2_contract.yaml`
- `docs/project_contract.md`
- `docs/evidence_map.md`
- `docs/handoff.md`
- `docs/risk_register.md`
- `docs/eval_seed_cases.md`
- workflow prompts under `docs/agent_workflow/prompts/`

The dominant requirement is PRD FR-3: the Cosmos3 `vllm-omni` patch line must be
available in the public GitHub fork and pinned by commit or tag before the WebUI
repo depends on it.

## Startup Evidence

WebUI repo:

- Branch: `session-2`
- State: clean at startup
- Remote: `git@github.com:fengwang/Cosmos3-Nano-WebUI.git`
- Recent commits: Session 1 docs and handoff followed by branch setup

Public vLLM-Omni fork:

- Local checkout: `/workspace/github.repo/vllm-omni`
- Remote: `git@github.com:fengwang/vllm-omni.git`
- Branch: `main`
- State: clean at startup
- Public base: `d4a869fe5e2edd49af48026051948c8d1018d727`

Authorized patch source selected by owner:

- Source: owner-authorized local historical checkout, intentionally not recorded
  in public docs.
- Patch range: owner-provided local range, intentionally not recorded in public
  docs.
- Commit count: 8

Baseline checks:

- WebUI `rtk python -m compileall vllm_omni`: failed because this repo does not
  contain fork source.
- WebUI targeted pytest command: failed because this repo does not contain fork
  tests.
- Fork `rtk python -m compileall vllm_omni`: passed.
- Fork targeted pytest command: failed before collection because the global
  Python environment lacks `aenum`, which is declared in
  `/workspace/github.repo/vllm-omni/requirements/common.txt`.

## Clarifications

1. Patch source: owner selected an authorized local historical checkout and
   eight-commit range. Private source path, branch, and source hashes are not
   recorded in public docs.
2. Publication policy: owner selected pushing both a public branch and stable tag.
3. Public names: owner selected branch `mig-s2-cosmos3-quant-pin` and tag
   `cosmos3-nano-webui-mig-s2`.
4. Test environment: owner selected an isolated venv at
   `/workspace/github.repo/vllm-omni/.venv-mig-s2`.
5. History policy: owner selected preserving the 8 patch commits.

## Approaches Considered

### A. Branch-and-compare rebase with preserved commits

Rebase or cherry-pick the 8 selected commits onto public fork `origin/main`,
resolve only in contract-approved Cosmos3, checkpoint adapter, quantization, and
test surfaces, run deterministic checks in an isolated venv, then push a public
branch and tag.

Trade-offs:

- Best traceability to the original patch series.
- Best fit for conflict notes and review.
- More conflict work than a squash if upstream has moved significantly.

Decision: selected.

### B. Squash into one public commit

Apply the same final diff as one commit.

Trade-offs:

- Cleaner public history.
- Weaker traceability to the original commits and conflict resolutions.
- Harder to review in a high-risk dependency session.

Decision: rejected.

### C. Prepare locally only

Rebase and test locally without pushing.

Trade-offs:

- Useful fallback if push authentication fails.
- Does not satisfy the public-pin acceptance criterion.

Decision: fallback only.

## Approved Design

Use `/workspace/github.repo/vllm-omni` as the public fork checkout. Create branch
`mig-s2-cosmos3-quant-pin` from `origin/main` at
`d4a869fe5e2edd49af48026051948c8d1018d727`. Cherry-pick the eight authorized
local commits in order, preserving commit boundaries while omitting private
source hashes from committed docs.

Keep code edits within the contract surfaces:

- `vllm_omni/diffusion/model_loader/checkpoint_adapters/**`
- `vllm_omni/diffusion/model_loader/diffusers_loader.py`
- `vllm_omni/diffusion/models/cosmos3/**`
- `vllm_omni/quantization/**`
- matching fork tests for touched surfaces

Use the isolated venv `.venv-mig-s2` for targeted tests. If missing optional
runtime dependencies, CUDA, or model weights block a check, classify the failure
before changing source. Do not change WebUI runtime source during this session.

Publish branch `mig-s2-cosmos3-quant-pin` and tag
`cosmos3-nano-webui-mig-s2` only after deterministic checks and review have a
clear disposition.

## Functional And Concept Notes

The main concept is `PublicForkPin`: it exists to give later WebUI Docker/build
work an immutable public dependency target. It synchronizes three independent
concepts:

- `PatchLine`: authorized commit series and conflict resolutions.
- `ForkVerification`: compile and targeted tests.
- `DependencyPin`: public branch/tag and install command.

Implementation follows ACD:

- Data: base commit, patch commits, conflict notes, test outputs, final pin.
- Calculations: diff comparison, expected file list, test path mapping, install
  command construction.
- Actions: branch creation, cherry-pick/rebase, dependency install, pytest,
  compileall, git push/tag.

## Approved Risks

- Current fork base is ahead of the source patch base; conflicts are likely.
- Targeted tests named by the contract include one stale path compared with the
  authorized patch source. The execution contract will resolve this explicitly.
- The environment may remain unable to run some tests if heavyweight optional
  dependencies or CUDA are required.
- Public push/tag must be verified with `git ls-remote`; a local branch alone is
  insufficient.
