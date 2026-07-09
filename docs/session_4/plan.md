# GPU-S4 Quant Loader Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Answer the upstream-state question and, if needed, publish a clean `fengwang/vllm-omni` branch with only model-agnostic FP8/NVFP4 quant-loader support.

**Architecture:** This repository stores the control artifacts and evidence. The external fork at `<external-vllm-omni-checkout>` stores code changes on a branch based on current upstream `main`. The implementation imports a narrow quant-loader slice from fork pin `697035018b70cef76b974a909d23371a9984c3f2`, then proves compile and no Cosmos3 dependency.

**Tech Stack:** Git, Python, pytest, vLLM-Omni, PyTorch CPU tests, `rg`, `compileall`.

---

## File Structure

- Create: `docs/session_4/upstream_state.md`, upstream-state evidence.
- Create: `docs/session_4/branch_notes.md`, branch construction, conflicts, semantic drift.
- Create: `docs/session_4/checks.md`, command results and failure classifications.
- Create: `docs/session_4/sharded_review.md`, medium-risk review results.
- Create: `docs/session_4/adversarial_verification.md`, fresh-context verifier result.
- Modify: `docs/evidence_map.md`, final evidence row.
- Modify: `docs/risk_register.md`, `R-06` and `R-07` state.
- Modify: `docs/eval_seed_cases.md`, eval seeds if this session catches or misses a gap.
- Modify: `docs/handoff.md`, next-session handoff.
- External create/modify: `<external-vllm-omni-checkout>` branch `gpu-s4-quant-loader-isolation` or a date-suffixed fallback.
- External modify: quant-loader files and narrow tests listed in `docs/session_4/proposal.md`.

## Task 1: Upstream State Finding

**Files:**

- Create: `docs/session_4/upstream_state.md`
- External read/write git metadata only: `<external-vllm-omni-checkout>/.git/config`, refs from fetch

- [ ] **Step 1: Verify external checkout state**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git remote -v
```

Expected: clean working tree at `697035018b70cef76b974a909d23371a9984c3f2`.

- [ ] **Step 2: Add upstream remote only if missing**

Run:

```bash
cd <external-vllm-omni-checkout>
if ! git remote get-url upstream >/dev/null 2>&1; then
  git remote add upstream https://github.com/vllm-project/vllm-omni.git
fi
rtk git remote -v
```

Expected: `upstream` fetch URL is `https://github.com/vllm-project/vllm-omni.git`.

- [ ] **Step 3: Fetch upstream**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk git fetch upstream
rtk git rev-parse upstream/main
```

Expected: command exits 0 and prints the fetched upstream SHA.

- [ ] **Step 4: Run upstream exact searches**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk git log --oneline upstream/main -- vllm_omni/quantization
rtk rg -n "fp8_blockwise|nvfp4_blockwise|modelopt_native|ModelOptNative|NvFp4|FP8" vllm_omni
```

Expected: results are recorded. If exact files or equivalent code exist, inspect before creating any branch commit.

- [ ] **Step 5: Write the finding**

Create `docs/session_4/upstream_state.md` with this structure:

````markdown
# Upstream State Finding

## Refs

- Fork pin:
- Upstream main:

## Commands

```bash
...
```

## Findings

- Exact filename matches:
- Semantic ModelOpt/FP8/NVFP4 matches:

## Conclusion

- Result: `missing` or `already-covered`
- Rationale:
````

Run:

```bash
cd <webui-repo>
rtk rg -n "Result: `missing`|Result: `already-covered`" docs/session_4/upstream_state.md
```

Expected: one result line.

Commit point: no commit required in this repository. If upstream is already covered, skip Tasks 2 and 3 and continue with Task 4 documentation only.

## Task 2: Isolated Branch Construction

**Files:**

- External create/modify in `<external-vllm-omni-checkout>`
- Create: `docs/session_4/branch_notes.md`

- [ ] **Step 1: Create branch from upstream main**

Run:

```bash
cd <external-vllm-omni-checkout>
BRANCH=gpu-s4-quant-loader-isolation
if git show-ref --verify --quiet refs/heads/$BRANCH; then
  BRANCH=gpu-s4-quant-loader-isolation-$(date +%Y%m%d)
fi
git switch -c "$BRANCH" upstream/main
rtk git merge-base HEAD upstream/main
rtk git rev-parse upstream/main
```

Expected: merge-base equals `upstream/main`.

- [ ] **Step 2: Import narrow tests first**

Run:

```bash
cd <external-vllm-omni-checkout>
PIN=697035018b70cef76b974a909d23371a9984c3f2
git checkout "$PIN" -- \
  tests/diffusion/quantization/test_fp8_blockwise_w8a16.py \
  tests/diffusion/model_loader/test_modelopt_native.py \
  tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py \
  tests/diffusion/model_loader/test_modelopt_native_nvfp4.py \
  tests/model_executor/quantization/test_nvfp4_blockwise_config.py \
  tests/model_executor/quantization/test_modelopt_nvfp4_nan_clamp.py
```

Expected: tests are CPU-only and self-contained. If a checked-out test imports `vllm_omni.diffusion.models.cosmos3`, remove that test from this branch and record why.

- [ ] **Step 3: Run the first RED test**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk python -m pytest -q tests/diffusion/quantization/test_fp8_blockwise_w8a16.py
```

Expected: FAIL during collection or import because upstream `main` does not yet have `vllm_omni.quantization.fp8_blockwise_w8a16`.

- [ ] **Step 4: Import candidate files from fork pin**

Run one file at a time so failures are easy to classify:

```bash
cd <external-vllm-omni-checkout>
PIN=697035018b70cef76b974a909d23371a9984c3f2
git checkout "$PIN" -- \
  vllm_omni/quantization/fp8_blockwise_w8a16.py \
  vllm_omni/quantization/nvfp4_blockwise.py \
  vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt.py \
  vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native.py \
  vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native_fp8_w8a16.py \
  vllm_omni/diffusion/model_loader/checkpoint_adapters/modelopt_native_nvfp4.py
```

Expected: files are staged in the working tree only, not committed.

- [ ] **Step 5: Import registration hooks with review**

Run:

```bash
cd <external-vllm-omni-checkout>
PIN=697035018b70cef76b974a909d23371a9984c3f2
git checkout "$PIN" -- \
  vllm_omni/quantization/__init__.py \
  vllm_omni/quantization/factory.py \
  vllm_omni/quantization/component_config.py \
  vllm_omni/diffusion/model_loader/checkpoint_adapters/__init__.py
rtk git diff -- vllm_omni/quantization/__init__.py vllm_omni/quantization/factory.py vllm_omni/quantization/component_config.py vllm_omni/diffusion/model_loader/checkpoint_adapters/__init__.py
```

Expected: diff is limited to registration of imported quant methods and adapters. If unrelated upstream registrations disappear, classify as BUG before fixing.

- [ ] **Step 6: Import only the NVFP4 NaN-clamp hunk if needed**

Inspect first:

```bash
cd <external-vllm-omni-checkout>
PIN=697035018b70cef76b974a909d23371a9984c3f2
rtk git show "$PIN:vllm_omni/patch.py" | rg -n "nvfp4|weight_scale|NaN|clamp|ModelOptNvFp4"
rtk rg -n "nvfp4|weight_scale|NaN|clamp|ModelOptNvFp4" vllm_omni/patch.py
```

If upstream already has the clamp, do not edit `vllm_omni/patch.py`. If a targeted test proves a missing behavior, edit `vllm_omni/patch.py` with the smallest hunk that provides the clamp and self-extinguish behavior. Do not copy unrelated fork patches.

Expected: either no `patch.py` diff, or `git diff -- vllm_omni/patch.py` shows only NVFP4 clamp support.

- [ ] **Step 7: Run scope sweeps before committing**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk git diff --name-only upstream/main...HEAD
rtk git diff --name-only | rg -n "cosmos3|Cosmos3" || true
rtk git diff | rg -n "cosmos3|Cosmos3|COSMOS3|docs/session_[0-9]|/data/|/workspace/" || true
```

Expected: no forbidden Cosmos3 runtime dependency remains in the imported slice. Documentation references in tests are removed or rewritten if they point to this repository's old session docs.

- [ ] **Step 8: Commit isolated code**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk git status --short
git add vllm_omni tests
git commit -s -m "feat: add model-agnostic FP8/NVFP4 quant loaders"
rtk git rev-parse HEAD
```

Expected: signed-off commit exists on the isolated branch.

## Task 3: Targeted Verification And Fixes

**Files:**

- Create: `docs/session_4/checks.md`
- Update: `docs/session_4/branch_notes.md`
- External modify only if Failure Arbiter classifies a fix as allowed

- [ ] **Step 1: Run targeted pytest**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk python -m pytest -q \
  tests/diffusion/quantization/test_fp8_blockwise_w8a16.py \
  tests/diffusion/model_loader/test_modelopt_native.py \
  tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py \
  tests/diffusion/model_loader/test_modelopt_native_nvfp4.py \
  tests/model_executor/quantization/test_nvfp4_blockwise_config.py \
  tests/model_executor/quantization/test_modelopt_nvfp4_nan_clamp.py
```

Expected: pass, skip for explicitly unsupported optional upstream ModelOpt imports, or failure classified before any fix.

- [ ] **Step 2: Run compileall**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk python -m compileall vllm_omni
```

Expected: exit 0.

- [ ] **Step 3: Run no-Cosmos3 and no-secret sweeps**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk git diff --name-only upstream/main...HEAD
rtk git diff upstream/main...HEAD | rg -n "cosmos3|Cosmos3|COSMOS3|HF_TOKEN|/data/|/workspace/|private" || true
```

Expected: no forbidden dependency, secret, private path, or model-specific runtime code in the diff.

- [ ] **Step 4: Classify failures before fixes**

If a command fails, append to `docs/session_4/failure_arbiter.md`:

```markdown
## FA-<n>: <command>

- Category:
- Evidence:
- Why other categories do not fit:
- Allowed next action:
- Forbidden next action:
```

Then apply only the allowed next action.

- [ ] **Step 5: Record checks**

Create `docs/session_4/checks.md` with:

```markdown
# Session 4 Checks

| Check | Workspace | Result | Notes |
|---|---|---|---|
| upstream fetch | external fork | PASS | upstream/main = ... |
| upstream state searches | external fork | PASS | ... |
| targeted pytest | external fork | PASS | ... |
| compileall | external fork | PASS | ... |
| no-Cosmos3 sweep | external fork | PASS | ... |
```

Expected: each final check has a result and notes.

Commit point: if external fixes were made after the first commit, create a second signed-off fix commit with a narrow message.

## Task 4: Branch Publication And Documentation

**Files:**

- Update: `docs/session_4/branch_notes.md`
- Update: `docs/evidence_map.md`
- Update: `docs/risk_register.md`
- Update: `docs/eval_seed_cases.md` if a caught or missed issue exists
- Create: `docs/session_4/sharded_review.md`
- Create: `docs/session_4/adversarial_verification.md`
- Update: `docs/handoff.md`

- [ ] **Step 1: Push the external branch**

Run:

```bash
cd <external-vllm-omni-checkout>
BRANCH=$(git branch --show-current)
git push -u origin "$BRANCH"
rtk git rev-parse HEAD
rtk git status --short --branch
```

Expected: branch tracks `origin/$BRANCH`; working tree is clean.

- [ ] **Step 2: Write branch notes**

Create `docs/session_4/branch_notes.md` with:

```markdown
# Branch Notes

## Branch

- Remote:
- Branch:
- Commit:
- Base upstream main:

## Conflict Notes

- None, or listed by file with resolution.

## Semantic Drift

- Upstream changes that affected the import:

## Scope Proof

- Files changed:
- Cosmos3 sweep:
```

- [ ] **Step 3: Update evidence and risks**

Add an evidence row to `docs/evidence_map.md` for `GATE-GPU-S4-UPSTREAM-SCOPE`. Update `R-06` and `R-07` in `docs/risk_register.md` with the final result.

- [ ] **Step 4: Run sharded review**

Review axes:

- Correctness
- Security/safety
- Tests
- Architecture/maintainability
- Performance

Save actionable findings to `docs/session_4/sharded_review.md`.

- [ ] **Step 5: Fix only High or Critical review findings**

For each High or Critical finding, classify if it is a failure. Apply the smallest safe fix, re-run the targeted check that proves the fix, and update `docs/session_4/checks.md`.

- [ ] **Step 6: Run adversarial verification**

Use only the session contract, project contract, external branch diff, and check evidence. Save to `docs/session_4/adversarial_verification.md` with verdict `PASS` or `FAIL`.

- [ ] **Step 7: Final checks**

Run:

```bash
cd <webui-repo>
rtk make scan
rtk git status --short
cd <external-vllm-omni-checkout>
rtk git status --short --branch
```

Expected: `make scan` passes; both working trees are clean except intended documentation changes in this repository if not committed.

- [ ] **Step 8: Update handoff**

Update `docs/handoff.md` using `docs/agent_workflow/templates/handoff.md`. Include checks run, checks not run, branch name, commit, remaining risks, and next-session warnings.

## Self-Review

- Spec coverage: Task 1 covers upstream-state finding, Task 2 covers quant-loader isolation, Task 3 covers rebased branch verification, and Task 4 covers publication and handoff.
- Placeholder scan: no task relies on unspecified test commands or unnamed files.
- Type and name consistency: branch name, spec names, and file paths match the proposal and execution contract.
