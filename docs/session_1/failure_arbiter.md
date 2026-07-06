# Session 1 Failure Arbiter

## FA-001: Direct `rtk test -f` Check Failed

- Category: TEST_BUG
- Failing command: `rtk test -f docs/session_1/brainstorming.md`
- Output evidence: command exited `2` and printed shell usage text instead of evaluating file existence.
- Relevant contract clause: Session 1 requires deterministic checks and failure classification before fixing.
- Why BUG does not fit: no product or documentation implementation existed yet to violate a requirement.
- Why SPEC_GAP does not fit: the intended behavior, checking whether a file exists, is clear.
- Why AMBIGUITY does not fit: there is only one intended interpretation of the check.
- Why ENVIRONMENT does not fit: the shell and `rtk` were available; the issue was the malformed check command.
- Allowed next action: replace the check with `rtk sh -lc 'test -f docs/session_1/brainstorming.md'`.
- Forbidden next action: treat the failure as a missing product file until the check command is corrected.

## FA-002: Placeholder Scan Matched Its Own Documentation

- Category: TEST_BUG
- Failing command: broad placeholder-marker scan over `docs/session_1`.
- Output evidence: command matched the literal pattern inside `docs/session_1/plan.md` and `docs/session_1/execution_contract.md`.
- Relevant contract clause: deterministic checks must provide evidence about the session artifacts.
- Why BUG does not fit: the matches were check examples, not unfinished placeholders in product or policy content.
- Why SPEC_GAP does not fit: the requirement to avoid unfinished placeholder markers is clear.
- Why AMBIGUITY does not fit: the false positive was caused by regex self-reference, not multiple valid interpretations.
- Why ENVIRONMENT does not fit: the command ran successfully in the current shell.
- Allowed next action: rewrite the scan examples with non-self-matching regex spelling.
- Forbidden next action: delete the placeholder scan requirement or ignore real placeholder matches.

## FA-003: Path Fragment Scan Searched File Contents

- Category: TEST_BUG
- Failing command: `rtk rg -n "(checkpoints|weights|artifacts|outputs|samples/generated)" . --glob "!docs/session_1/**"`
- Output evidence: command matched ordinary documentation sentences about weights and artifacts across project docs.
- Relevant contract clause: scrub scans must detect files that should not enter the public repo.
- Why BUG does not fit: no forbidden file path or artifact was found.
- Why SPEC_GAP does not fit: the exclusion requirement is clear; the scan should inspect file paths for excluded path fragments.
- Why AMBIGUITY does not fit: the false positives came from content search rather than multiple valid interpretations.
- Why ENVIRONMENT does not fit: `rg` worked correctly.
- Allowed next action: replace path and extension scans with `rg --files | rg ...` commands.
- Forbidden next action: remove weight, artifact, cache, archive, or legacy-submodule scan coverage.
