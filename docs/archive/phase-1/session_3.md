# Session 3 - Curated WebUI/API Source Import and Scrub

Contract: `docs/session_3_contract.yaml`
Risk: high
Routing: worker_plus_reviewers

## Objective

Import the public beta source tree in curated form: API, WebUI, schemas, tests,
tools, and selected deploy support, while removing private references, unsupported
legacy submodules, bulky artifacts, and local-only files.

## Why This Session Exists

The public repo needs real source before CI, Docker, or README work can be
verified. A direct mirror is too risky because it may include private paths,
archives, large evidence outputs, or unsupported dependency surfaces.

## In Scope

1. Copy selected API source, WebUI source, schemas, tests, tools, and non-Docker
   deploy support according to the `MIG-S1` manifest.
2. Exclude legacy plain vLLM and TensorRT-LLM submodules and unsupported code
   unless a public runtime dependency is proven.
3. Replace private path defaults with environment variables or placeholders.
4. Remove private codenames and private host references.
5. Ensure no weights, generated media, caches, or bulky evidence are imported.
6. Run source-level smoke checks that do not require CUDA or model weights.
7. Update evidence and risk rows for import results.

## Out of Scope

- No vLLM-Omni fork edits.
- No HF checkpoint deep validation.
- No GitHub Actions workflow finalization.
- No README rewrite.
- No Docker runtime validation.

## Deliverables

- Curated source import in the public repo.
- Import manifest with included and excluded paths.
- Private-reference scrub report.
- Source smoke check evidence.

## Deterministic Checks

```bash
rtk rg --files
rtk rg -n "$PRIVATE_REF_PATTERN" .
rtk rg -n "submodules/(vllm|TensorRT-LLM)|TensorRT-LLM"
rtk rg -n "\\.(safetensors|pt|pth|ckpt|mp4|mov|avi)$"
rtk python -m compileall api || true
```

## Exit Criteria

- `GATE-MIG-S3-IMPORT` passes.
- Public source tree is present and scrubbed.
- Unsupported legacy submodule dependencies are absent or explicitly blocked.
- Later CI and Docker sessions can run from public files only.

## Handoff

Hand off the imported tree summary, scrub report, excluded-path list, and any
source gaps to `MIG-S4` and `MIG-S5`.
