# Specification - Private Reference Scan

Session: MIG-S5
Capability: Private Reference Scan

## ADDED Requirements

### Requirement: A committed, testable scan detects private references and secrets

The repository MUST provide a committed scan at `tests/test_private_ref_scan.py`
that detects private absolute paths, private hosts/codenames, secrets/tokens, and
committed model-weight/media files across the change-controlled surface
(`.github`, `api`, `webui`, `tests`, `schemas`, `docs`). The core detection MUST be
a pure function over file contents so it is unit-testable, and it MUST be runnable
both under pytest and as a standalone CLI (`__main__`).

#### Scenario: Clean tree yields zero findings

WHEN the scan runs against the current session tree
THEN it SHALL report zero findings and the pytest wrapper SHALL pass.

#### Scenario: A planted secret is caught

WHEN the pure scan function is given text containing a private-key header, an
`hf_`-prefixed token, or an `sk-`-prefixed token
THEN it SHALL report a finding for that input.

#### Scenario: A committed weight/media file is caught

WHEN the scan encounters a tracked file whose extension is a model-weight or
generated-media type (for example `.safetensors`, `.pt`, `.ckpt`, `.mp4`)
THEN it SHALL report a finding.

### Requirement: The scan ignores allowed placeholders and its own definition

The scan MUST NOT flag the documented placeholder examples
(`/path/to/Cosmos3-Nano-FP8-Blockwise`, `/path/to/Cosmos3-Nano-NVFP4-Blockwise`),
and MUST NOT flag the pattern definitions inside
`docs/session_1/scrub_checklist.md` or inside the scanner module itself
(`EV-MIG-SCRUB-COMMAND-SANITY`).

#### Scenario: Placeholders do not trip the scan

WHEN the scan encounters `/path/to/Cosmos3-Nano-FP8-Blockwise`
THEN it SHALL NOT report a finding for that path.

#### Scenario: Pattern documentation does not create false positives

WHEN the scan processes `docs/session_1/scrub_checklist.md` and its own source file
THEN it SHALL treat their pattern definitions as excluded
AND SHALL NOT report a finding for those documentation-only patterns.

### Requirement: The scan runs in CI and locally

The scan MUST execute inside the CPU CI Python job (as part of the pytest run) and
MUST be reproducible locally via a documented command.

#### Scenario: Scan participates in the Python job

WHEN the CI Python job runs `pytest -m "not gpu"`
THEN `tests/test_private_ref_scan.py` SHALL be collected and executed.

#### Scenario: Scan is runnable standalone

WHEN a developer runs the scanner's `__main__` CLI
THEN it SHALL scan the controlled surface and exit non-zero if any finding is
present.
