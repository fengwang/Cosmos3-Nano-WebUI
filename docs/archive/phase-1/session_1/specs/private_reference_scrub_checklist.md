# Private-Reference Scrub Checklist Specification

## ADDED Requirements

### Requirement: Scrub Pattern Groups

The session SHALL define scrub pattern groups for private hosts, private absolute paths, secrets, tokens, model weight paths, generated media paths, local-only artifacts, and unsupported legacy submodules.

#### Scenario: Private Reference Scan

WHEN a future session runs the scrub checklist from a clean shell
THEN `docs/session_1/scrub_checklist.md` MUST provide commands that work even if `$PRIVATE_REF_PATTERN` is unset.

### Requirement: Release-Blocking Scan Results

The scrub checklist SHALL define which scan matches block the session and how to classify allowed placeholder examples.

#### Scenario: Placeholder Path Example

WHEN a scan matches an allowed placeholder such as `/path/to/Cosmos3-Nano-FP8-Blockwise`
THEN `docs/session_1/scrub_checklist.md` MUST require the worker to record it as an allowed placeholder rather than a private leak.

#### Scenario: Real Secret Or Private Path

WHEN a scan matches a token, key, private hostname, or real private absolute path
THEN `docs/session_1/scrub_checklist.md` MUST require the worker to classify the failure before fixing and block the commit until the match is removed.

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
