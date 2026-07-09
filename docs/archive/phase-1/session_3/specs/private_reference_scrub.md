# Specification - Private Reference Scrub

Session: MIG-S3
Capability: Private Reference Scrub

## ADDED Requirements

### Requirement: Imported files contain no private references

Imported source, config, schema, test, and tool files MUST NOT contain private
hosts, private absolute paths, private codenames, private repository names,
secrets, or tokens. The Session 3 private-reference pattern SHALL cover at least:
RFC1918 intranet hosts (the private host in the source `.gitmodules`), private
home / checkout paths, a sibling private quantization repo name and private
codenames, checkpoint suffixes `-wfen` and `-dist`,
`hf_[A-Za-z0-9]{20,}`, `sk-[A-Za-z0-9_-]{20,}`, and private-key headers.

#### Scenario: Private-reference scan is clean

WHEN the Session 3 private-reference pattern is scanned over the imported tree
(excluding `docs/session_3/**` scan documentation)
THEN there SHALL be no match
AND the scan SHALL exit non-zero (no matches).

### Requirement: Checkpoint locations are operator env inputs

Real checkpoint directories SHALL be resolved from operator environment variables
(`COSMOS3_*_MODEL_DIR` and equivalents). `/data/models` MAY remain only as a
documented container-mount convention and as the trust-boundary allowlist root in
path tests; it MUST NOT be combined with a private specific (for example `-wfen`
or `-dist`) in imported source or kept tests.

#### Scenario: Source default resolves from env

WHEN `tools/checkpoint_prep/copy_shared.py` is read
THEN the BF16 base reference SHALL be resolvable from an environment variable
AND any literal default SHALL use the `/data/models/Cosmos3-Nano` mount convention,
not a `-wfen`/`-dist` or home path.

#### Scenario: No private checkpoint specifics remain

WHEN the imported tree is scanned for `-wfen`, `-dist`, and the private home /
checkout paths
THEN there SHALL be no match.

### Requirement: Submodule and private-host config is removed

`.gitmodules` and all `submodules/` gitlinks MUST NOT be imported, and no imported
file may reference the private vLLM-Omni host.

#### Scenario: No submodule config or private host

WHEN the repo root is listed and the imported tree is scanned
THEN `.gitmodules` SHALL be absent
AND no `submodules/` path SHALL be present
AND the private intranet host SHALL NOT appear in any imported file.

### Requirement: Scrub report is recorded

Session 3 SHALL record a scrub report documenting the pattern used, the matches
found, each disposition, the `/data/models` decision, and the final clean scan.

#### Scenario: Scrub report present with final clean scan

WHEN `docs/session_3/scrub_report.md` is read
THEN it SHALL contain the private-reference pattern, the enumerated dispositions,
the `/data/models` mount-convention decision, and a final scan showing no
release-blocking match.
