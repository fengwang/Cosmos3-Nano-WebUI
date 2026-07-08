# Specification - GPU Beta-Limited Disposition

Session: MIG-S8
Capability: gpu-beta-limited-disposition

## ADDED Requirements

### Requirement: Every GPU surface is a recorded manual gate

Each manual GPU case (`EV-MIG-GPU-FP8-T2V`, `-FP8-T2V-AUDIO`, `-FP8-I2V`, `-FP8-T2I`,
`-FP8-FD`, `-NVFP4-SURFACE`, `-REASONING`, `-JOBS-SSE`, `-ARTIFACTS`) MUST be recorded as
NOT-YET-RUN with the exact command to run it later and the evidence fields a later run must
capture (hardware, driver/CUDA, checkpoint repo + revision, vLLM-Omni commit, request shape,
artifact metadata, pass/fail).

#### Scenario: Each GPU case is enumerated and deferred

WHEN the GPU disposition is read
THEN every `EV-MIG-GPU-*` case SHALL appear with status NOT-YET-RUN and the deferred command
and required evidence fields.

#### Scenario: Pin and revisions are fixed for later runs

WHEN a GPU case records the artifacts it must match
THEN it SHALL name the vLLM-Omni pin `697035018b70…` and the checkpoint revisions (FP8
`4e181f99…`, NVFP4 `b5c9332e…`), so a later run against a different fork or revision is
detectable.

### Requirement: Unverified surfaces are marked so INV-8 holds

Because the beta ships with manual GPU gates, every unverified runtime surface MUST be
clearly marked as beta-limited in the release-facing docs, satisfying `INV-8`.

#### Scenario: README marking is confirmed

WHEN the disposition cross-checks the README
THEN it SHALL confirm that the README marks each generation/reasoning/action mode
GPU-unverified (`MIG-S8` gate), so no unverified surface reads as supported.

#### Scenario: Drift D1 is disclosed as a limitation

WHEN the disposition covers checkpoint loading
THEN it SHALL disclose drift D1 (the in-process oracle cannot load either public checkpoint
as-is; the default engine is the `vllm_omni` container path) as a beta limitation to resolve
in the GPU session.
