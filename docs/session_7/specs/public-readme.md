# Specification - Public README

Session: MIG-S7
Capability: public-readme

## ADDED Requirements

### Requirement: README exists and is non-empty

The repository root MUST contain a non-empty `README.md` that presents the project
(logo, one-line pitch, subtitle, badges) and serves as the entry point for GitHub
visitors, operators, and contributors.

#### Scenario: README is present and non-empty

WHEN `test -s README.md` runs
THEN it SHALL succeed (the file exists and has non-zero size).

#### Scenario: README references the tracked logo

WHEN `README.md` is rendered
THEN it SHALL embed the tracked `misc/logo.png` asset near the top.

### Requirement: Runtime claims are evidence-qualified

The README MUST NOT present unverified runtime behavior as a shipped capability. Every
statement about GPU inference, FP8/NVFP4 generation, RTX 5090, reasoning, or action MUST
be qualified as GPU-unverified and pointed at the `MIG-S8` manual gate or the evidence
map. The README MUST NOT contain a production-readiness assertion or a performance
guarantee.

#### Scenario: Generation modes are qualified

WHEN a reader reads the feature/capabilities section
THEN each generation, reasoning, and action mode SHALL be marked as code-present and
GPU-unverified (a `MIG-S8` manual gate), not as a proven runtime capability.

#### Scenario: No forbidden marketing claim in the README

WHEN `rg -n "production-ready|guaranteed|always|official" README.md` runs
THEN it SHALL return no match that functions as an unsupported production or performance
claim.

#### Scenario: Beta posture is stated up front

WHEN the top of the README is read
THEN it SHALL state that the project is a beta / research preview and SHALL link a
"Limitations" section covering GPU-unverified status, drift D1, and the Docker-socket
privilege (R-16).

### Requirement: Setup flow uses public inputs only

The README setup and quickstart MUST work from public inputs: a `git clone`, public
Hugging Face checkpoint downloads at pinned revisions, and a local Docker build. It MUST
NOT depend on an unpublished image, a private host, or a private absolute path. Example
paths MUST be repo-relative (`./models/<Repo>`) or the sanctioned placeholder
(`/path/to/...`).

#### Scenario: Quickstart is local-build and public-download

WHEN a reader follows the quickstart
THEN the steps SHALL be clone → download the public checkpoint(s) at their pinned
revisions → `make build` → bring up a stack — with no registry image pull and no private
path.

#### Scenario: No private reference in the README

WHEN `uv run python tests/test_private_ref_scan.py` runs over the tree including
`README.md`
THEN it SHALL report 0 findings.

### Requirement: License boundaries are separated

The README MUST present the repository-code license (MIT) separately from the model
weight licenses, and MUST state that the MIT license does not cover the Hugging Face
model weights.

#### Scenario: Three-way license separation is stated

WHEN the license and checkpoint-setup sections are read
THEN they SHALL state repo code = MIT, FP8/NVFP4 weights = `openmdw-1.0`, and base
`nvidia/Cosmos3-Nano` = `other`, and SHALL state that MIT does not cover the weights.

### Requirement: README is concise and links to docs

The README MUST stay concise and move detailed checkpoint material to the tracked
`docs/model_setup.md` rather than duplicating it. Every relative link in the README MUST
resolve to a tracked file.

#### Scenario: Checkpoint detail is linked, not duplicated

WHEN the checkpoint-setup section is read
THEN it SHALL summarize the repo IDs and pinned revisions and SHALL link
`docs/model_setup.md` for the full matrix.

#### Scenario: Relative links resolve

WHEN each relative link target in `README.md` is checked with `git ls-files`
THEN every target SHALL be a tracked path in the repository.
