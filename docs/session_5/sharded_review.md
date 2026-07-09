# Session 5 Sharded Review

## Inputs

- Session contract: `docs/session_5_contract.yaml`
- Execution contract: `docs/session_5/execution_contract.md`
- External diff: `<external-vllm-omni-checkout>`, branch `gpu-s4-quant-loader-isolation` vs. `upstream/main`
- Precheck reports: `docs/session_5/precheck_quick.md`, `docs/session_5/precheck_full.md`
- Checks: `docs/session_5/checks.md`
- PR metadata draft: `docs/session_5/pr_record.md`, `docs/session_5/pr_body.md`

## Summary

Result before fixes: one High metadata finding, no Critical findings.

The branch itself is narrow, DCO-signed, rebased onto current upstream, and locally checked. The only blocking issue is PR-title routing: the initial `[Kernel]` draft passes the static local checklist, but live upstream quantization PRs use quantization-oriented prefixes, and no recent quant PR evidence supports `[Kernel]`.

## Reviewer Shards

### Correctness Reviewer

- Branch freshness: PASS. Merge-base equals current upstream `main` `ca0ae7269ca3e9487645cf66088fdfc338951da9`.
- Local behavior checks: PASS. Targeted pytest passed after rebase and after formatter cleanup.
- Finding: F1, PR title prefix is not sufficiently supported by current upstream quant PR norms.

### Security/Safety Reviewer

- Owner gate: PASS so far. No PR exists yet; owner gate is pending.
- Secrets/private paths: PASS. Branch-diff forbidden residue sweep returned zero matches.
- External writes: PASS. Only fork branch was force-pushed after clean rebase; no direct upstream write occurred.
- Findings: none.

### Tests Reviewer

- Targeted tests: PASS. 128 targeted tests pass.
- Hook coverage: PASS. Pre-commit and wheel build pass after classified environment setup.
- Warning: `SimpleNamespace` fakes and test-only broad import guard remain warnings but do not weaken production behavior.
- Findings: none.

### Architecture/Maintainability Reviewer

- Scope: PASS. Diff remains 13 files in quant-loader/config/test surfaces.
- ACD boundaries: PASS. Pure parsing/remapping/target calculations remain separated from file and GitHub actions.
- Residual S4 Medium/Low items remain non-blocking: adapter/quantization helper coupling and eager imports are not worsened by `GPU-S5`.
- Finding: F1 also affects maintainability of upstream review routing.

### Performance Reviewer

- FP8 W8A16: PASS. Resident W8A16 path remains opt-in.
- Hot paths: PASS. Diff-scoped sweep found no new hot-path clone/deepcopy/event-loop blocking hits.
- Benchmark claims: PASS. PR body draft makes no GPU benchmark claim.
- Findings: none.

## Deduplicated Findings

### F1: PR Title Prefix Should Reflect Current Quantization Review Norms

- Severity: High
- Axes: correctness, architecture/maintainability
- Evidence:
  - `docs/session_5/pr_record.md` initial title: `[Kernel] Add ModelOpt-native FP8/NVFP4 blockwise quant loaders`.
  - Live upstream PR title search for `quant` returned active/recent titles such as `[Quantization] Support ModelOpt AutoQuant checkpoints`, `[Quant] Add ModelOpt mixed FP8/NVFP4 support for Wan2.2 video`, and `[Diffusion][Quantization] SVDQuant W4A4 (Nunchaku) for Z-Image-Turbo`.
  - Live search for `[Kernel] quant` returned no matching upstream PRs.
- Violated contract clause: `docs/session_5_contract.yaml` in-scope item "Determine the correct PR-title prefix ... per upstream contribution norms"; `docs/session_5/specs/owner-gated-pr-submission.md` requirement "PR Metadata Follows Upstream Norms".
- Impact: A technically valid PR could be misrouted or appear inconsistent with current quantization contribution practice.
- Smallest safe fix: revise the final title to a prefix that satisfies the static precheck category while also carrying the live quantization norm, e.g. `[Core][Quantization] Add ModelOpt-native FP8/NVFP4 blockwise loaders`, and record the local-precheck/live-norm ambiguity.
- Confidence: Medium-high. Current docs and the local precheck skill do not list `[Quantization]`, but live upstream PR evidence strongly shows quantization-oriented prefixes are used in practice.

## Final Review Decision

Fix F1 before requesting the owner gate. No code findings require a product change.
