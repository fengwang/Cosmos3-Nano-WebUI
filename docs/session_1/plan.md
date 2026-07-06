# Session 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the Session 1 public repo inventory, import/exclusion scope, scrub checklist, evidence updates, and handoff.

**Architecture:** This is a documentation and policy session. Shell commands are Actions at the edge; their outputs become Data recorded in Markdown; classification and scope decisions are Calculations documented in specs and manifests.

**Tech Stack:** Markdown, Git, `rtk`, `rg`, POSIX shell checks.

---

## File Structure

- Create: `docs/session_1/brainstorming.md`
- Create: `docs/session_1/proposal.md`
- Create: `docs/session_1/design.md`
- Create: `docs/session_1/specs/public_repository_inventory.md`
- Create: `docs/session_1/specs/target_remote_baseline.md`
- Create: `docs/session_1/specs/curated_import_manifest.md`
- Create: `docs/session_1/specs/exclusion_manifest.md`
- Create: `docs/session_1/specs/private_reference_scrub_checklist.md`
- Create: `docs/session_1/specs/evidence_risk_handoff.md`
- Create: `docs/session_1/tasks.md`
- Create: `docs/session_1/plan.md`
- Create: `docs/session_1/execution_contract.md`
- Create: `docs/session_1/failure_arbiter.md` if any command or check fails
- Create: `docs/session_1/inventory.md`
- Create: `docs/session_1/import_manifest.md`
- Create: `docs/session_1/exclusion_manifest.md`
- Create: `docs/session_1/scrub_checklist.md`
- Modify: `docs/evidence_map.md` only if baseline evidence changes or needs a Session 1 row
- Modify: `docs/risk_register.md` only if risk status changes
- Modify: `docs/eval_seed_cases.md` only if a reusable eval seed is found
- Create: `docs/handoff.md`

### Task 1: Lifecycle Planning Pack

**Files:**
- Create: `docs/session_1/brainstorming.md`
- Create: `docs/session_1/proposal.md`
- Create: `docs/session_1/design.md`
- Create: `docs/session_1/specs/*.md`
- Create: `docs/session_1/tasks.md`
- Create: `docs/session_1/plan.md`
- Create: `docs/session_1/execution_contract.md`
- Create: `docs/session_1/failure_arbiter.md`

- [x] **Step 1: Run failing check**

Run:

```bash
rtk sh -lc 'test -f docs/session_1/brainstorming.md'
```

Expected before implementation: command exits `1` because the file does not exist.

- [x] **Step 2: Create planning files**

Write the lifecycle files listed for Task 1. Each spec file must use `#### Scenario:` headings.

- [x] **Step 3: Run planning checks**

Run:

```bash
rtk sh -lc 'test -f docs/session_1/brainstorming.md && test -f docs/session_1/proposal.md && test -f docs/session_1/design.md && test -f docs/session_1/tasks.md && test -f docs/session_1/plan.md && test -f docs/session_1/execution_contract.md'
rtk sh -lc 'for f in docs/session_1/specs/*.md; do rg -n "^#### Scenario:" "$f" >/dev/null || exit 1; done'
rtk rg -n "T[B]D|T[O]DO|F[I]XME" docs/session_1
```

Expected after implementation: first two commands exit `0`; the placeholder scan exits `1` with no matches.

- [x] **Step 4: Commit checkpoint**

Run:

```bash
rtk git status --short
rtk git add docs/session_1
rtk git commit -m "docs: add session 1 planning pack"
```

Expected: commit succeeds and contains only `docs/session_1/**`.

### Task 2: Public Repository Inventory

**Files:**
- Create: `docs/session_1/inventory.md`

- [x] **Step 1: Run failing check**

Run:

```bash
rtk sh -lc 'test -f docs/session_1/inventory.md'
```

Expected before implementation: command exits `1`.

- [x] **Step 2: Run baseline commands**

Run:

```bash
rtk git status --short --branch
rtk git remote -v
rtk rg --files
rtk git log --oneline -n 8 --decorate
rtk sh -lc 'GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" git ls-remote git@github.com:fengwang/Cosmos3-Nano-WebUI.git HEAD "refs/heads/*"'
rtk sh -lc 'GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" git ls-remote git@github.com:fengwang/vllm-omni.git HEAD "refs/heads/*"'
rtk sh -lc 'test -n "$PRIVATE_REF_PATTERN"'
```

Expected: git status, remote, file list, log, and remote probes exit `0`. The `$PRIVATE_REF_PATTERN` check may exit `1`; classify as environment/setup if unset.

- [x] **Step 3: Write inventory**

Write `docs/session_1/inventory.md` with:

- local branch and commit
- dirty or clean status
- recent commits
- remotes
- public WebUI and vLLM-Omni remote HEAD/main commits
- current file tree summary
- README and logo state
- handoff state
- baseline check table
- out-of-scope validation note for Hugging Face checkpoints

- [x] **Step 4: Run inventory checks**

Run:

```bash
rtk rg -n "session-1|Cosmos3-Nano-WebUI|vllm-omni|wfen/Cosmos3-Nano-FP8-Blockwise|wfen/Cosmos3-Nano-NVFP4-Blockwise|PRIVATE_REF_PATTERN" docs/session_1/inventory.md
```

Expected: command exits `0` and finds each required baseline item.

- [x] **Step 5: Commit checkpoint**

Run:

```bash
rtk git status --short
rtk git add docs/session_1/inventory.md docs/session_1/failure_arbiter.md
rtk git commit -m "docs: record session 1 public inventory"
```

Expected: commit succeeds and stays inside `docs/session_1/**`.

### Task 3: Import And Exclusion Manifests

**Files:**
- Create: `docs/session_1/import_manifest.md`
- Create: `docs/session_1/exclusion_manifest.md`

- [x] **Step 1: Run failing check**

Run:

```bash
rtk sh -lc 'test -f docs/session_1/import_manifest.md && test -f docs/session_1/exclusion_manifest.md'
```

Expected before implementation: command exits `1`.

- [x] **Step 2: Write manifests**

Write `docs/session_1/import_manifest.md` with allowed import categories, proof requirements, and stop conditions. Write `docs/session_1/exclusion_manifest.md` with excluded file classes, path fragments, extensions, and exception rules.

- [x] **Step 3: Run manifest checks**

Run:

```bash
rtk rg -n "API source|WebUI source|schemas|tests|tools|project hygiene|proof" docs/session_1/import_manifest.md
rtk rg -n "safetensors|TensorRT-LLM|generated media|cache|archive|private evidence|legacy submodule" docs/session_1/exclusion_manifest.md
```

Expected: both commands exit `0` and show the required categories.

- [x] **Step 4: Commit checkpoint**

Run:

```bash
rtk git status --short
rtk git add docs/session_1/import_manifest.md docs/session_1/exclusion_manifest.md
rtk git commit -m "docs: define session 1 import boundaries"
```

Expected: commit succeeds and stays inside `docs/session_1/**`.

### Task 4: Scrub Checklist And Baseline Scan

**Files:**
- Create: `docs/session_1/scrub_checklist.md`
- Modify: `docs/session_1/failure_arbiter.md` if scan setup failures occur

- [x] **Step 1: Run failing check**

Run:

```bash
rtk sh -lc 'test -f docs/session_1/scrub_checklist.md'
```

Expected before implementation: command exits `1`.

- [x] **Step 2: Write scrub checklist**

Write `docs/session_1/scrub_checklist.md` with named pattern groups, exact commands, expected result handling, allowed placeholders, and failure classification rules.

- [x] **Step 3: Run baseline scans**

Run:

```bash
rtk sh -lc 'PRIVATE_REF_PATTERN="(/home/[A-Za-z0-9._-]+|/Users/[A-Za-z0-9._-]+|/mnt/[^[:space:]]+|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY|([A-Za-z0-9_]*token|secret|password|api[_-]?key)[[:space:]]*[:=])"; rg -n -i "$PRIVATE_REF_PATTERN" .'
rtk sh -lc 'rg --files | rg -n "\.(safetensors|pt|pth|ckpt|mp4|mov|avi)$"'
rtk sh -lc 'rg --files | rg -n "(^|/)(checkpoints|weights|artifacts|outputs|samples/generated)(/|$)"'
rtk sh -lc 'rg --files | rg -n "\.(zip|tar|tar\.gz|tgz|7z|rar)$"'
rtk sh -lc 'rg --files | rg -n "(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|node_modules|dist|build|\.next|coverage)(/|$)"'
rtk sh -lc 'rg --files | rg -n "(^|/)submodules/(vllm|TensorRT-LLM)(/|$)|(^|/)TensorRT-LLM(/|$)"'
```

Expected in current baseline: scans exit `1` with no matches, except intentional references to these scan patterns inside Session 1 docs must be classified as documentation examples if they appear.

- [x] **Step 4: Run checklist checks**

Run:

```bash
rtk rg -n "PRIVATE_REF_PATTERN|fallback|allowed placeholder|release-blocking|safetensors|TensorRT-LLM" docs/session_1/scrub_checklist.md
```

Expected: command exits `0`.

- [x] **Step 5: Commit checkpoint**

Run:

```bash
rtk git status --short
rtk git add docs/session_1/scrub_checklist.md docs/session_1/failure_arbiter.md
rtk git commit -m "docs: add session 1 scrub checklist"
```

Expected: commit succeeds and stays inside `docs/session_1/**`.

### Task 5: Evidence, Risk, Handoff, And Done Gate

**Files:**
- Modify: `docs/evidence_map.md` if needed
- Modify: `docs/risk_register.md` if needed
- Modify: `docs/eval_seed_cases.md` if needed
- Create: `docs/handoff.md`

- [ ] **Step 1: Run final-document failing check**

Run:

```bash
rtk sh -lc 'test -f docs/handoff.md'
```

Expected before implementation: command exits `1`.

- [ ] **Step 2: Update evidence, risk, and eval docs only as needed**

Use the observed baseline. Add narrowly scoped rows if they improve future checks. Do not rewrite unrelated rows.

- [ ] **Step 3: Write handoff**

Write `docs/handoff.md` with state snapshot, narrative context, decision log, next priority queue, warnings, and eval seed notes.

- [ ] **Step 4: Run final checks**

Run:

```bash
rtk git status --short --branch
rtk git remote -v
rtk rg --files
rtk sh -lc 'GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" git ls-remote git@github.com:fengwang/Cosmos3-Nano-WebUI.git HEAD "refs/heads/*"'
rtk sh -lc 'GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" git ls-remote git@github.com:fengwang/vllm-omni.git HEAD "refs/heads/*"'
rtk sh -lc 'PRIVATE_REF_PATTERN="(/home/[A-Za-z0-9._-]+|/Users/[A-Za-z0-9._-]+|/mnt/[^[:space:]]+|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY|([A-Za-z0-9_]*token|secret|password|api[_-]?key)[[:space:]]*[:=])"; rg -n -i "$PRIVATE_REF_PATTERN" .'
rtk sh -lc 'rg --files | rg -n "\.(safetensors|pt|pth|ckpt|mp4|mov|avi)$"'
rtk sh -lc 'rg --files | rg -n "(^|/)(checkpoints|weights|artifacts|outputs|samples/generated)(/|$)"'
rtk sh -lc 'rg --files | rg -n "\.(zip|tar|tar\.gz|tgz|7z|rar)$"'
rtk sh -lc 'rg --files | rg -n "(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|node_modules|dist|build|\.next|coverage)(/|$)"'
rtk sh -lc 'rg --files | rg -n "(^|/)submodules/(vllm|TensorRT-LLM)(/|$)|(^|/)TensorRT-LLM(/|$)"'
rtk rg -n "T[B]D|T[O]DO|F[I]XME" docs/session_1 docs/handoff.md
```

Expected: contract baseline commands run; fallback private-reference and artifact scans produce no release-blocking matches; placeholder scan produces no matches.

- [ ] **Step 5: Commit checkpoint**

Run:

```bash
rtk git status --short
rtk git add docs/session_1 docs/evidence_map.md docs/risk_register.md docs/eval_seed_cases.md docs/handoff.md
rtk git commit -m "docs: complete session 1 handoff"
```

Expected: commit succeeds. Changed files stay inside the allowed blast radius plus the approved `docs/handoff.md` amendment.

## Self-Review Notes

- Spec coverage: each proposal capability has a spec and at least one task.
- Placeholder scan target: unfinished placeholder markers.
- Risk routing: sharded review and adversarial verifier are not mandatory while Session 1 remains low risk; run them only if scope or risk rises to medium.
