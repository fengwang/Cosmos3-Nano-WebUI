# Capability: checkpoint-fresh-verification-probe

Source: `docs/session_2/proposal.md` (New Capabilities)

## ADDED Requirements

### Requirement: Torch-Free And No Large Download
The probe MUST NOT import `torch` or `diffusers`, and MUST NOT require
downloading any checkpoint's large weight file (`*.safetensors`, `*.pt`) to
reach a verdict. It relies on client-tool invocations scoped to skip large
blobs (`GIT_LFS_SKIP_SMUDGE=1 git clone`, `hf download` with weight-file
excludes) plus `HfApi` manifest metadata.

#### Scenario: Probe runs without importing torch or diffusers
WHEN `docs/session_2/probes/verify_gpu_s2_checkpoints.py` runs to completion
THEN `torch` and `diffusers` are absent from `sys.modules`.

#### Scenario: Probe completes without a full weight download
WHEN the probe's fresh-clone step is inspected
THEN no request for a `*.safetensors` or `*.pt` byte range larger than the
LFS pointer-file size (≈130 bytes) is made.

### Requirement: Detects Stale Index Presence
The probe MUST report whether a top-level `model.safetensors.index.json`
exists at the probed revision, for each repo independently.

#### Scenario: Stale index reported present before the fix
WHEN the probe runs against the pre-fix revision (`4e181f99…` for FP8,
`b5c9332e…` for NVFP4)
THEN it reports `stale_index_present: true` for that repo.

#### Scenario: Stale index reported absent after the fix
WHEN the probe runs against the new post-fix revision for either repo
THEN it reports `stale_index_present: false`.

### Requirement: Detects Incorrectly-LFS'd Small Files
The probe MUST classify every file in the manifest as LFS-backed or a
regular blob (via `HfApi.get_paths_info`'s `.lfs` attribute, or the fresh
clone's own smudge behavior) and flag any file at or under 10 MB that is
plain text but still LFS-backed.

#### Scenario: Pre-fix manifest flags known-bad files
WHEN the probe runs against the pre-fix revision of
`wfen/Cosmos3-Nano-FP8-Blockwise`
THEN `config.json`, `checkpoint.json`, and `load_quantized.py` are each
flagged as "small plain-text file incorrectly LFS-backed".

#### Scenario: Post-fix manifest flags nothing
WHEN the probe runs against the new revision of either repo
THEN the flagged list is empty.

### Requirement: Confirms Large Files Remain LFS-Backed
The probe MUST confirm that every file over 10 MB or of a known binary type
is still reported as LFS-backed after the fix, with an unchanged LFS SHA256
relative to the pre-fix manifest.

#### Scenario: Transformer weight stays LFS with an unchanged SHA256
WHEN the probe compares the pre-fix and post-fix manifest entries for
`transformer/diffusion_pytorch_model.safetensors` (FP8) and
`transformer/model.safetensors` (NVFP4)
THEN both are LFS-backed in both manifests
AND each file's LFS SHA256 is identical between the two manifests.

### Requirement: Self-Check Runs Without Network
The probe MUST support a `--check` mode that runs pure-core assertions with
no network access and no filesystem access beyond its own source.

#### Scenario: `--check` passes offline
WHEN `python3 docs/session_2/probes/verify_gpu_s2_checkpoints.py --check` is
run with network access disabled
THEN it exits 0 and prints a self-check-passed message.
