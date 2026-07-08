# Target Remote Baseline Specification

## ADDED Requirements

### Requirement: Public Git Remote Baseline

The session SHALL record public WebUI and vLLM-Omni remote URLs and reachable HEAD or branch commits from `git ls-remote`.

#### Scenario: WebUI Remote Reachable

WHEN `rtk git ls-remote git@github.com:fengwang/Cosmos3-Nano-WebUI.git HEAD 'refs/heads/*'` succeeds
THEN `docs/session_1/inventory.md` MUST record the WebUI public remote URL and the observed HEAD/main commit.

#### Scenario: vLLM-Omni Remote Reachable

WHEN `rtk git ls-remote git@github.com:fengwang/vllm-omni.git HEAD 'refs/heads/*'` succeeds
THEN `docs/session_1/inventory.md` MUST record the vLLM-Omni public remote URL and the observed HEAD/main commit.

### Requirement: Public Checkpoint Target IDs

The session SHALL record the public Hugging Face checkpoint repo IDs named by the PRD without validating their file layout or runtime compatibility.

#### Scenario: Checkpoint Targets Recorded

WHEN `docs/prd.md` names `wfen/Cosmos3-Nano-FP8-Blockwise` and `wfen/Cosmos3-Nano-NVFP4-Blockwise`
THEN `docs/session_1/inventory.md` MUST list those repo IDs as targets for `MIG-S4` and MUST state that checkpoint validation is out of scope for `MIG-S1`.

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
