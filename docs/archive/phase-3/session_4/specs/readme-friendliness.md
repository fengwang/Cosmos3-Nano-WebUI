# Spec — readme-friendliness

Capability introduced by UX-S4. Refs FR-9. Source: `docs/session_4/proposal.md`,
`docs/session_4/design.md` D1/D2.

## ADDED Requirements

### Requirement: Features-first structure

The `README.md` SHALL present *what the project does* and its *feature/status
table* before the quickstart, and SHALL NOT contain a development/CI command
block (the `uv sync` / `ruff` / `pytest` / `pnpm build|lint|typecheck|test` /
CI-mirror commands).

#### Scenario: Newcomer opens the README

- **WHEN** a reader opens `README.md` from the top
- **THEN** a "what it does" summary and the Features table appear before the
  "Quickstart" heading
- **AND** no development/CI command block (`uv sync`, `ruff`, `pytest`,
  `pnpm build/lint/typecheck/test`) appears anywhere in `README.md`.

### Requirement: Runnable few-minute quickstart

The `README.md` SHALL contain a quickstart that a new user can follow in a few
minutes, and it MUST retain every must-have step: clone, download a pinned public
checkpoint, `make build`, `make up-fp8`, `make health`, and open the Web UI.

#### Scenario: User follows the quickstart end to end

- **WHEN** a new user reads the Quickstart section
- **THEN** it contains, in order, a `git clone`, an `hf download` of the pinned
  FP8 checkpoint, `make build`, `make up-fp8`, `make health`, and the Web UI URL
- **AND** it states that no authentication needs to be configured and that the
  shipped defaults already produce recommended quality and a 720p video default.

### Requirement: Development/CI owned by CONTRIBUTING.md

`CONTRIBUTING.md` SHALL be the single owner of the development/CI workflow;
`README.md` SHALL reference it rather than restate the commands.

#### Scenario: Contributor looks for the checks to run

- **WHEN** a contributor searches for the CPU-check commands
- **THEN** the `uv sync` / `ruff` / `pytest` / `pnpm` command workflow is present
  in `CONTRIBUTING.md`
- **AND** `README.md` links to `CONTRIBUTING.md` for the full workflow and does
  not duplicate those commands.

### Requirement: Relaxed trusted-LAN tone

The `README.md` SHALL frame the project as a trusted-LAN appliance and SHALL NOT
open with a beta banner that forbids the intended use; honesty is retained via
the Status & security section, not a top-of-file warning.

#### Scenario: Reader forms a first impression

- **WHEN** a reader views the top of `README.md`
- **THEN** the first screenful leads with what the project is and a light
  trusted-LAN pointer
- **AND** it does not contain a `[!WARNING]` banner stating the project is "not
  intended for production or untrusted, internet-facing use" as the framing.
