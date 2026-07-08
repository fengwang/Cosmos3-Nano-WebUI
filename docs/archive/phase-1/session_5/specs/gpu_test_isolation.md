# Specification - GPU Test Isolation

Session: MIG-S5
Capability: GPU Test Isolation

## ADDED Requirements

### Requirement: GPU-marked tests are skipped off-GPU by a collection hook

`tests/conftest.py` MUST implement a collection hook that skips every test carrying
the `gpu` marker unless the environment variable `COSMOS3_ENABLE_GPU_TESTS` is set
to a truthy value. This SHALL hold regardless of whether the `-m "not gpu"` filter
is supplied.

#### Scenario: gpu test is skipped when the opt-in is unset

WHEN a test marked `@pytest.mark.gpu` is collected and `COSMOS3_ENABLE_GPU_TESTS`
is unset
THEN the collection hook SHALL mark it skipped
AND the skip reason SHALL name `COSMOS3_ENABLE_GPU_TESTS`.

#### Scenario: gpu test runs only when explicitly opted in

WHEN `COSMOS3_ENABLE_GPU_TESTS=1` is set
THEN the collection hook SHALL NOT skip `gpu`-marked tests.

### Requirement: CI filters GPU tests with the marker expression

The CPU CI Python job MUST invoke pytest with `-m "not gpu"` so GPU-marked tests
are deselected even if the collection hook were absent. The two mechanisms MUST be
independent.

#### Scenario: CI deselects gpu tests

WHEN the CI Python job runs pytest
THEN the invocation SHALL include `-m "not gpu"`.

### Requirement: GPU test modules guard heavy imports

To keep the marker filter effective, any test module that is GPU-only MUST guard
heavy imports (for example with `pytest.importorskip`) so pytest can import the
module during collection without the `oracle` extra. This convention MUST be
recorded for future sessions.

#### Scenario: Convention is documented

WHEN `tests/conftest.py` and the developer command list are read
THEN they SHALL state that GPU-only modules guard heavy imports so collection never
fails on a CPU runner.

### Requirement: A manual GPU test command is documented for S8

The session MUST document the command that runs GPU tests on real hardware, handing
it to the manual GPU release gate (S8).

#### Scenario: Manual GPU command is recorded

WHEN the developer command list is read
THEN it SHALL include `COSMOS3_ENABLE_GPU_TESTS=1 pytest -m gpu` (or an equivalent)
as the manual GPU command
AND state that it is a manual gate, not part of CPU CI.
