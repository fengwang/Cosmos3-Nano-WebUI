# Curated Import Manifest Specification

## ADDED Requirements

### Requirement: Allowed Import Categories

The session SHALL define the categories that `MIG-S3` may import: API source, WebUI source, schemas, tests, tools, selected non-Docker deploy support, fresh public docs, and project hygiene files.

#### Scenario: Future Source Import Uses Categories

WHEN `MIG-S3` starts a curated import
THEN `docs/session_1/import_manifest.md` MUST give category-level rules and proof requirements without naming private source paths.

### Requirement: Import Proof Requirements

The import manifest SHALL require later sessions to prove that imported files are public-safe, needed for runtime or tests, and free of private references.

#### Scenario: Candidate File Needs Proof

WHEN a future session considers importing a candidate file
THEN `docs/session_1/import_manifest.md` MUST require the future worker to classify the file, state why it belongs in the public beta, and run scrub scans before commit.

### Requirement: No Source Import In Session 1

The session SHALL not import runtime source files while defining import rules.

#### Scenario: Runtime Directory Appears

WHEN files under `api/**`, `webui/**`, `deploy/**`, `tools/**`, `schemas/**`, or `.github/**` are changed during `MIG-S1`
THEN the session MUST classify this as a blast-radius violation unless a contract amendment exists.

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
