# Session 4 - Upstream State Check and Quant-Patch Isolation/Rebase

Contract: `docs/session_4_contract.yaml`
Risk: medium
Routing: worker_plus_reviewers

## Objective

Determine whether `vllm-project/vllm-omni` `main` already implements
FP8/NVFP4 blockwise quant or ModelOpt-native detection; if not, isolate the
model-agnostic quant loader files from Cosmos3-specific code and rebase them
onto current upstream `main` on a `fengwang/vllm-omni` fork feature branch.

## Why This Session Exists

The upstream contribution is the highest-risk, most outward-facing of the
three deferred tasks — a public contribution to a major project, attributed
to the owner. Checking upstream state first avoids wasted rebase and PR work
if the feature already exists, and isolating model-agnostic code from
Cosmos3-specific code before any PR-facing work reduces the risk of the
eventual PR being rejected for scope reasons. This session does the
investigative and git-mechanical work; it does not submit anything.

## In Scope

1. Inspect `vllm-project/vllm-omni` `main` for existing FP8/NVFP4 blockwise
   quant support or ModelOpt-native detection.
2. If missing, identify the candidate files from the fork at pin
   `697035018b70cef76b974a909d23371a9984c3f2`:
   `vllm_omni/quantization/{fp8_blockwise_w8a16.py,nvfp4_blockwise.py}`,
   registration hooks in
   `vllm_omni/quantization/{__init__.py,factory.py,component_config.py}`,
   `vllm_omni/diffusion/model_loader/checkpoint_adapters/{modelopt.py,
   modelopt_native.py,modelopt_native_fp8_w8a16.py,modelopt_native_nvfp4.py}`,
   and the isolated NVFP4 W4A4 `weight_scale` NaN-clamp hunk in
   `vllm_omni/patch.py`.
3. Isolate those files and hunks from Cosmos3-specific code on a feature
   branch of the `fengwang/vllm-omni` fork.
4. Rebase the isolated commits onto current upstream `main`.
5. Record conflict resolutions and any semantic drift between the fork's
   base and current upstream.

## Out of Scope

- Opening any pull request (`GPU-S5`).
- Running the fork's `precheck-pr` skill (`GPU-S5`) — that gate runs against
  the near-final branch, after isolation is settled.
- Any change to this repository's runtime source, Dockerfile, or
  checkpoints.
- Adding unit tests for the quant methods (`GPU-S5`, alongside the CI and
  hygiene pass).

## Deliverables

- A recorded, evidenced answer to "does upstream already have this."
- If proceeding: an isolated, rebased feature branch on the
  `fengwang/vllm-omni` fork containing only model-agnostic quant loader
  code.
- Conflict-resolution notes and any semantic-drift findings.

## Deterministic Checks

```bash
git remote add upstream https://github.com/vllm-project/vllm-omni.git   # one-time, if not already present
git fetch upstream
git log upstream/main -- vllm_omni/quantization
rtk rg -n "fp8_blockwise|nvfp4_blockwise|modelopt_native" vllm_omni
git rebase upstream/main <isolated feature branch>
python -m compileall vllm_omni
```

These commands run against the `fengwang/vllm-omni` fork checkout, not this
repository.

## Exit Criteria

- `GATE-GPU-S4-UPSTREAM-SCOPE` passes.
- Either: upstream already covers the contribution, and this is documented
  as the done condition (`GPU-S5` is then skipped); or: an isolated,
  rebased, compiling feature branch exists with no Cosmos3-specific code in
  it.
- Any semantic conflict is resolved with recorded reasoning, or explicitly
  escalated for owner input.

## Handoff

Hand off the upstream-state finding and, if applicable, the isolated feature
branch name/commit and conflict notes to `GPU-S5`.
