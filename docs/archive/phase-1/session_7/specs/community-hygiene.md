# Specification - Community Hygiene Files

Session: MIG-S7
Capability: community-hygiene

## ADDED Requirements

### Requirement: MIT LICENSE scoped to repo code

The repository root MUST contain a `LICENSE` file with the MIT license text for the
WebUI/API code. The license MUST be presented as covering the repository code only, not
the Hugging Face model weights.

#### Scenario: LICENSE exists and is MIT

WHEN `test -f LICENSE` runs
THEN it SHALL succeed
AND the file SHALL contain the MIT license body and a copyright line.

#### Scenario: LICENSE does not claim the model weights

WHEN the README and `LICENSE`/checkpoint docs are read together
THEN they SHALL make clear that MIT covers repo code and the model weights carry their
own licenses (`openmdw-1.0` / `other`).

### Requirement: SECURITY.md uses private reporting

The repository MUST contain `SECURITY.md` that directs vulnerability reports to a private
channel (GitHub private vulnerability reporting and/or an email address) and MUST instruct
reporters NOT to open a public issue for a vulnerability. It MUST state the beta /
research-preview support posture.

#### Scenario: SECURITY.md exists and forbids public disclosure

WHEN `test -f SECURITY.md` runs
THEN it SHALL succeed
AND the file SHALL provide a private reporting route and SHALL explicitly ask reporters
not to file a public issue for a security vulnerability.

### Requirement: CONTRIBUTING.md with specific commands

The repository MUST contain `CONTRIBUTING.md` that documents the contribution workflow
with specific commands (not greedy ones), mirrors the CI checks, and links the Code of
Conduct.

#### Scenario: CONTRIBUTING.md exists and mirrors CI

WHEN `test -f CONTRIBUTING.md` runs
THEN it SHALL succeed
AND it SHALL list the local check commands that correspond to `.github/workflows/ci.yml`
(Python lint/tests via `uv`, WebUI build/lint/typecheck/test via `pnpm`)
AND it SHALL link `CODE_OF_CONDUCT.md`.

#### Scenario: Contribution steps avoid greedy add commands

WHEN the commit guidance in `CONTRIBUTING.md` is read
THEN it SHALL prefer explicit `git add <path>` over `git add .` to avoid committing
unwanted files.

### Requirement: Code of Conduct is present

The repository MUST contain `CODE_OF_CONDUCT.md` (Contributor Covenant) with a working
enforcement-contact placeholder.

#### Scenario: CODE_OF_CONDUCT.md exists

WHEN `test -f CODE_OF_CONDUCT.md` runs
THEN it SHALL succeed
AND it SHALL contain a Contributor Covenant body with an enforcement contact.

### Requirement: Issue and PR templates request no sensitive data

The repository MUST provide `.github/ISSUE_TEMPLATE/bug_report.yml`,
`.github/ISSUE_TEMPLATE/feature_request.yml`, `.github/ISSUE_TEMPLATE/config.yml`, and
`.github/PULL_REQUEST_TEMPLATE.md`. The templates MUST NOT request secrets, tokens, or
private paths, and `config.yml` MUST disable blank issues and route security reports to
the private channel.

#### Scenario: Templates exist and are safe

WHEN the issue and PR template files are read
THEN each SHALL exist
AND none SHALL ask the reporter for a secret, token, API key value, or private path.

#### Scenario: Blank issues are disabled and security is redirected

WHEN `.github/ISSUE_TEMPLATE/config.yml` is read
THEN it SHALL set `blank_issues_enabled: false`
AND it SHALL provide a contact link that directs security reports to the `SECURITY.md`
private channel rather than a public issue.

### Requirement: Release checklist gates beta

The repository MUST contain `docs/release_checklist.md` that captures the pre-beta gate:
private-reference scan, license separation, link check, CPU CI, and the manual GPU gates
deferred to `MIG-S8`.

#### Scenario: Release checklist exists and covers the gates

WHEN `docs/release_checklist.md` is read
THEN it SHALL enumerate the pre-release checks including the private-reference scan,
license-boundary review, link resolution, CPU CI pass, and the `MIG-S8` manual GPU gates.

### Requirement: Hygiene surface stays private-reference clean

All added hygiene files and templates MUST pass the committed private-reference scan.

#### Scenario: Private-reference scan is clean over hygiene files

WHEN `uv run python tests/test_private_ref_scan.py` runs after the hygiene files are added
THEN it SHALL report 0 findings.
