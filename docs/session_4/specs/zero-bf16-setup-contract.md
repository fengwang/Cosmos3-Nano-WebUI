# Capability: zero-bf16-setup-contract

`docs/model_setup.md` is the authoritative setup contract; it SHALL require only the
quantized checkpoint(s) for every default mode. Status: MODIFIED.

Refs: PRD FR-4, NFR-5, INV-4, E-14 (license discrepancy stays AM-S6).

## MODIFIED Requirements

### Requirement: Setup requires only the quantized checkpoint(s)

`docs/model_setup.md` SHALL state that reasoning and action need no separate BF16 base,
and SHALL NOT instruct the operator to download `nvidia/Cosmos3-Nano` for any default
mode. The mount layout SHALL NOT list the BF16 base as required.

#### Scenario: Setup steps omit the BF16 base as a requirement

- WHEN an operator follows the `docs/model_setup.md` operator-setup steps for the FP8
  stack
- THEN only the FP8 quantized checkpoint download is required for all three modes
- AND the BF16 base is described as needed only by the legacy/dormant paths, not any
  default mode

### Requirement: Per-mode matrix reflects verified reality

The per-mode compatibility matrix SHALL show reasoning served by the FP8 reasoner
container off the quantized checkpoint and marked GPU-verified on FP8 (AM-S2, owner
PASS), and action served by the `vllm_omni` container off the quantized checkpoint and
GPU-verified on FP8 (AM-S3, owner PASS). Neither row SHALL name the BF16 base as its
serving path.

#### Scenario: Reasoning row updated

- WHEN a reader consults the per-mode matrix for reasoning
- THEN its serving path is the FP8 reasoner container off the quantized checkpoint
- AND its status is GPU-verified FP8 (AM-S2), not "GPU-unverified (S8), BF16 base"

#### Scenario: No default mode maps to the BF16 base

- WHEN a reader scans the matrix's serving-path column
- THEN no default mode (t2i/t2v*/reasoning/action) lists the BF16 base as its serving
  path

### Requirement: BF16 base demoted to legacy/dormant

The checkpoint table and environment-variable table SHALL mark the BF16 base and its
env (`COSMOS3_REASONER_MODEL_DIR`, `COSMOS3_BASE_ACTION_DIR`) as legacy/dormant-only,
consistent with `.env.example`. No new pinned revision is introduced (no re-export this
session), so existing quantized revisions and their `t2i` verification stand unchanged
(NFR-5).

#### Scenario: Env table marks BF16 vars legacy

- WHEN a reader consults the environment-variable table
- THEN `COSMOS3_REASONER_MODEL_DIR` and `COSMOS3_BASE_ACTION_DIR` are marked
  legacy/dormant with no default required for any live mode

#### Scenario: No checkpoint re-export this session

- WHEN the setup contract's pinned revisions are compared before and after AM-S4
- THEN the FP8 and NVFP4 quantized revisions are unchanged
- AND no new action-bundled revision is introduced
