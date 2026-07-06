# Specification - CPU CI Pipeline

Session: MIG-S5
Capability: CPU CI Pipeline

## ADDED Requirements

### Requirement: A CPU-only workflow runs on push and pull request

The repository MUST provide a GitHub Actions workflow at `.github/workflows/ci.yml`
that triggers on `push` and `pull_request`. The workflow SHALL declare
`permissions: contents: read`, SHALL set a `concurrency` group that cancels
superseded runs, and MUST NOT reference any repository secret.

#### Scenario: Workflow triggers and is least-privilege

WHEN `.github/workflows/ci.yml` is parsed
THEN it SHALL declare both `push` and `pull_request` triggers
AND it SHALL set `permissions: contents: read`
AND it SHALL contain no `secrets.` reference and no registry-login step.

#### Scenario: Redundant runs are cancelled

WHEN two runs are queued for the same ref
THEN the workflow's `concurrency` group with `cancel-in-progress: true` SHALL
cancel the superseded run.

### Requirement: The Python job uses uv-provisioned Python 3.12 and stays torch-free

The Python job MUST provision Python 3.12 through `uv` (never the host
interpreter) and MUST install dependencies from `uv.lock` with `uv sync --frozen`,
selecting only the torch-free groups (core, `dev`, `test-cpu`). It MUST NOT install
the `oracle` extra.

#### Scenario: Python job installs the frozen torch-free environment

WHEN the Python job runs
THEN it SHALL provision Python 3.12 via `uv`
AND it SHALL run `uv sync --frozen --group test-cpu`
AND it SHALL NOT pass `--extra oracle`
AND `torch` SHALL NOT be importable in the job environment.

#### Scenario: Python job runs lint and CPU tests

WHEN the Python job's checks run
THEN it SHALL run `uv run ruff check api tests`
AND it SHALL run `uv run pytest -m "not gpu"`
AND both SHALL exit zero.

### Requirement: The WebUI job uses pinned Node and pnpm with a frozen lockfile

The WebUI job MUST use pnpm `11.3.0` and Node `22`, MUST install with
`pnpm install --frozen-lockfile`, and MUST set `NEXT_TELEMETRY_DISABLED=1`.

#### Scenario: WebUI job installs deterministically

WHEN the WebUI job runs
THEN it SHALL set up pnpm `11.3.0` and Node `22`
AND it SHALL run `pnpm install --frozen-lockfile`
AND it SHALL set `NEXT_TELEMETRY_DISABLED=1`.

#### Scenario: WebUI job runs the public checks in dependency order

WHEN the WebUI job's checks run
THEN it SHALL run, in order, the schema-sync diff, `pnpm build`, `pnpm lint`,
`pnpm typecheck`, and `pnpm test`
AND every step SHALL exit zero.

### Requirement: CI checks are reproducible locally from a documented command set

The session MUST document the exact local commands equivalent to each CI check, so
a contributor can reproduce CI without secrets, CUDA, weights, or private network.

#### Scenario: Local command list mirrors CI

WHEN the developer local-check command list in `docs/session_5/**` is read
THEN it SHALL list the `uv`-based Python commands and the `pnpm`-based WebUI
commands used by `ci.yml`
AND none of the listed commands SHALL require a secret, a GPU, or model weights.
