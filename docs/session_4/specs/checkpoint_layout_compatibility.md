# Specification - Checkpoint Layout Compatibility

Session: MIG-S4
Capability: Checkpoint Layout Compatibility

## ADDED Requirements

### Requirement: Public layout is checked against the diffusers loader's transformer discovery

The verification MUST check each public repo's layout against
`api/engines/diffusers_oracle/loader.py:discover_transformer_dir`, which requires a
transformer directory containing `*.safetensors` + `modelopt_state.pt` +
`config.json` (nested `transformer/transformer/` tried first, then flat
`transformer/`). Any missing required artifact MUST be recorded as drift with its
loader impact.

#### Scenario: FP8 transformer directory satisfies discovery

WHEN the probe evaluates the FP8 public manifest against the discovery requirement
THEN a transformer directory SHALL be found containing `config.json`,
`modelopt_state.pt`, and at least one `*.safetensors`
AND the finding SHALL be recorded as SATISFIED.

#### Scenario: NVFP4 transformer discovery is evaluated and any gap is drift

WHEN the probe evaluates the NVFP4 public manifest against the discovery requirement
THEN the presence of `config.json`, `modelopt_state.pt`, and `*.safetensors` SHALL be
recorded for the discovered transformer directory
AND if any required artifact is absent, the finding SHALL be MISSING and raised as
drift D1 with its loader impact documented (does the observe-precision fallback still
resolve, or is the load blocked).

### Requirement: Precision metadata is verifiable

The verification MUST determine each checkpoint's quantization precision. Precision
MAY come from `<root>/quantization_config.json` (`recipe`, `scale_layout.granularity`)
and/or from safetensors header keys (`weight_quantizer._double_scale` present ⇒ NVFP4,
absent ⇒ FP8). A disagreement between the two sources MUST be recorded as drift.

#### Scenario: FP8 precision resolves to FP8

WHEN the probe reads FP8 precision from `quantization_config.json` and/or header keys
THEN the resolved precision SHALL be FP8
AND the source(s) used SHALL be recorded.

#### Scenario: NVFP4 precision resolves to NVFP4

WHEN the probe reads NVFP4 precision from `quantization_config.json` and/or header keys
THEN the resolved precision SHALL be NVFP4
AND if `quantization_config.json` is absent, the precision SHALL be resolved from
header keys and the absence SHALL be recorded as part of drift D1.

### Requirement: Self-containment for the generation path is confirmed

The verification MUST confirm that each public repo is self-contained for the
diffusers generation path — it ships the pipeline components the oracle/action
engines expect without requiring a separate download.

#### Scenario: Generation components present in both repos

WHEN the probe evaluates each public manifest
THEN each repo SHALL contain `model_index.json`, `config.json`,
`generation_config.json`, and the `vae/`, `text_tokenizer/`, `vision_encoder/`,
`sound_tokenizer/`, and `scheduler/` component directories
AND the self-containment finding SHALL be recorded per repo.

### Requirement: Local header probes describe the public artifact

Because the local mount may hold a different build, the verification MUST cross-check
each locally-probed file's blob SHA against the public LFS SHA. Only files whose local
SHA equals the public LFS SHA (`MATCH`) may have their header findings treated as
describing the public artifact.

#### Scenario: Local files are gated by SHA cross-check

WHEN the probe reads a local `*.safetensors` header and the file is LFS-tracked publicly
THEN the probe SHALL compare the local blob SHA to the public LFS SHA
AND a `MATCH` SHALL mark the header finding as verified-for-public
AND a `MISMATCH`, `LOCAL_ABSENT`, or `NO_LFS_SHA` SHALL downgrade the finding to
public-manifest-only and record the reason.

### Requirement: BF16-dependent modes are identified

The verification MUST identify runtime modes that depend on a BF16 base model not
covered by the two public repos, and MUST record the base repo's reachability.

#### Scenario: Base model requirement and reachability recorded

WHEN the probe checks reachability of the BF16 base repo `wfen/Cosmos3-Nano`
THEN the reachability SHALL be recorded as REACHABLE or NOT_FOUND or ERROR
AND the reasoner (`COSMOS3_REASONER_MODEL_DIR`) and action/forward_dynamics
(`COSMOS3_BASE_ACTION_DIR`) dependence on that base SHALL be recorded
AND a NOT_FOUND result SHALL feed the beta-limited compatibility matrix.
