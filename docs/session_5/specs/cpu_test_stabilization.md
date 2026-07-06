# Specification - CPU Test Stabilization

Session: MIG-S5
Capability: CPU Test Stabilization

## ADDED Requirements

### Requirement: The Python lint check passes over api and tests

`ruff check api tests` MUST exit zero on the stabilized tree. Where a lint rule
conflicts with a deliberate, necessary pattern, the suppression MUST be local and
documented rather than a global rule relaxation.

#### Scenario: Lint is clean after stabilization

WHEN `uv run ruff check api tests` runs on the session tree
THEN it SHALL report no errors and exit zero.

#### Scenario: The intentional stub-before-import keeps a documented local ignore

WHEN `tests/api/test_oracle_adapter_audio.py` injects `sys.modules` stubs before
importing the adapter under test
THEN the import-order lint (`E402`) SHALL be suppressed by an inline `# noqa: E402`
carrying a one-line reason
AND no project-wide `E402` ignore SHALL be introduced.

### Requirement: Test collection is torch-free

Collecting the CPU suite MUST NOT require `torch`, `diffusers`, `transformers`, or
`nvidia-modelopt`. Any test that needs a heavy dependency MUST defer or guard the
import so collection succeeds without it.

#### Scenario: Collection succeeds without the oracle extra

WHEN `uv run pytest -m "not gpu" --collect-only` runs in an environment without the
`oracle` extra installed
THEN collection SHALL succeed with no import error.

### Requirement: A torch-free CPU test dependency group makes encoder tests execute

The project MUST define a `test-cpu` dependency group containing only torch-free
packages (`numpy`, `pillow`, `imageio`, `imageio-ffmpeg`) so the image/video
artifact-encoder tests execute in CI instead of being skipped for a missing
dependency. `uv.lock` MUST be regenerated to include the group.

#### Scenario: Encoder tests run under the test-cpu group

WHEN the suite runs with the `test-cpu` group installed
THEN the artifact-encoder tests in `tests/api/test_artifact_encoders.py` and
`tests/checkpoint_prep/test_writer_format.py` SHALL execute rather than skip for a
missing `numpy`.

#### Scenario: The group stays torch-free

WHEN the `test-cpu` group is installed via `uv sync --frozen --group test-cpu`
THEN `torch` SHALL NOT be present in the environment.
