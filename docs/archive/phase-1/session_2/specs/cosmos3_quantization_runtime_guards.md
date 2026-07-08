# Specification - Cosmos3 Quantization Runtime Guards

Session: MIG-S2
Capability: Cosmos3 Quantization Runtime Guards

## ADDED Requirements

### Requirement: FP8 W8A16 runtime path is explicit and testable

Cosmos3 FP8 W8A16 runtime support SHALL expose explicit configuration and method
selection behavior that can be tested without loading model weights.

#### Scenario: FP8 W8A16 config selects the resident method

WHEN a lightweight quantization config fixture requests FP8 W8A16 resident
serving
THEN the configured linear method SHALL be selected through the patch-provided
quantization surface
AND the test SHALL assert behavior without requiring CUDA execution.

### Requirement: NVFP4 runtime guard is explicit

Cosmos3 NVFP4 runtime support SHALL reject unsupported checkpoint/config states
with an explicit guard instead of silently falling back to an incompatible path.

#### Scenario: NVFP4 guard blocks unsupported load

WHEN a Cosmos3 NVFP4 load fixture presents an unsupported or incomplete config
THEN the loader or transformer guard SHALL raise a documented error
AND the error SHALL identify NVFP4 compatibility as the reason.

### Requirement: Cosmos3 pipeline and transformer hooks stay scoped

Cosmos3 pipeline and transformer edits MUST be limited to quantized checkpoint
loading and runtime guard behavior needed by the selected patch line.

#### Scenario: Patch does not broaden Cosmos3 product behavior

WHEN the final fork diff is reviewed against public fork `main`
THEN Cosmos3 pipeline and transformer changes SHALL be explainable by FP8 W8A16
or NVFP4 loading/runtime support
AND unrelated API or request-shape behavior SHALL remain unchanged.

