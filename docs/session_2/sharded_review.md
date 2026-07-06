# Session 2 Sharded Review

Date: 2026-07-06
Session: MIG-S2
Risk: high
Verifier scope: WebUI Session 2 docs plus external vLLM-Omni fork diff
`origin/main...697035018b70cef76b974a909d23371a9984c3f2`

## Method

Dedicated subagent review was attempted, but the available subagent channel
returned a usage-limit error. The review was completed locally against the
required axes:

- correctness
- security/safety
- tests
- architecture/maintainability
- performance

## Findings

### F1 - Public docs recorded private source details

- Severity: High
- Axis: security/safety
- Evidence: Session 2 brainstorming/proposal/plan docs recorded the local source
  checkout path and source identifiers before review.
- Violated contract clause: `docs/project_contract.md` INV-1 and PRD FR-2/NFR-1
  forbid private absolute paths and local-only artifact references in public
  files.
- Smallest safe fix: replace private source path, private branch, and private
  source-hash details with public-safe placeholders and owner-authorized
  eight-commit source descriptor.
- Status: Fixed in Session 2 docs. Rechecked with a targeted private-detail scan.
- Confidence: High

### F2 - NVFP4 sidecar preflight was missing before weight-file discovery

- Severity: High
- Axis: correctness, tests
- Evidence: `vllm_omni/diffusion/model_loader/diffusers_loader.py` called
  `ModelOptNativeFp8CheckpointAdapter.validate_source_sidecar(source)` before
  `_prepare_weights`, but did not call the NVFP4 validator even though
  `ModelOptNativeNvfp4CheckpointAdapter.validate_source_sidecar` exists.
- Violated contract clause:
  `docs/session_2/specs/modelopt_checkpoint_adapters.md`, requirement
  "Sidecar validation fails before weight-file discovery".
- Smallest safe fix: import/export `ModelOptNativeNvfp4CheckpointAdapter`, call
  `validate_source_sidecar(source)` before `_prepare_weights`, and add a loader
  test proving `_prepare_weights` is not invoked when NVFP4 preflight fails.
- Status: Fixed in public fork commit
  `697035018b70cef76b974a909d23371a9984c3f2`.
- Recheck:
  `rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_diffusers_loader.py::test_get_weights_iterator_validates_nvfp4_sidecar_before_weight_discovery`
  passed.
- Confidence: High

## Axis Results

Correctness: PASS after F2 fix. The branch preserves the eight selected patch
commits and adds one review-fix commit. Adapter dispatch, sidecar parsing,
resident FP8 W8A16 routing, NVFP4 W4A16 routing, and pipeline FP8 guard behavior
are covered by targeted tests.

Security/Safety: PASS after F1 fix. No model weights, secrets, registry
credentials, private source paths, or private host references were added to the
WebUI docs or fork patch.

Tests: PASS after F2 fix. The expanded targeted suite passed with 118 tests. The
contract-listed NVFP4 config path under `tests/diffusion/quantization/` remains a
stale path and is classified as AMBIGUITY; the actual preserved patch path is
`tests/model_executor/quantization/test_nvfp4_blockwise_config.py`.

Architecture/Maintainability: PASS. New behavior stays isolated to checkpoint
adapters, quantization config surfaces, Cosmos3 load hooks, and matching tests.
The W8A16 selection predicate is shared by construction and load dispatch.

Performance: PASS with residual risk. Deterministic CPU tests validate the
weight-resident path and per-op dequant calculation. GPU throughput and VRAM
claims remain out of scope for Session 2 and must be verified in later GPU gates.

## Deduplicated Disposition

- High/Critical fixed: F1, F2.
- Medium: none requiring Session 2 code change.
- Low/Nit: none recorded.
