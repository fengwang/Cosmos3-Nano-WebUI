# Specification - Acceptance Matrix

Session: MIG-S8
Capability: acceptance-matrix

## ADDED Requirements

### Requirement: Every PRD MUST is covered

`docs/session_8/outputs/acceptance_matrix.md` MUST contain exactly one row for every
MUST-level PRD requirement (functional FR-1..FR-12 where the keyword is MUST, and
non-functional NFR-1..NFR-6). Each row MUST name the requirement, its owning gate, a public
evidence pointer, and a verdict.

#### Scenario: All PRD MUSTs appear

WHEN the matrix is compared against `docs/prd.md` §4
THEN every MUST-level requirement SHALL appear as its own row, and no MUST SHALL be omitted.

#### Scenario: SHOULD requirements are distinguished

WHEN a SHOULD-level requirement (FR-11, FR-12) is included
THEN it SHALL be marked as SHOULD and SHALL NOT be treated as a release blocker.

### Requirement: Verdicts use the fixed domain and are evidence-backed

Each verdict MUST be one of `PASS`, `BETA-LIMITED`, or `NO-GO`. A `PASS` MUST cite a
public evidence pointer (command output, tracked file, or public remote/model page). A
`NO-GO` MUST name the specific unmet clause.

#### Scenario: No PASS without evidence

WHEN a row is marked `PASS`
THEN it SHALL cite a public evidence pointer, and no `PASS` SHALL rest on a private citation.

#### Scenario: GPU-dependent MUSTs are beta-limited

WHEN the rows for FR-9 (manual GPU validation) and NFR-6 (GPU evidence fields) are read
THEN each SHALL be `BETA-LIMITED`, cite the deferral (owner decision + `INV-8`), and point
to the exact deferred manual-gate command.

#### Scenario: The matrix does not lower a bar silently

WHEN a MUST cannot be met at beta time
THEN the row SHALL be `BETA-LIMITED` or `NO-GO` with an owner-visible disposition, and SHALL
NOT be recorded as `PASS`.
