# Specification: Quant Loader Isolation

## ADDED Requirements

### Requirement: Branch Contains Only Model-Agnostic Quant Loader Code

If upstream does not already cover the feature, the isolated branch MUST contain only model-agnostic quant-loader code, registration hooks, the isolated NVFP4 NaN-clamp hunk, and narrow tests for touched surfaces.

#### Scenario: Cosmos3 Code Is Excluded

WHEN the isolated branch diff is inspected
THEN it SHALL NOT include Cosmos3 model, pipeline, guard, adapter, or runtime files.

#### Scenario: Quant Loader Files Are Included

WHEN the isolated branch diff is inspected
THEN it SHALL include the FP8/NVFP4 quant-loader files and checkpoint-adapter files needed for the model-agnostic loader behavior if those files are absent upstream.

### Requirement: Narrow Tests Cover Touched Surfaces

The isolated branch MUST include or preserve narrow CPU tests for the touched quant-loader surfaces.

#### Scenario: Tests Fail On Missing Loader Behavior

WHEN FP8/NVFP4 loader behavior is absent or incorrectly wired
THEN at least one targeted test SHALL fail before broad GPU or PR checks are needed.

#### Scenario: Tests Avoid Cosmos3 Fixtures

WHEN targeted tests run on the isolated branch
THEN they SHALL NOT require Cosmos3 model weights, Cosmos3 pipeline imports, GPU hardware, or private files.

### Requirement: Actions And Calculations Stay Separated

Quant-loader logic MUST keep parsing, remapping, shape checks, target matching, and dequant math as pure calculations unless an existing upstream adapter boundary requires file access. File discovery and checkpoint loading SHALL remain at adapter boundaries.

#### Scenario: Pure Name Calculation Is Testable

WHEN a target-name or scale-name calculation is tested
THEN it SHALL accept explicit input values and return deterministic output without reading files, environment variables, or global mutable state.
