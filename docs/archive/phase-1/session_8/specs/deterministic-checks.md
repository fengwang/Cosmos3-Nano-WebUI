# Specification - Deterministic Checks

Session: MIG-S8
Capability: deterministic-checks

## ADDED Requirements

### Requirement: CPU deterministic checks are re-run and logged

The session MUST re-run the CPU deterministic checks listed in the session contract and
record, for each, the exact command, the raw result, and a pass/fail verdict in
`docs/session_8/outputs/deterministic_checks.md`. The log MUST be reproducible from public
inputs (no CUDA, no model weights, no private network).

#### Scenario: Python CPU suite passes

WHEN the torch-free Python suite is run (`uv sync --frozen --group test-cpu` then
`uv run pytest -m "not gpu"`)
THEN it SHALL pass with 0 failures and the passing count SHALL be recorded, and `ruff check
api tests` SHALL report 0 issues.

#### Scenario: WebUI CPU checks pass

WHEN the WebUI checks are run (`pnpm build` → `lint` → `typecheck` → `test`)
THEN all SHALL pass and the Vitest count SHALL be recorded.

#### Scenario: Compose renders clean for both quant stacks

WHEN `docker compose -f deploy/docker-compose.fp8.yml config` and the `nvfp4` equivalent run
THEN each SHALL exit 0 with no unset-variable warning, and the result SHALL be recorded.

#### Scenario: Scans are clean

WHEN the committed private-reference scan and the weight/media file-path scan are run over
the controlled surface
THEN each SHALL report 0 findings, recorded with the surface scanned.

### Requirement: Checks that cannot run are recorded with a reason

The log MUST explicitly record any contract check that cannot run in this environment,
with the reason and the authoritative substitute or deferral.

#### Scenario: GitHub-hosted CI run is recorded as at-publish

WHEN the log covers the GitHub Actions workflow
THEN it SHALL record that the GitHub-hosted run is not executed locally (nothing pushed) and
is an at-publish confirmation, while the local equivalent commands are run and recorded.

#### Scenario: Unset scan pattern is recorded as ENVIRONMENT

WHEN `$PRIVATE_REF_PATTERN` is unset
THEN the log SHALL record this as an ENVIRONMENT condition and name the committed
`tests/test_private_ref_scan.py` (plus a documented fallback `rg`) as the authoritative
baseline.

### Requirement: Failures are classified before any fix

A failing check MUST be classified with the Failure Arbiter (BUG / SPEC_GAP / AMBIGUITY /
ENVIRONMENT / TEST_BUG) before any change is made, and product code MUST NOT be edited
without an owner-approved release fix.

#### Scenario: A failing check is classified first

WHEN a deterministic check fails
THEN a Failure-Arbiter entry SHALL be written (category + evidence + allowed/forbidden next
action) before any edit, and no runtime-source fix SHALL be applied without owner approval.
