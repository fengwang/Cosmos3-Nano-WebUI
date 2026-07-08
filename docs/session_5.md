# Session 5 - precheck-pr Gate and Upstream PR Submission

Contract: `docs/session_5_contract.yaml`
Risk: high
Routing: branch_and_compare

## Objective

Run the fork's `precheck-pr` skill, satisfy upstream CI/pre-commit/DCO
requirements, add unit tests for the quant methods, and — only after an
explicit owner go-ahead recorded immediately before submission — open the
pull request against `vllm-project/vllm-omni` `main`.

## Why This Session Exists

This is the irreversible, outward-facing half of the upstream contribution.
Everything through `GPU-S4` is local and reversible; opening a public pull
request attributed to the owner on a major upstream project is not something
to walk back casually. This session exists specifically to hold that action
behind its own gate, separate from the investigative work in `GPU-S4`.

## In Scope

1. Run the `fengwang/vllm-omni` fork's `precheck-pr` skill (quick, then
   full) against the `GPU-S4` feature branch.
2. Add unit tests for the quant methods.
3. Confirm the branch passes
   `.github/workflows/{pre-commit,build_wheel}.yml` and
   `.pre-commit-config.yaml`.
4. DCO sign-off (`git commit -s`) on every commit in the PR.
5. Confirm no regression in existing (non-quant / other-model) upstream
   paths.
6. Determine the correct PR-title prefix (for example `[Kernel]` for quant
   linear methods) per upstream contribution norms.
7. Record an explicit owner go-ahead immediately before opening the PR.
8. Open the PR against `vllm-project/vllm-omni` `main`.

## Out of Scope

- Further isolation or rebase work (`GPU-S4`) unless `precheck-pr` surfaces a
  scope violation, in which case this session stops and returns to `GPU-S4`
  rather than patching around it.
- Responding to maintainer review after the PR is open — tracked as a
  post-Phase-2 follow-up, not part of this session's done condition.
- Any change to this repository.

## Deliverables

- `precheck-pr` output (quick and full) for the submitted branch.
- Added unit tests for the quant methods.
- A DCO-signed, CI-green branch.
- A recorded owner go-ahead, timestamped immediately before submission.
- The opened PR's URL.

## Deterministic Checks

```bash
<fork checkout>/.claude/skills/precheck-pr   # quick, then full
git log --show-signature -n <N>              # DCO sign-off presence
gh pr checks <PR>                            # after opening
```

`precheck-pr` runs against the `fengwang/vllm-omni` fork checkout, not this
repository, and never posts on its own per its own contract.

## Exit Criteria

- `GATE-GPU-S5-PR` passes.
- `precheck-pr` is clean, CI is green, DCO sign-off is present, and no
  regression is found in non-quant paths.
- The PR is not opened without a recorded owner go-ahead immediately
  preceding submission.
- Either the PR is open, or the session records why it did not proceed (for
  example a scope conflict routed back to `GPU-S4`).

## Handoff

Hand off the PR URL, its review status, and any maintainer-requested changes
to a post-Phase-2 follow-up. There is no further Phase-2 session downstream
of `GPU-S5`.
