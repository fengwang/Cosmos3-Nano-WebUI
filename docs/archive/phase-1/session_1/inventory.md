# Session 1 Public Repository Inventory

Date: 2026-07-06
Session: MIG-S1

## Summary

The working repo is a public migration seed on branch `session-1`. At Session 1 startup it contained the blueprint contract pack, an empty `README.md`, and `misc/logo.png`. During Task 1, the Session 1 planning pack was added under `docs/session_1/**`.

No runtime source, WebUI source, schemas, tools, deploy files, workflows, model weights, or generated media are present in the current public tree.

## Local Repo State

### Startup State Before Edits

- Branch: `session-1`.
- Startup HEAD: `76e60a26e73dde0a0e39287d55fe2ce47e2e0ba4`.
- Startup `git status --short`: clean.
- `docs/handoff.md`: absent.
- `README.md`: present and empty.
- `misc/logo.png`: present.

### Current State At Inventory Write

- Branch: `session-1`.
- Current HEAD: `96a10e3` after Task 1 checkpoint commit.
- Current `rtk git status --short --branch` output:

```text
## session-1
```

Recent commits:

```text
96a10e3 (HEAD -> session-1) docs: add session 1 planning pack
76e60a2 (blueprint) ignore session related documents
bc8ecc7 blueprint created
d1b6e84 (main) prepare for migration
c3983f7 (origin/main) initialize repo
```

## Local Remote Configuration

`rtk git remote -v`:

```text
origin  git@github.com:fengwang/Cosmos3-Nano-WebUI.git (fetch)
origin  git@github.com:fengwang/Cosmos3-Nano-WebUI.git (push)
```

## Public Target Remotes

### WebUI/API Repo

- Remote: `git@github.com:fengwang/Cosmos3-Nano-WebUI.git`
- Probe:

```bash
rtk sh -lc 'GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" git ls-remote git@github.com:fengwang/Cosmos3-Nano-WebUI.git HEAD "refs/heads/*"'
```

- Observed result:

```text
c3983f7fc68c3718e870dfcbab0f0141a1566764  HEAD
c3983f7fc68c3718e870dfcbab0f0141a1566764  refs/heads/main
```

### vLLM-Omni Fork

- Remote: `git@github.com:fengwang/vllm-omni.git`
- Probe:

```bash
rtk sh -lc 'GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" git ls-remote git@github.com:fengwang/vllm-omni.git HEAD "refs/heads/*"'
```

- Observed result:

```text
d4a869fe5e2edd49af48026051948c8d1018d727  HEAD
d4a869fe5e2edd49af48026051948c8d1018d727  refs/heads/main
```

### Hugging Face Checkpoint Targets

These are target public repos from the PRD. Session 1 records them only; file layout, license metadata, and runtime compatibility remain `MIG-S4` scope.

- FP8: `wfen/Cosmos3-Nano-FP8-Blockwise`
- NVFP4: `wfen/Cosmos3-Nano-NVFP4-Blockwise`

## Current File Tree

`rtk rg --files` currently reports:

```text
docs/session_5.md
docs/session_7_contract.yaml
docs/session_6_contract.yaml
docs/session_5_contract.yaml
docs/session_8_contract.yaml
docs/session_4_contract.yaml
docs/session_4.md
docs/eval_seed_cases.md
docs/session_7.md
docs/project_contract.md
docs/session_2_contract.yaml
docs/risk_register.md
docs/session_3.md
docs/session_6.md
docs/session_1.md
docs/prd.md
docs/session_1_contract.yaml
docs/evidence_map.md
README.md
docs/session_3_contract.yaml
docs/session_8.md
docs/session_2.md
docs/session_1/proposal.md
docs/session_1/plan.md
docs/session_1/execution_contract.md
docs/session_1/failure_arbiter.md
docs/session_1/tasks.md
docs/session_1/design.md
docs/session_1/brainstorming.md
docs/session_1/specs/target_remote_baseline.md
docs/session_1/specs/exclusion_manifest.md
docs/session_1/specs/evidence_risk_handoff.md
docs/session_1/specs/private_reference_scrub_checklist.md
docs/session_1/specs/curated_import_manifest.md
docs/session_1/specs/public_repository_inventory.md
misc/logo.png
```

## Seed File State

`rtk wc -c README.md misc/logo.png` showed:

```text
0 README.md
123413 misc/logo.png
```

`README.md` is intentionally not changed in Session 1. README work belongs to `MIG-S7`.

## Baseline Check Table

| Check | Result | Classification |
|---|---|---|
| `rtk git status --short --branch` | Passed. Current branch is `session-1`. | PASS |
| `rtk git remote -v` | Passed. Only `origin` is configured. | PASS |
| `rtk rg --files` | Passed. File list is recorded above. | PASS |
| WebUI `git ls-remote` probe | Passed. `main` points at `c3983f7fc68c3718e870dfcbab0f0141a1566764`. | PASS |
| vLLM-Omni `git ls-remote` probe | Passed. `main` points at `d4a869fe5e2edd49af48026051948c8d1018d727`. | PASS |
| `rtk sh -lc 'test -n "$PRIVATE_REF_PATTERN"'` | Failed because the variable is unset. | ENVIRONMENT |
| Direct `rtk test -f ...` planning check | Failed because the command form was malformed. | TEST_BUG |
| Initial placeholder scan | Failed because the scan matched its own documented pattern. | TEST_BUG |

Failure classifications are recorded in `docs/session_1/failure_arbiter.md`.

## Baseline Scope Conclusions

- `MIG-S1` is operating from a small public seed repo plus blueprint docs.
- The local branch has Session 1 planning commits not present on `origin/main`.
- Future public-source import must happen in `MIG-S3`, not in this session.
- vLLM-Omni patch work must happen in `MIG-S2`, not in this session.
- Checkpoint metadata and compatibility validation must happen in `MIG-S4`, not in this session.
- The exact contract scrub command needs a defined `$PRIVATE_REF_PATTERN` or the fallback scan from `docs/session_1/scrub_checklist.md`.
