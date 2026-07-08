# Session 1 - Public Repo Inventory and Migration Scope

Contract: `docs/session_1_contract.yaml`
Risk: low
Routing: single_agent

## Objective

Lock the public migration baseline: current GitHub repo state, target remotes,
file inclusion and exclusion rules, evidence policy, private-reference scrub
patterns, and the exact public beta scope.

## Why This Session Exists

The migration starts from a small public seed repo. Before importing source or
rebasing dependencies, the project needs a public-safe boundary: what may be
copied, what must stay out, and which claims need re-verification.

## In Scope

1. Record current public repo branch, status, remotes, file tree, and docs state.
2. Record target public remotes for WebUI/API, vLLM-Omni, and Hugging Face
   checkpoints.
3. Define the curated import manifest: source, deploy files, schemas, tests,
   tools, docs, and project hygiene.
4. Define the exclusion manifest: weights, archives, caches, generated media,
   private evidence, temporary folders, local-only outputs, and legacy submodules.
5. Define scrub patterns for private hosts, private absolute paths, codenames,
   secrets, tokens, and weight paths.
6. Update `docs/evidence_map.md` and `docs/risk_register.md` only if public
   baseline evidence changes.

## Out of Scope

- No source import.
- No vLLM-Omni rebase.
- No Docker changes.
- No README rewrite.
- No GPU or checkpoint validation.

## Deliverables

- A migration inventory note under `docs/session_1/`.
- A curated import/exclusion manifest.
- A scrub checklist and command set for later sessions.
- Updated evidence or risk rows if the public baseline has drifted.

## Deterministic Checks

```bash
rtk git status --short --branch
rtk git remote -v
rtk rg --files
rtk git ls-remote git@github.com:fengwang/Cosmos3-Nano-WebUI.git HEAD 'refs/heads/*'
rtk git ls-remote git@github.com:fengwang/vllm-omni.git HEAD 'refs/heads/*'
rtk rg -n "$PRIVATE_REF_PATTERN" .
```

## Exit Criteria

- `GATE-MIG-S1-SCOPE` passes.
- Import and exclusion rules are explicit enough for `MIG-S3`.
- Private-reference scans have a baseline result.
- Later sessions know which claims need public re-verification.

## Handoff

Hand off the import manifest, exclusion manifest, scrub patterns, and any baseline
drift to `MIG-S2` and `MIG-S3`.
