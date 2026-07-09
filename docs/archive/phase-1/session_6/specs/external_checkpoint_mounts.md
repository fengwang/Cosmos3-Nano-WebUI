# Specification - External Checkpoint Mounts

Session: MIG-S6
Capability: External Checkpoint Mounts

## ADDED Requirements

### Requirement: Checkpoints are operator-configurable external mounts

Checkpoint locations MUST be operator environment inputs (INV-4). The Compose stacks
MUST bind-mount an operator-supplied host directory into the generation container and
MUST NOT embed a checkpoint in any image. Defaults MUST be repo-relative placeholders
(`./models/<Repo>`), never a private or user-home absolute path (INV-1).

#### Scenario: Checkpoint path comes from the environment

WHEN the FP8 stack is rendered with no override
THEN the `vllm-omni` service SHALL bind-mount `./models/Cosmos3-Nano-FP8-Blockwise`
(or the `COSMOS3_FP8_DIR` value) to a fixed in-container path
AND `COSMOS3_MODEL_DIR` SHALL point at that in-container path.

#### Scenario: Operator can override the mount

WHEN `COSMOS3_FP8_DIR=/path/to/fp8-weights docker compose -f deploy/docker-compose.fp8.yml config` runs
THEN the rendered bind-mount source SHALL be `/path/to/fp8-weights`.

#### Scenario: No private or user-home path in defaults

WHEN either stack is rendered with no override
THEN the output SHALL contain no `/home/<user>`, no other private absolute path, and
no private host.

### Requirement: Environment surface matches the model setup contract

`.env.example` MUST document the checkpoint-relevant environment variables from
`docs/model_setup.md` — at least `COSMOS3_MODEL_DIR`, `COSMOS3_CHECKPOINT_LABEL`,
`COSMOS3_REASONER_MODEL_DIR`, `COSMOS3_BASE_ACTION_DIR`, `COSMOS3_GEN_ENGINE`,
`COSMOS3_VLLM_OMNI_URL`, `COSMOS3_GEN_CONTAINER`, `COSMOS3_DEVICE` — plus the deploy
wiring vars (`API_INTERNAL_URL`, `COSMOS3_API_KEY`, `WEBUI_PORT`, `API_PORT`, and the
per-stack checkpoint dir vars).

#### Scenario: Example env documents the checkpoint surface

WHEN `.env.example` is read
THEN it SHALL define the checkpoint variables above with repo-relative or documented
example values and inline comments citing `docs/model_setup.md`.

#### Scenario: Pinned revisions are documented for downloads

WHEN `.env.example` documents fetching weights
THEN it SHALL reference the pinned public repo ids and revisions from
`docs/model_setup.md` (FP8, NVFP4, and the `nvidia/Cosmos3-Nano` base) so operators
download the verified revisions.
