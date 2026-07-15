# Session 5 Failure Arbiter

## FA-1: Local pre-commit module missing

- Failing command: `.venv-mig-s2/bin/python -m pre_commit run --files $(git diff --name-only "$BASE"...HEAD)`
- Output: `No module named pre_commit`
- Category: ENVIRONMENT
- Evidence: `which pre-commit` found no executable; `/usr/bin/python -m pre_commit --version` also failed; `.venv-mig-s2/bin/python -m pip show pre-commit` reported package not found.
- Why other categories do not fit:
  - BUG: no product code ran; the failure is before hooks execute.
  - SPEC_GAP: the session contract requires local pre-commit where practical, and upstream docs say contributors install `pre-commit`.
  - AMBIGUITY: behavior is unambiguous: the tool is absent.
  - TEST_BUG: no test assertion is involved.
- Allowed next action: install `pre-commit` as a local contributor tool in the external fork venv or use an equivalent isolated runner, then rerun the hook.
- Forbidden next action: rewrite product code to bypass a missing local developer tool.

## FA-2: pre-commit formatting and typos failures

- Failing command: `.venv-mig-s2/bin/python -m pre_commit run --files $(git diff --name-only "$BASE"...HEAD)`
- Output: `ruff-check` and `ruff-format` modified 11 files; `typos` rejected `mis-declared` and `mis-routed` in docstrings/messages.
- Category: BUG
- Evidence: pre-commit is a required local CI gate in `docs/session_5/specs/precheck-and-local-ci.md`. The branch did not satisfy the repository's formatting and spelling hooks.
- Why other categories do not fit:
  - SPEC_GAP: the formatting/spelling policy is explicit in `.pre-commit-config.yaml`.
  - AMBIGUITY: the hook output names exact files and replacements.
  - ENVIRONMENT: after installing pre-commit, hooks ran successfully enough to report product-file findings.
  - TEST_BUG: hook failures are not contradictory tests; they enforce repo style.
- Allowed next action: keep the hook's formatting changes, replace the rejected words with clear alternatives, rerun pre-commit, and then rerun targeted tests.
- Forbidden next action: bypass `typos` or commit formatter changes without re-running tests.

## FA-3: Local wheel build targeted externally managed system Python

- Failing command: `UV_SYSTEM_PYTHON=1 bash scripts/build_wheel.sh --python python`
- Output: `uv pip` selected `/usr` Python 3.14.6 and failed because the interpreter is externally managed.
- Category: ENVIRONMENT
- Evidence: the build script failed while installing the `build` module into the local system interpreter, before invoking package build logic. The external fork venv exists and reports Python 3.12.12.
- Why other categories do not fit:
  - BUG: no project build code had run yet.
  - SPEC_GAP: the local-equivalent requirement permits practical local execution; CI's `UV_SYSTEM_PYTHON=1` environment differs from this workstation.
  - AMBIGUITY: the error explicitly identifies externally managed system Python.
  - TEST_BUG: no test assertion is involved.
- Allowed next action: rerun `scripts/build_wheel.sh --python .venv-mig-s2/bin/python` so the build module installs into the fork venv.
- Forbidden next action: modify production code or pyproject metadata to work around a local system package-management policy.

## FA-4: PR title prefix guidance drift

- Failing check or review finding: sharded review F1 found the draft `[Kernel]` title under-supported by live upstream quantization PR title patterns.
- Category: AMBIGUITY
- Evidence: local precheck skill and `docs/contributing/README.md` list `[Core]` and `[Kernel]` but not `[Quantization]`; live upstream PR search for `quant` shows active/recent `[Quant]`, `[Quantization]`, and `[Diffusion][Quantization]` titles, while `[Kernel] quant` returned no matches.
- Why other categories do not fit:
  - BUG: no code or local check failed.
  - SPEC_GAP: both sources provide guidance, but they point in different directions.
  - ENVIRONMENT: not caused by local setup.
  - TEST_BUG: no test assertion is involved.
- Allowed next action: choose an explicit title that satisfies the static first-prefix list and the live quantization norm: `[Core][Quantization] Add ModelOpt-native FP8/NVFP4 blockwise loaders`.
- Forbidden next action: leave the title as `[Kernel]` without recording why it matches current upstream norms.

## FA-5: Final adversarial verification record not closed

- Failing check or review finding: final adversarial verifier reported that `docs/session_5/adversarial_verification.md` still described the pre-owner-gate state and explicitly said the final `GATE-GPU-S5-PR` claim was not yet supported.
- Category: BUG
- Evidence: the PR existed and GitHub checks were green, but the verifier artifact had not been updated with a post-PR round; `docs/session_5/tasks.md` still left task 4.7 unchecked.
- Why other categories do not fit:
  - SPEC_GAP: the session contract explicitly requires adversarial verification after deterministic checks.
  - AMBIGUITY: the verifier's objection names exact stale lines and the missing final round.
  - ENVIRONMENT: GitHub and local checks were available.
  - TEST_BUG: the verifier correctly identified a documentation/evidence gap.
- Allowed next action: add a final adversarial verification round with live PR/check/DCO evidence, then mark the done-condition task complete after rechecking.
- Forbidden next action: claim `GATE-GPU-S5-PR` passes while the verifier artifact still says final verification is deferred.

## FA-6: Precheck reports still had pending PR-body rows

- Failing check or review finding: final adversarial verifier found `PENDING` PR-body rows in the quick and full precheck reports after the PR body had already been finalized and submitted.
- Category: BUG
- Evidence: `docs/session_5/precheck_quick.md` and `docs/session_5/precheck_full.md` still said body matching/integrity was pending, while `docs/session_5/pr_body.md` and live PR #5000 now match exactly.
- Why other categories do not fit:
  - SPEC_GAP: the precheck clean requirement includes PR body integrity.
  - AMBIGUITY: the final PR body exists and can be compared directly.
  - ENVIRONMENT: `gh pr view --json body` succeeded.
  - TEST_BUG: the verifier accurately found stale evidence text.
- Allowed next action: update the precheck reports with the final body-integrity recheck evidence.
- Forbidden next action: leave `PENDING` rows while claiming quick/full precheck are clean.

## FA-7: PR creation timestamp mismatch

- Failing check or review finding: final adversarial verifier found a mismatch between the recorded local command timestamp and GitHub's actual PR creation timestamp.
- Category: BUG
- Evidence: `docs/session_5/pr_record.md` recorded `2026-07-09T19:41:21Z`; `gh pr view 5000 --json createdAt` reports `2026-07-09T19:41:13Z`.
- Why other categories do not fit:
  - SPEC_GAP: the session requires timestamped owner/PR evidence.
  - AMBIGUITY: GitHub's `createdAt` is the authoritative PR creation timestamp.
  - ENVIRONMENT: GitHub returned a stable value.
  - TEST_BUG: the verifier's check is valid.
- Allowed next action: correct the PR record to the GitHub-observed creation timestamp while keeping the local evidence timestamp in the checks log where relevant.
- Forbidden next action: use the later local `date` output as the PR's creation time.
