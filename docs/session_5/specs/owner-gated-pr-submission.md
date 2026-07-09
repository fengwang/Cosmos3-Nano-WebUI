# Specification: Owner-Gated PR Submission

## ADDED Requirements

### Requirement: Every PR Commit Is DCO Signed

Every commit included in the upstream PR MUST include a `Signed-off-by` trailer matching the configured contributor identity.

#### Scenario: DCO Sweep Covers All PR Commits

WHEN the branch commits are listed from upstream base to HEAD
THEN each commit SHALL contain a `Signed-off-by:` trailer before the branch is pushed for PR submission.

### Requirement: PR Metadata Follows Upstream Norms

The PR title MUST use a valid upstream prefix, and the PR body MUST accurately describe the diff, tests run, DCO status, and known limitations without claiming unsupported GPU or benchmark evidence.

#### Scenario: Prefix Is Valid

WHEN the PR title is checked against upstream contribution guidance
THEN the title SHALL start with a valid prefix such as `[Kernel]`, `[Core]`, or another prefix justified by current docs.

#### Scenario: Body Matches Diff

WHEN the PR body file/change summary is compared with the branch diff
THEN it SHALL not claim files, benchmarks, models, or runtime behavior outside the actual contribution.

### Requirement: PR Is Opened Only After Immediate Owner Go-Ahead

The session MUST ask for and record explicit owner go-ahead immediately before running `gh pr create`. Earlier brainstorming approval, plan approval, or passing checks MUST NOT count as PR-opening approval.

#### Scenario: Owner Gate Precedes PR Create

WHEN `gh pr create` is run
THEN the immediately preceding session record SHALL contain the owner's explicit approval to open the PR.

#### Scenario: No Go-Ahead Means No PR

WHEN the owner does not approve PR opening
THEN the session SHALL leave the PR unopened and record a ready-or-blocked handoff instead.

### Requirement: GitHub Checks Are Recorded After PR Creation

If the PR is opened, the session MUST run `gh pr checks <PR>` and record the result. A failing check MUST be classified before any fix.

#### Scenario: Checks Green Satisfies Gate

WHEN GitHub reports all required checks passing
THEN the session SHALL record the PR URL, check summary, and `GATE-GPU-S5-PR` pass evidence.

#### Scenario: Checks Fail Or Pending

WHEN GitHub reports a failing, missing, or still-pending required check
THEN the session SHALL record the status and classify the failure or pending state before deciding whether further action is in scope.
