# Specification: Upstream State Finding

## ADDED Requirements

### Requirement: Upstream State Is Checked Before Contribution Code

The session MUST inspect current `vllm-project/vllm-omni` `main` for existing FP8/NVFP4 blockwise quant support or ModelOpt-native detection before creating any isolation commit.

#### Scenario: Missing Support Is Recorded Before Isolation

WHEN upstream `main` lacks equivalent FP8/NVFP4 blockwise or ModelOpt-native detection support
THEN the session SHALL record the upstream ref, commands, matches, and conclusion before creating the isolated branch commit.

#### Scenario: Existing Support Stops Code Work

WHEN upstream `main` already contains equivalent support
THEN the session SHALL document the no-PR-needed finding and SHALL NOT create contribution code.

### Requirement: Evidence Uses Deterministic Commands

The upstream-state finding MUST cite deterministic commands and exact refs.

#### Scenario: Finding Can Be Replayed

WHEN a reviewer reads the upstream-state finding
THEN it SHALL include the upstream commit SHA, local command list, and enough command output summary to replay the conclusion.

