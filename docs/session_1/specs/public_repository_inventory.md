# Public Repository Inventory Specification

## ADDED Requirements

### Requirement: Current Repository Baseline

The session SHALL record the local branch, current commit, clean or dirty status, recent commit summary, remote configuration, current file tree, README state, logo state, and existing handoff state.

#### Scenario: Clean Local Baseline

WHEN `rtk git status --short --branch`, `rtk git rev-parse HEAD`, `rtk git log --oneline -n 8 --decorate`, `rtk git remote -v`, and `rtk rg --files` are run
THEN `docs/session_1/inventory.md` MUST record enough output to reconstruct the public repo baseline for later sessions.

#### Scenario: Existing Public Seed Files

WHEN the current tree contains `README.md` and `misc/logo.png`
THEN `docs/session_1/inventory.md` MUST record that `README.md` is empty and `misc/logo.png` is present without rewriting the README.

### Requirement: Baseline Check Classification

The session SHALL classify startup or baseline command failures before using replacement commands or fixing files.

#### Scenario: Shell Pattern Variable Missing

WHEN `$PRIVATE_REF_PATTERN` is not set
THEN the session MUST classify the contract scrub command gap as an environment or setup issue and MUST define a usable fallback scan in `docs/session_1/scrub_checklist.md`.

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
