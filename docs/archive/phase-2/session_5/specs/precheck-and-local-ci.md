# Specification: Precheck And Local CI Gate

## ADDED Requirements

### Requirement: Precheck Runs Quick And Full

The fork's `precheck-pr` skill MUST run in quick mode and full mode against the submission branch. A quick pass MUST NOT substitute for the full run.

#### Scenario: Quick Then Full Evidence Exists

WHEN the session records precheck evidence
THEN it SHALL contain separate quick and full reports with mode, PR type, title evaluation, code-quality sweep, and verdict.

#### Scenario: Full Run Is Not Skipped

WHEN the quick precheck reports no blockers
THEN the session SHALL still run full precheck before asking for PR-opening approval.

### Requirement: Local CI Equivalents Run Before Owner Gate

Before the owner go-ahead is requested, the session MUST run targeted quant tests, `compileall`, guard sweeps, DCO checks, local `pre-commit`, and local wheel build where practical.

#### Scenario: Product Failure Is Classified Before Fix

WHEN a local check fails
THEN the session SHALL classify the failure as BUG, SPEC_GAP, AMBIGUITY, ENVIRONMENT, or TEST_BUG before applying any fix.

#### Scenario: Environment Failure Does Not Trigger Product Rewrite

WHEN a local check fails because of missing local services, toolchain, network, timeout, or cache conditions
THEN the session SHALL record ENVIRONMENT and SHALL NOT rewrite product code solely to satisfy that environment.

### Requirement: Quant Unit Tests Cover Contribution Methods

The submission branch MUST retain or add unit tests for FP8/NVFP4 blockwise quant methods and checkpoint adapters, and those tests MUST not require Cosmos3 model weights, GPU hardware, private files, or this repository's runtime.

#### Scenario: Targeted Tests Pass On Submission Branch

WHEN targeted quant tests are run after the final code change
THEN they SHALL pass or the session SHALL classify and fix any in-scope failure before submission.

#### Scenario: Test Fakes Do Not Weaken Production Types

WHEN test utilities or fakes are added or changed
THEN they SHALL not force new production `Any` types or hide a real typed object behind misleading test-only behavior.
