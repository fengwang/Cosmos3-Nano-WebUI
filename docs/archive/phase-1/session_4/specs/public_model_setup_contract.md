# Specification - Public Model Setup Contract

Session: MIG-S4
Capability: Public Model Setup Contract

## ADDED Requirements

### Requirement: Setup contract records repo IDs and pinned revisions

`docs/model_setup.md` MUST record the two public checkpoint repo IDs and their pinned
40-hex revisions, so Docker (S6) and README (S7) consume a fixed source of truth
rather than the mutable `main` branch alone.

#### Scenario: Repo IDs and revisions present

WHEN `docs/model_setup.md` is read
THEN it SHALL list `wfen/Cosmos3-Nano-FP8-Blockwise` with its recorded revision
AND `wfen/Cosmos3-Nano-NVFP4-Blockwise` with its recorded revision.

### Requirement: Environment variables and mount layout are documented

The contract MUST document the `COSMOS3_*` environment variables the runtime uses to
locate checkpoints, and a mount layout. All path examples MUST use placeholders
(`/path/to/<Repo>`) or the documented `/data/models/<Repo>` mount convention only
(INV-4); no dev-only checkpoint variant name or host path may appear.

#### Scenario: Env-var table present with configurable paths

WHEN `docs/model_setup.md` is read
THEN it SHALL include a table covering at least `COSMOS3_MODEL_DIR`,
`COSMOS3_REASONER_MODEL_DIR`, `COSMOS3_BASE_ACTION_DIR`, and `COSMOS3_CHECKPOINT_LABEL`
AND each documented path SHALL be a placeholder or the `/data/models/<Repo>` convention.

#### Scenario: No private specifics in the contract

WHEN `docs/model_setup.md` is scanned with the private-value pattern
THEN there SHALL be no dev-only checkpoint variant name, no host path, and no secret.

### Requirement: License separation is stated

The contract MUST state that the model weights carry the `openmdw-1.0` model license,
distinct from the repository's MIT code license (INV-7).

#### Scenario: Model vs repo license called out

WHEN `docs/model_setup.md` is read
THEN it SHALL state the model license `openmdw-1.0`
AND SHALL state that it is separate from the repository MIT license.

### Requirement: Per-mode compatibility matrix records verified backing and true residual limits

The contract MUST include a per-mode compatibility matrix grounded in the verification
evidence. Each mode's weight backing (which public repos supply its weights) MUST be
recorded, together with each residual limit: GPU-unverified runtime (the blanket `MIG-S8`
gate, INV-8) and any loader/serving incompatibility (drift D1). Because verification found
the declared BF16 base publicly available (`nvidia/Cosmos3-Nano`), no mode may be marked
beta-limited for a "non-public base"; any unverified status MUST be attributed to its true
cause. (Updated per Failure Arbiter FA-1: the original non-public-base premise was refuted
by `evidence.json`.)

#### Scenario: Matrix records weight backing and true residual limits

WHEN `docs/model_setup.md` is read
THEN each mode (generation `t2v`/`t2v_audio`/`i2v`/`t2i`, reasoning, action/`forward_dynamics`)
SHALL record the public repo(s) that supply its weights
AND generation SHALL cite the FP8/NVFP4 checkpoints while reasoning and action/`forward_dynamics`
SHALL cite the public base `nvidia/Cosmos3-Nano`
AND each mode's residual limit SHALL be recorded as GPU-unverified (`MIG-S8`) and, where it
applies, the D1 in-process-oracle incompatibility — not a non-public-base claim.

### Requirement: Contract respects session scope boundaries

The contract is an authoritative setup contract plus minimal operator notes. It MUST
NOT edit Docker/Compose files (S6) or rewrite the public README (S7), and it MUST
defer polished quickstart prose to S7.

#### Scenario: No Docker or README changes are made

WHEN the session diff is inspected
THEN no Dockerfile, Compose file, `.github/**`, or `README.md` SHALL be modified
AND `docs/model_setup.md` SHALL explicitly note that Docker wiring is S6 and public
README prose is S7.
