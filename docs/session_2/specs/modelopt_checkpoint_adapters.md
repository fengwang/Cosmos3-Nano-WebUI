# Specification - ModelOpt Checkpoint Adapter Support

Session: MIG-S2
Capability: ModelOpt Checkpoint Adapter Support

## ADDED Requirements

### Requirement: ModelOpt-native adapters are registered through one adapter factory

vLLM-Omni SHALL expose ModelOpt-native checkpoint adapter selection through the
existing diffusion checkpoint adapter factory. FP8 blockwise, FP8 W8A16, NVFP4,
and existing mixed-precision behavior MUST be selected through explicit
compatibility predicates.

#### Scenario: Adapter factory selects compatible adapter

WHEN a test passes a source and quantization config matching a ModelOpt-native
FP8, FP8 W8A16, or NVFP4 checkpoint layout
THEN `get_checkpoint_adapter` SHALL return the matching adapter
AND it SHALL return `None` for unsupported source/config combinations.

### Requirement: Sidecar validation fails before weight-file discovery

ModelOpt-native adapters MUST validate required quantization sidecar metadata
before discovering or loading weight files, so malformed public checkpoints fail
deterministically and early.

#### Scenario: Missing sidecar metadata fails fast

WHEN a lightweight fixture omits required ModelOpt quantization sidecar metadata
THEN adapter construction or compatibility validation SHALL fail with a
documented exception
AND it SHALL not attempt model-weight iteration.

### Requirement: Tests do not require model weights

ModelOpt adapter tests SHALL use lightweight fixtures and monkeypatches rather
than public or private model weights.

#### Scenario: Targeted adapter tests run without checkpoint files

WHEN targeted adapter tests are run in the isolated Session 2 environment
THEN they SHALL not require CUDA, Hugging Face downloads, or model-weight files
unless the failure is classified and documented as an environment blocker.

