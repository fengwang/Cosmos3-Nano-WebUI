# Session 1 Execution Contract

Session: MIG-S1
Risk: low
Routing: single_agent

## Planned File Changes

Create:

- `docs/session_1/brainstorming.md`
- `docs/session_1/proposal.md`
- `docs/session_1/design.md`
- `docs/session_1/specs/public_repository_inventory.md`
- `docs/session_1/specs/target_remote_baseline.md`
- `docs/session_1/specs/curated_import_manifest.md`
- `docs/session_1/specs/exclusion_manifest.md`
- `docs/session_1/specs/private_reference_scrub_checklist.md`
- `docs/session_1/specs/evidence_risk_handoff.md`
- `docs/session_1/tasks.md`
- `docs/session_1/plan.md`
- `docs/session_1/execution_contract.md`
- `docs/session_1/failure_arbiter.md`
- `docs/session_1/inventory.md`
- `docs/session_1/import_manifest.md`
- `docs/session_1/exclusion_manifest.md`
- `docs/session_1/scrub_checklist.md`
- `docs/handoff.md`

Modify only if needed:

- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/eval_seed_cases.md`

## Allowed Blast Radius

Allowed by session contract:

- `docs/session_1/**`
- `docs/evidence_map.md`
- `docs/risk_register.md`
- `docs/eval_seed_cases.md`

Allowed by direct user amendment:

- `docs/handoff.md`

Forbidden:

- `api/**`
- `webui/**`
- `deploy/**`
- `tools/**`
- `schemas/**`
- `.github/**`
- `README.md`
- model weight files
- generated media files

## First Test To Write Or Identify

Use this failing check before creating the planning pack:

```bash
rtk sh -lc 'test -f docs/session_1/brainstorming.md'
```

Expected before implementation: exit `1`.

## Checks After Each Task

### Task 1: Lifecycle Planning Pack

```bash
rtk sh -lc 'test -f docs/session_1/brainstorming.md && test -f docs/session_1/proposal.md && test -f docs/session_1/design.md && test -f docs/session_1/tasks.md && test -f docs/session_1/plan.md && test -f docs/session_1/execution_contract.md'
rtk sh -lc 'for f in docs/session_1/specs/*.md; do rg -n "^#### Scenario:" "$f" >/dev/null || exit 1; done'
rtk rg -n "T[B]D|T[O]DO|F[I]XME" docs/session_1
```

### Task 2: Public Repository Inventory

```bash
rtk rg -n "session-1|Cosmos3-Nano-WebUI|vllm-omni|wfen/Cosmos3-Nano-FP8-Blockwise|wfen/Cosmos3-Nano-NVFP4-Blockwise|PRIVATE_REF_PATTERN" docs/session_1/inventory.md
```

### Task 3: Import And Exclusion Manifests

```bash
rtk rg -n "API source|WebUI source|schemas|tests|tools|project hygiene|proof" docs/session_1/import_manifest.md
rtk rg -n "safetensors|TensorRT-LLM|generated media|cache|archive|private evidence|legacy submodule" docs/session_1/exclusion_manifest.md
```

### Task 4: Scrub Checklist

```bash
rtk rg -n "PRIVATE_REF_PATTERN|fallback|allowed placeholder|release-blocking|safetensors|TensorRT-LLM" docs/session_1/scrub_checklist.md
```

### Task 5: Final Gate

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

## Review Axes

If risk rises to medium or higher, run read-only sharded review over:

- correctness
- security and safety
- tests
- architecture and maintainability
- performance, only if a performance-relevant change appears

Session 1 starts low risk, so the default is a self-review plus deterministic checks.

## Adversarial Verifier Brief

If risk rises to medium or higher, provide a fresh verifier with:

- `docs/project_contract.md`
- `docs/session_1_contract.yaml`
- current `git diff` or checkpoint diff
- check output summaries
- Session 1 done claim

The verifier must try to disprove `GATE-MIG-S1-SCOPE` by checking acceptance criteria, invariants, blast radius, test strength, edge cases, security leaks, and unsupported claims.

## Concrete Done Condition

`GATE-MIG-S1-SCOPE` passes when all are true:

- Public repo baseline is recorded.
- Public WebUI, vLLM-Omni, and Hugging Face target IDs are recorded.
- Import manifest exists and is explicit enough for `MIG-S3`.
- Exclusion manifest exists and excludes weights, generated media, caches, archives, private evidence, local-only outputs, and legacy submodules by default.
- Scrub checklist exists and provides usable commands when `$PRIVATE_REF_PATTERN` is unset.
- Evidence, risk, and eval docs are updated only where justified.
- `docs/handoff.md` records next-session warnings.
- Final checks have run and failures are classified.
- All commits stay inside the allowed blast radius plus the approved handoff amendment.
