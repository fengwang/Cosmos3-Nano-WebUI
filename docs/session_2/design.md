# Session 2 Design - vLLM-Omni Patch Rebase And Public Pin

Date: 2026-07-06
Session: MIG-S2
Risk: high

## Context

The public WebUI repo is a seed migration repo and does not contain vLLM-Omni
source. Session 2 therefore operates on the external public fork checkout at
`/workspace/github.repo/vllm-omni`, while recording evidence in this repo. The
authorized Cosmos3 patch line lives in a private/local historical checkout and
must be replayed into the public fork.

The public fork `main` currently points to
`d4a869fe5e2edd49af48026051948c8d1018d727`. The authorized patch source is an
owner-provided local eight-commit range; private source path, branch, and source
hashes are not recorded in public docs.

## Goals

- Rebase or cherry-pick the selected Cosmos3 patch series onto current public
  fork `main`.
- Preserve the eight original commits for reviewability and conflict traceability.
- Run deterministic compile and targeted tests where practical.
- Publish a public branch and immutable tag for later WebUI Docker/build config.
- Record the install target and caveats for `MIG-S3`, `MIG-S4`, and `MIG-S6`.

## Non-Goals

- Do not import WebUI/API source.
- Do not verify Hugging Face checkpoint artifacts.
- Do not publish Docker images.
- Do not create an upstream PR to the main vLLM-Omni project.
- Do not broaden source changes outside Cosmos3, checkpoint adapter,
  quantization, or matching tests.

## Decisions

### Preserve Patch Commits

Use ordered cherry-pick/rebase of the 8 source commits rather than a squash.

Rationale: conflict resolution notes and review can map directly to original
patch intent. This is safer for a high-risk dependency session.

Alternative rejected: one squashed commit. It is cleaner but hides which original
commit introduced each behavior.

### Publish Branch And Tag

Push branch `mig-s2-cosmos3-quant-pin` and tag `cosmos3-nano-webui-mig-s2`.

Rationale: the branch is convenient for inspection; the tag and commit hash are
stable install targets. `MIG-S6` must not depend on a mutable branch name alone.

### Isolated Test Environment

Use `.venv-mig-s2` under the fork checkout.

Rationale: baseline pytest failed because the global environment lacks `aenum`.
The dependency is declared by the fork, so this is an environment setup issue,
not a source bug.

### Test Path Resolution

Run the contract-listed targeted tests where they exist. If a contract path is
stale, prefer the actual test path from the rebased patch only after recording a
failure classification.

Rationale: `docs/session_2.md` allows exact paths to change with the fork, but
the YAML check list names concrete files. The execution contract must keep this
choice auditable.

## ACD Shape

Actions:

- Create branch.
- Cherry-pick/rebase commits.
- Resolve conflicts.
- Install test dependencies.
- Run compile/test commands.
- Push branch/tag.

Calculations:

- Compute patch commit list.
- Compare expected vs actual changed-file surfaces.
- Map stale test path to actual test path.
- Build deterministic install command from final tag/commit.

Data:

- Source base and target base commits.
- Patch commit list.
- Conflict notes.
- Test outputs and classifications.
- Public branch, tag, and final commit.

## Risks And Mitigations

- Rebase conflict in upstream-changed Cosmos3 code -> stop at conflict, resolve
  only contract-approved surfaces, and record conflict notes.
- Targeted tests require heavyweight dependencies or CUDA -> classify as
  ENVIRONMENT and keep compile/static tests as deterministic evidence.
- Tests pass without covering touched behavior -> review must inspect spec-to-test
  mapping and can require additional lightweight tests.
- Public tag points to a local-only commit -> verify with `git ls-remote` after
  push.
- Private source details leak into public docs -> cite only local command
  evidence and public fork state; do not publish private host URLs.

## Migration Plan

1. Create Session 2 planning artifacts and execution contract.
2. Create a fork working branch from public `origin/main`.
3. Create or refresh `.venv-mig-s2`.
4. Identify the first spec-derived failing/missing test.
5. Replay the patch commits one task at a time, resolving conflicts only inside
   scope.
6. Run targeted checks after each task.
7. Run full Session 2 checks.
8. Run sharded review and fix only High/Critical findings.
9. Run adversarial verification.
10. Push the public branch and tag.
11. Update evidence, risk, handoff, and eval seeds as needed.

Rollback:

- If source work becomes unsafe, reset only the external fork working branch, not
  WebUI docs.
- If push succeeds but verification fails, delete or supersede the tag only after
  recording the failure and owner disposition.

## Open Questions

No owner decision remains open. Environment and test failures may still require
classification during execution.
