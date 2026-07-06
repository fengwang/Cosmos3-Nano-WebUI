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

### Requirement: Per-mode compatibility matrix marks unbacked modes beta-limited

The contract MUST include a per-mode compatibility matrix. Modes backed by the two
public checkpoints (generation: `t2v`, `t2v_audio`, `i2v`, `t2i`) MUST be marked
backed. Modes requiring the non-public BF16 base (reasoning, action/`forward_dynamics`)
MUST be marked beta-limited with the reason recorded.

#### Scenario: Matrix distinguishes backed from beta-limited modes

WHEN `docs/model_setup.md` is read
THEN generation modes SHALL be marked as backed by the public checkpoints
AND reasoning and action/`forward_dynamics` SHALL be marked beta-limited
AND the reason (non-public BF16 base model) SHALL be recorded for each beta-limited mode.

### Requirement: Contract respects session scope boundaries

The contract is an authoritative setup contract plus minimal operator notes. It MUST
NOT edit Docker/Compose files (S6) or rewrite the public README (S7), and it MUST
defer polished quickstart prose to S7.

#### Scenario: No Docker or README changes are made

WHEN the session diff is inspected
THEN no Dockerfile, Compose file, `.github/**`, or `README.md` SHALL be modified
AND `docs/model_setup.md` SHALL explicitly note that Docker wiring is S6 and public
README prose is S7.
