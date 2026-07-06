# Session 4 - Hugging Face Checkpoint Verification and Model Setup Docs

Contract: `docs/session_4_contract.yaml`
Risk: high
Routing: branch_and_compare

## Objective

Verify the public FP8 and NVFP4 Hugging Face checkpoints and define the model
setup contract that Docker, README, and manual GPU gates will use.

## Why This Session Exists

The public beta uses external weights. Public docs and Docker examples cannot
assume that checkpoint layout, license metadata, model cards, or runtime
compatibility match development expectations. The HF artifacts need their own
public evidence.

## In Scope

1. Verify both HF repos are reachable and record commit/revision IDs.
2. Record license metadata and model-card state.
3. List files needed by the WebUI/API runtime without downloading unnecessary
   large blobs in CI.
4. Run metadata or header-level probes where feasible on a machine with the
   checkpoints available.
5. Compare public artifact layout to the vLLM-Omni/WebUI runtime assumptions.
6. Write public model setup notes for README and Docker sessions.
7. Open risk rows for any drift, missing model-card content, or unsupported mode.

## Out of Scope

- No model weights in Git.
- No automatic runtime download on API boot.
- No Docker changes.
- No public README rewrite yet.

## Deliverables

- HF verification note under `docs/session_4/`.
- Public model setup contract: repo IDs, expected local env vars, mount layout,
  and license notes.
- Drift report, if any.

## Deterministic Checks

```bash
rtk git ls-remote https://huggingface.co/wfen/Cosmos3-Nano-FP8-Blockwise HEAD 'refs/heads/*'
rtk git ls-remote https://huggingface.co/wfen/Cosmos3-Nano-NVFP4-Blockwise HEAD 'refs/heads/*'
rtk python - <<'PY'
from huggingface_hub import HfApi
for repo in ["wfen/Cosmos3-Nano-FP8-Blockwise", "wfen/Cosmos3-Nano-NVFP4-Blockwise"]:
    info = HfApi().model_info(repo)
    print(repo, info.sha, info.card_data)
PY
```

If `huggingface_hub` is unavailable, record the missing dependency as an
environment issue and use `git ls-remote` plus browser evidence.

## Exit Criteria

- `GATE-MIG-S4-HF` passes.
- FP8 and NVFP4 public artifact assumptions are documented.
- Any mismatch is routed before Docker or README relies on it.

## Handoff

Hand off model setup variables, mount expectations, license notes, and
compatibility caveats to `MIG-S6` and `MIG-S7`.

