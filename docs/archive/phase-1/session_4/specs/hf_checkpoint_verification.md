# Specification - HF Checkpoint Verification

Session: MIG-S4
Capability: HF Checkpoint Verification

## ADDED Requirements

### Requirement: Public HF repos are reachable and revisions are pinned

The verification MUST prove both public checkpoint repos
(`wfen/Cosmos3-Nano-FP8-Blockwise`, `wfen/Cosmos3-Nano-NVFP4-Blockwise`) are
reachable and MUST record each repo's resolved revision as a 40-character commit
SHA. The recorded revision SHALL be internally consistent between `git ls-remote`
and `HfApi.model_info().sha`.

#### Scenario: FP8 repo resolves and revision is recorded

WHEN the probe resolves `wfen/Cosmos3-Nano-FP8-Blockwise` via `git ls-remote HEAD`
and via `HfApi.model_info().sha`
THEN both SHALL return the same 40-hex commit SHA
AND that SHA SHALL be recorded in `evidence.json` and `docs/session_4/hf_verification.md`.

#### Scenario: NVFP4 repo resolves and revision is recorded

WHEN the probe resolves `wfen/Cosmos3-Nano-NVFP4-Blockwise` via `git ls-remote HEAD`
and via `HfApi.model_info().sha`
THEN both SHALL return the same 40-hex commit SHA
AND that SHA SHALL be recorded in `evidence.json` and `docs/session_4/hf_verification.md`.

### Requirement: Model license is recorded and kept separate from repo MIT license

The verification MUST record the model license reported by each repo's card
metadata. The model license MUST be documented as separate from the WebUI/API
repository's MIT code license (INV-7).

#### Scenario: Both repos report the model license

WHEN the probe reads `HfApi.model_info().card_data.license` for both repos
THEN each SHALL equal `openmdw-1.0`
AND the value SHALL be recorded per repo in `evidence.json`.

#### Scenario: License separation is documented

WHEN `docs/model_setup.md` is read
THEN it SHALL state that the model weights are licensed `openmdw-1.0`
AND that this is distinct from the repository's MIT code license.

### Requirement: Model-card state is recorded per repo

The verification MUST record whether each repo's model card is populated, empty, or
absent, because README (S7) depends on public model-card content.

#### Scenario: Card state recorded for both repos

WHEN the probe inspects each repo's `README.md` (presence and non-whitespace size)
THEN the FP8 card state SHALL be recorded as POPULATED or EMPTY or ABSENT
AND the NVFP4 card state SHALL be recorded as POPULATED or EMPTY or ABSENT
AND any EMPTY or ABSENT card SHALL be routed as drift (R-04).

### Requirement: Full public file manifest is captured with sizes and LFS SHAs

The verification MUST capture the complete public file listing for each repo, with
each file's byte size and (for LFS-tracked blobs) its LFS SHA, so downstream
sessions can reason about downloads and integrity without re-probing.

#### Scenario: Manifest captured for both repos

WHEN the probe calls `HfApi.list_repo_files` and `HfApi.get_paths_info` for a repo
THEN `evidence.json` SHALL contain every public file path
AND each entry SHALL carry its size
AND each LFS-tracked entry SHALL carry its LFS SHA.

### Requirement: Verification is reproducible without large downloads

The probe MUST be torch-free and MUST NOT download large weight blobs. It SHALL rely
on repo metadata plus partial (header-only) reads of already-present local files, and
SHALL be committed under `docs/session_4/probes/` so the evidence is re-runnable.

#### Scenario: Probe is torch-free and re-runnable

WHEN `docs/session_4/probes/` is inspected
THEN it SHALL contain the probe script and its emitted `evidence.json`
AND the probe SHALL import neither `torch` nor `diffusers`
AND running it SHALL regenerate the recorded revisions and manifest.
