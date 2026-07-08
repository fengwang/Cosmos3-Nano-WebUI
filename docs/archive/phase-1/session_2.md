# Session 2 - vLLM-Omni Patch Rebase and GitHub Fork Pin

Contract: `docs/session_2_contract.yaml`
Risk: high
Routing: branch_and_compare

## Objective

Move the Cosmos3 vLLM-Omni patch line onto the public GitHub fork, verify it
against the current fork base, and produce a public commit or tag that
Cosmos3-Nano-WebUI can pin.

## Why This Session Exists

The WebUI/API runtime depends on patched vLLM-Omni behavior for quantized
Cosmos3 checkpoints. The public WebUI repo cannot depend on a private checkout or
unpublished local patch. The patch must be rebased, tested, and pinned in the
GitHub fork first.

## In Scope

1. Confirm the current GitHub fork base commit.
2. Import the authorized Cosmos3 patch series into a working branch on the fork.
3. Rebase or merge onto the current fork base.
4. Resolve conflicts in Cosmos3 model, checkpoint adapter, and quantization
   surfaces only.
5. Run deterministic vLLM-Omni tests that do not require model weights, plus any
   lightweight adapter probes available from public fixtures.
6. Publish or prepare a branch, commit, or tag that the WebUI repo can pin.
7. Record install instructions for consuming the fork from Docker/build config.

## Out of Scope

- No WebUI/API source import.
- No model weight validation.
- No Docker image publishing.
- No upstream PR to the main vLLM-Omni project unless separately approved.

## Deliverables

- Public vLLM-Omni branch and pinned commit or tag.
- Rebase notes with conflict resolutions.
- Test evidence and known limitations.
- WebUI dependency pin recommendation for `MIG-S6`.

## Deterministic Checks

```bash
rtk git status --short --branch
rtk git remote -v
rtk git log --oneline -n 20
rtk pytest -q tests/quantization tests/diffusion || true
rtk python -m compileall vllm_omni
```

The exact test paths may change with the fork. Record skipped or unavailable
checks explicitly.

## Exit Criteria

- `GATE-MIG-S2-VLLM` passes.
- The pinned public commit exists on the GitHub fork.
- Tests pass or failures are classified and accepted by the owner.
- `MIG-S6` has a precise public install target.

## Handoff

Hand off the pinned vLLM-Omni commit/tag, install command, test result summary,
and any runtime caveats to `MIG-S3`, `MIG-S4`, and `MIG-S6`.

