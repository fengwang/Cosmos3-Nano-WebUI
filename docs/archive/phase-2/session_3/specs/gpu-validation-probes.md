# Capability: GPU Validation Probes

## ADDED Requirements

### Requirement: Evidence record schema
Every probe in this capability SHALL record its outcome as an `EvidenceRecord`
containing `task_id`, `hardware`, `driver_cuda`, `checkpoint_repo`,
`checkpoint_revision`, `vllm_omni_commit`, `request_shape`, `artifact_path`,
`artifact_metadata`, `verdict`, and `notes`. `verdict` SHALL be one of
`PASS`, `FAIL`, or `SCOPED_OUT` — never a bare boolean. `notes` SHALL be
non-empty whenever `verdict` is not `PASS`.

#### Scenario: A probe records a passing result
- **WHEN** a probe's action and check both succeed
- **THEN** it writes an `EvidenceRecord` with `verdict: PASS`, a non-null
  `artifact_path`/`artifact_metadata` where applicable, and every INV-8
  field populated (hardware, driver/CUDA, checkpoint repo+revision,
  vLLM-Omni commit, request shape, pass/fail)

#### Scenario: A probe records a failing result instead of crashing
- **WHEN** an action (download, compose lifecycle, HTTP call) raises an
  unexpected exception
- **THEN** the probe's single narrow exception boundary catches it and
  writes an `EvidenceRecord` with `verdict: FAIL` and `notes` containing the
  exception detail, rather than letting the process crash with no recorded
  evidence

### Requirement: Fresh checkpoint fetch verification
The checkpoint-fetch probe SHALL perform a genuinely fresh `hf download` of
both `wfen/Cosmos3-Nano-{FP8,NVFP4}-Blockwise` repos at the `GPU-S2`-pinned
revisions into `models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise` (repo-root
relative), and SHALL NOT reuse or read from any pre-existing local checkpoint
directory (including `/data/models/Cosmos3-Nano-*` paths from earlier
sessions) as a substitute for the download.

#### Scenario: Fresh download resolves with no manual workaround
- **WHEN** the checkpoint-fetch probe completes for a given checkpoint
- **THEN** it SHALL verify no file under the downloaded directory is an
  unresolved LFS/Xet pointer and no stale top-level
  `model.safetensors.index.json` is present, and record `verdict: PASS`
  only if both checks hold

#### Scenario: A pre-existing local directory is never substituted
- **WHEN** the checkpoint-fetch probe runs
- **THEN** it SHALL target a clean `models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise`
  directory for this session's download and SHALL NOT read checkpoint files
  from any other pre-existing path on the host as if they were this
  download's output

### Requirement: Direct generation verification
The direct-generation probe SHALL, for a given checkpoint (`fp8` or
`nvfp4`), bring up the matching compose overlay, submit a text-to-image
generation request straight to the vLLM-Omni container (bypassing the api
layer), and validate the returned artifact is a well-formed image at the
requested dimensions before recording `verdict: PASS`.

#### Scenario: Direct FP8 and NVFP4 T2I both succeed
- **WHEN** the direct-generation probe is run once for `fp8` and once for
  `nvfp4` against the fresh checkpoints and the `GPU-S1` image
- **THEN** each run SHALL record a `PASS` `EvidenceRecord` with a valid
  image artifact and the exact `vllm_omni_commit`
  (`697035018b70cef76b974a909d23371a9984c3f2`)

#### Scenario: Only one compose stack is ever up at a time
- **WHEN** the direct-generation probe finishes one checkpoint and starts
  the next
- **THEN** it SHALL tear down the previous compose stack before bringing up
  the next one, since both overlays share a fixed container name

### Requirement: Full-stack generation verification
The full-stack probe SHALL, for a given checkpoint, submit a generation
request through the api using the configured `X-API-Key`, poll the returned
job until it reaches a terminal state, and retrieve and validate the
resulting artifact — never bypassing auth and never reading the artifact
directly from the generation container.

#### Scenario: Full-stack FP8 and NVFP4 T2I both succeed end to end
- **WHEN** the full-stack probe posts a generation request with a valid
  `X-API-Key` for a given checkpoint
- **THEN** the job SHALL reach a terminal `succeeded` state and the artifact
  SHALL be retrievable via the api and pass the same image-validity check as
  the direct path, recorded as `verdict: PASS`

#### Scenario: A job that never reaches a terminal state is a failure, not a hang
- **WHEN** polling exceeds the probe's documented timeout without the job
  reaching a terminal state
- **THEN** the probe SHALL record `verdict: FAIL` with `notes` stating the
  timeout, rather than polling indefinitely or reporting no result
