# GPU-S5 PR Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the isolated quant-loader branch through precheck, local CI evidence, DCO, owner-gated PR creation, and post-PR check recording.

**Architecture:** This repository stores session artifacts and evidence. The external fork at `<external-vllm-omni-checkout>` stores branch changes and runs contribution checks. PR creation is a GitHub Action guarded by an immediate owner approval synchronization point.

**Tech Stack:** Git, GitHub CLI, Python 3.12 venv in the external fork, pytest, pre-commit, vLLM-Omni build scripts, `rg`, `compileall`.

---

## File Structure

- Create/modify: `docs/session_5/brainstorming.md`, approved design and startup checks.
- Create/modify: `docs/session_5/proposal.md`, capability contract.
- Create/modify: `docs/session_5/design.md`, implementation design.
- Create/modify: `docs/session_5/specs/submission-branch-freshness.md`, branch freshness requirements.
- Create/modify: `docs/session_5/specs/precheck-and-local-ci.md`, precheck/local CI requirements.
- Create/modify: `docs/session_5/specs/owner-gated-pr-submission.md`, DCO/PR gate requirements.
- Create/modify: `docs/session_5/tasks.md`, coarse task checklist.
- Create/modify: `docs/session_5/plan.md`, this executable plan.
- Create/modify: `docs/session_5/execution_contract.md`, implementation contract.
- Create/modify: `docs/session_5/checks.md`, command evidence.
- Create/modify: `docs/session_5/precheck_quick.md`, quick-mode report.
- Create/modify: `docs/session_5/precheck_full.md`, full-mode report.
- Create/modify: `docs/session_5/pr_record.md`, PR metadata, owner gate, URL, checks.
- Create/modify: `docs/session_5/sharded_review.md`, high-risk review.
- Create/modify: `docs/session_5/adversarial_verification.md`, verifier result.
- Create/modify: `docs/session_5/failure_arbiter.md`, only if a failure needs classification.
- Modify: `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/handoff.md`.
- External fork: modify only the existing `GPU-S4` quant-loader branch files if precheck/local CI produces concrete in-scope failures.

## Task 1: Submission Branch Freshness

**Files:**

- Create/modify: `docs/session_5/checks.md`
- External checkout: `<external-vllm-omni-checkout>` git refs and possibly branch history

- [ ] **Step 1: Fetch upstream and record starting refs**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk git status --short --branch
rtk git fetch upstream
rtk git rev-parse HEAD
rtk git rev-parse upstream/main
rtk git merge-base HEAD upstream/main
```

Expected: working tree clean. Record HEAD, upstream main, and merge-base in `docs/session_5/checks.md`.

- [ ] **Step 2: Verify current branch freshness test fails or passes**

Run:

```bash
cd <external-vllm-omni-checkout>
test "$(git merge-base HEAD upstream/main)" = "$(git rev-parse upstream/main)"
```

Expected before rebase in this environment: nonzero, because upstream advanced. Classify as expected branch-freshness precondition, not product BUG.

- [ ] **Step 3: Attempt clean rebase**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk git rebase upstream/main
```

Expected: exits 0. If it conflicts, stop, write `docs/session_5/failure_arbiter.md` entry with category AMBIGUITY or BUG as appropriate, run `git rebase --abort`, and route back to `GPU-S4`.

- [ ] **Step 4: Verify branch freshness passes**

Run:

```bash
cd <external-vllm-omni-checkout>
test "$(git merge-base HEAD upstream/main)" = "$(git rev-parse upstream/main)"
rtk git status --short --branch
rtk git log --oneline upstream/main..HEAD
```

Expected: merge-base equals upstream main; working tree clean; branch commits are the quant contribution commits.

- [ ] **Step 5: Run post-rebase scope sweeps**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk git diff --name-only upstream/main...HEAD
rtk proxy bash -lc 'git diff upstream/main...HEAD | rg -n "cosmos3|Cosmos3|COSMOS3|docs/session_[0-9]|/(data|workspace)/|HF_TOKEN|wfen|private" && exit 1 || test $? = 1'
rtk git diff --check upstream/main...HEAD
```

Expected: changed files stay within quant-loader/config/test scope; forbidden sweep exits 0 by finding no matches; diff check exits 0.

Commit point: rebase rewrites branch history; do not create a main-repo commit yet.

## Task 2: Precheck And Local CI Gate

**Files:**

- Create/modify: `docs/session_5/precheck_quick.md`
- Create/modify: `docs/session_5/precheck_full.md`
- Create/modify: `docs/session_5/checks.md`
- External modify: only in-scope files if a blocker is proven

- [ ] **Step 1: Decide PR title candidate**

Use upstream docs, precheck prefixes, and live quantization PR title patterns. Final candidate after sharded review:

```text
[Core][Quantization] Add ModelOpt-native FP8/NVFP4 blockwise loaders
```

Record the candidate and rationale. `[Core]` satisfies the static precheck first-prefix list; `[Quantization]` reflects current upstream quantization PR practice.

- [ ] **Step 2: Run quick precheck manually from the skill checklist**

Run:

```bash
cd <external-vllm-omni-checkout>
BASE="$(git merge-base HEAD upstream/main)"
rtk git diff --name-only "$BASE"...HEAD
rtk git diff "$BASE"...HEAD -- "*.py" | grep "^+[^+]" | grep -E '\*\*kwargs|kwargs(\.get|\[)|"[a-z_]+"\s+in\s+kwargs' || true
rtk git diff "$BASE"...HEAD -- "*.py" | grep "^+[^+]" | grep -E 'except\s*(Exception|BaseException)?\s*:' || true
rtk git diff "$BASE"...HEAD -- "*.py" | grep "^+[^+]" | grep -E ':\s*Any\b|->\s*Any\b' || true
rtk git diff "$BASE"...HEAD -- "tests/" | grep "^+[^+]" | grep "SimpleNamespace" || true
rtk git diff "$BASE"...HEAD -- "*.py" | grep "^+[^+]" | grep -E '\.clone\(\)|\.copy_\(|copy\.deepcopy|deepcopy\(' || true
rtk git diff "$BASE"...HEAD -- "*.py" | grep "^+[^+]" | grep -E 'time\.sleep|requests\.(get|post|put|delete)|urllib\.request|urlopen|async with|\.acquire\(\)' || true
```

Expected: quick report includes title format, PR type, branch freshness, code-quality sweep, and no blockers. Save to `docs/session_5/precheck_quick.md`.

- [ ] **Step 3: Fix quick blockers with TDD if any**

If a blocker is a product/test BUG, first write or identify the narrow failing test and run it red. Example command for a target-selection bug:

```bash
cd <external-vllm-omni-checkout>
rtk .venv-mig-s2/bin/python -m pytest -q tests/model_executor/quantization/test_nvfp4_blockwise_config.py::test_target_prefixes_included
```

Expected: FAIL before fix, PASS after fix. Commit with `git commit -s`.

- [ ] **Step 4: Run full precheck manually from the full checklist**

Run the quick checks again plus:

```bash
cd <external-vllm-omni-checkout>
BASE="$(git merge-base HEAD upstream/main)"
rtk git diff --stat "$BASE"...HEAD
rtk git diff --name-only "$BASE"...HEAD
rtk python -m compileall -q vllm_omni
rtk rg -n "cosmos3|Cosmos3|COSMOS3|/(data|workspace)/|HF_TOKEN|wfen|private" $(git diff --name-only "$BASE"...HEAD) || true
rtk python - <<'PY'
import ast
import pathlib
import subprocess

base = subprocess.check_output(["git", "merge-base", "HEAD", "upstream/main"], text=True).strip()
files = subprocess.check_output(["git", "diff", "--name-only", f"{base}...HEAD", "--", "*.py"], text=True).splitlines()
for path in files:
    tree = ast.parse(pathlib.Path(path).read_text(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            pass
print(f"AST parsed {len(files)} changed python files")
PY
```

Expected: no blockers; AST parse succeeds. Save result to `docs/session_5/precheck_full.md`.

- [ ] **Step 5: Run targeted tests**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk .venv-mig-s2/bin/python -m pytest -q \
  tests/diffusion/quantization/test_fp8_blockwise_w8a16.py \
  tests/diffusion/model_loader/test_modelopt_native.py \
  tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py \
  tests/diffusion/model_loader/test_modelopt_native_nvfp4.py \
  tests/model_executor/quantization/test_nvfp4_blockwise_config.py \
  tests/model_executor/quantization/test_modelopt_nvfp4_nan_clamp.py
```

Expected: pass. If a failure repeats twice, invoke the Failure Arbiter before a third fix attempt.

- [ ] **Step 6: Run local pre-commit**

Prefer changed files first:

```bash
cd <external-vllm-omni-checkout>
BASE="$(git merge-base HEAD upstream/main)"
rtk .venv-mig-s2/bin/python -m pre_commit run --files $(git diff --name-only "$BASE"...HEAD)
```

If `pre_commit` is unavailable in the venv, classify as ENVIRONMENT and try:

```bash
cd <external-vllm-omni-checkout>
rtk python -m pre_commit run --files $(git diff --name-only "$(git merge-base HEAD upstream/main)"...HEAD)
```

Expected: pass or product-modifying hooks are applied, reviewed, tested, and committed with `git commit -s`.

- [ ] **Step 7: Run local wheel build equivalent**

Run:

```bash
cd <external-vllm-omni-checkout>
UV_SYSTEM_PYTHON=1 rtk bash scripts/build_wheel.sh --python python
```

If environment lacks required build resources, classify as ENVIRONMENT and record the exact failure. If it reveals product build breakage, fix with a failing test or build reproduction first.

## Task 3: DCO, PR Metadata, And Owner Gate

**Files:**

- Create/modify: `docs/session_5/pr_record.md`
- Create/modify: `docs/session_5/checks.md`
- External push: `origin/gpu-s4-quant-loader-isolation`

- [ ] **Step 1: Verify DCO on all branch commits**

Run:

```bash
cd <external-vllm-omni-checkout>
BASE="$(git merge-base HEAD upstream/main)"
rtk git log --format='%H%n%B%x00' "$BASE"..HEAD
rtk proxy bash -lc 'BASE="$(git merge-base HEAD upstream/main)"; missing=0; while read -r sha; do git log -1 --format=%B "$sha" | grep -q "^Signed-off-by:" || { echo "missing signoff: $sha"; missing=1; }; done < <(git rev-list "$BASE"..HEAD); exit "$missing"'
```

Expected: every commit has `Signed-off-by:`.

- [ ] **Step 2: Draft PR body**

Use this template in `docs/session_5/pr_record.md` before submission:

```markdown
## Summary
- Add ModelOpt-native FP8 blockwise sidecar loading for `fp8_blockwise_mixed` checkpoints.
- Add NVFP4 blockwise sidecar loading and W4A16 target-inclusion config for `nvfp4_blockwise_mixed_v1` checkpoints.
- Keep the FP8 resident W8A16 path opt-in while load-time dequant remains the default.

## Tests
- `<targeted pytest summary>`
- `<compileall summary>`
- `<pre-commit summary>`
- `<wheel build summary or ENVIRONMENT note>`

## Notes
- DCO signed on all commits.
- No Cosmos3-specific code or model weights included.
- No GPU benchmark claim in this PR.
```

- [ ] **Step 3: Push final branch**

Run:

```bash
cd <external-vllm-omni-checkout>
rtk git push --force-with-lease origin gpu-s4-quant-loader-isolation
rtk git ls-remote origin refs/heads/gpu-s4-quant-loader-isolation
```

Expected: remote branch points to local HEAD. Use force-with-lease only if the rebase rewrote prior branch history.

- [ ] **Step 4: Stop for owner go-ahead**

Ask the owner:

```text
All pre-submission checks that can run before PR creation have been recorded. Do you approve opening the PR against vllm-project/vllm-omni main now?
```

Expected: explicit approval immediately before `gh pr create`. If not approved, do not open the PR.

- [ ] **Step 5: Open PR if approved**

Run only after owner approval:

```bash
cd <external-vllm-omni-checkout>
rtk gh pr create \
  --repo vllm-project/vllm-omni \
  --base main \
  --head fengwang:gpu-s4-quant-loader-isolation \
  --title "[Core][Quantization] Add ModelOpt-native FP8/NVFP4 blockwise loaders" \
  --body-file <prepared-pr-body-file>
```

Expected: command prints the PR URL. Record it in `docs/session_5/pr_record.md`.

- [ ] **Step 6: Run PR checks**

Run:

```bash
rtk gh pr checks <PR-URL-or-number> --repo vllm-project/vllm-omni --watch
```

Expected: all required checks pass, or failures/pending state are classified before any fix.

## Task 4: Review, Verification, And Closeout

**Files:**

- Create/modify: `docs/session_5/sharded_review.md`
- Create/modify: `docs/session_5/adversarial_verification.md`
- Modify: `docs/evidence_map.md`
- Modify: `docs/risk_register.md`
- Modify: `docs/eval_seed_cases.md`
- Modify: `docs/handoff.md`

- [ ] **Step 1: Run sharded review**

Review axes:

- correctness
- security/safety
- tests
- architecture/maintainability
- performance

Inputs:

- `docs/session_5_contract.yaml`
- `docs/project_contract.md`
- external branch diff against `upstream/main`
- `docs/session_5/checks.md`
- precheck reports
- PR record, if opened

Save deduplicated actionable findings to `docs/session_5/sharded_review.md`.

- [ ] **Step 2: Fix High/Critical findings only**

For each High/Critical finding, classify if it involves a failing check, add or identify a failing test, implement the smallest fix, re-run targeted checks, and commit with `git commit -s` if external code changes.

- [ ] **Step 3: Run adversarial verification**

Verifier sees only:

- session contract
- project contract
- external diff
- check evidence
- precheck reports
- PR record

Save verdict to `docs/session_5/adversarial_verification.md`.

- [ ] **Step 4: Update evidence and handoff**

Update:

- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/eval_seed_cases.md`
- `docs/handoff.md`

Use the handoff template and include checks run, checks not run, PR URL or non-submission reason, and remaining risks.

- [ ] **Step 5: Final checks**

Run:

```bash
cd <webui-repo>
rtk make scan
rtk git status --short
cd <external-vllm-omni-checkout>
rtk git status --short --branch
rtk git log --show-signature -n 5
```

Expected: main repo docs do not leak private paths; external fork is clean or any remaining state is documented; DCO trailers present.
