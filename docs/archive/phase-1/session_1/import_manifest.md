# Session 1 Curated Import Manifest

Date: 2026-07-06
Session: MIG-S1

## Purpose

This manifest tells `MIG-S3` what may be imported into the public repo. It does not import source during `MIG-S1`.

The rule is curated import, not mirroring. Every imported file must have a public-beta purpose and must pass private-reference and artifact scans before commit.

## Allowed Import Categories

| Category | Owner Session | Allowed Content | Required Proof |
|---|---|---|---|
| API source | MIG-S3 | Runtime API code needed for public beta routes and CPU-safe tests. | File is needed for API runtime or tests; no private defaults; no model weights; no generated media. |
| WebUI source | MIG-S3 | Frontend source needed for the public beta UI and tests. | File is needed for UI runtime or tests; no private hosts; no local-only artifact paths; no checked-in build output. |
| Schemas | MIG-S3, MIG-S5 | OpenAPI, request/response schemas, and generated schema inputs needed by tests. | Schema source is public-safe; generated outputs have a deterministic source and sync check. |
| Tests | MIG-S3, MIG-S5 | CPU-only unit, lint, typecheck, and stub tests that do not require CUDA or model weights. | Test can run from public inputs; fixtures are small and public-safe; failures can be classified deterministically. |
| Tools | MIG-S3, MIG-S5 | Developer tools needed for scrub, schema sync, local checks, or public setup. | Tool does not require private network access; tool has a clear public migration purpose. |
| Non-Docker deploy support | MIG-S3 | Public-safe config templates and local launch helpers that do not build images. | Paths are configurable; examples use placeholders or repo-relative paths. |
| Docker and Compose support | MIG-S6 | Dockerfiles, Compose files, and env examples. | Import or edit only in `MIG-S6`; files use external checkpoint mounts and pinned public vLLM-Omni input. |
| Project hygiene | MIG-S7 | `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, issue templates, release checklist. | Files match public beta scope and license boundaries. |
| Fresh public docs | MIG-S7, MIG-S8 | README, setup docs, limitation docs, release notes. | Claims map to public evidence rows or release gates. |

## File-Level Import Checklist

For every candidate file, the importing session must record:

1. Category from the allowed import table.
2. Why the file is needed for public beta.
3. Whether the file is source, config, schema, test, fixture, tool, docs, or generated output.
4. Whether the file requires CUDA, model weights, private network access, or external services.
5. Scrub scan result for private references.
6. Artifact scan result for model weights, generated media, caches, and archives.
7. Dependency impact, if any.
8. Owner decision or contract amendment, if the file falls outside the allowed categories.

## Import Rules

- Import the smallest public-safe file set that supports the session goal.
- Prefer source and deterministic config over generated output.
- Keep checkpoint locations configurable through environment variables or documented mounts.
- Use placeholders such as `/path/to/Cosmos3-Nano-FP8-Blockwise` only for examples.
- Do not preserve compatibility layers just to support legacy private layouts.
- Do not cite private source paths or private evidence in public docs.
- Do not change public API behavior unless the active session contract allows it.

## Stop Conditions

The importing session must stop and classify the issue before commit when any of these occur:

- A candidate file contains a real private path, private host, private codename, credential, or secret assignment.
- A candidate file is a model weight, generated video, generated image, archive, cache, or bulky evidence artifact.
- A candidate file belongs to a legacy plain vLLM or TensorRT-LLM submodule.
- A candidate file requires Docker, workflow, dependency, or README changes outside the active session contract.
- A candidate file needs a production dependency that the user has not approved.
- A candidate file changes public API behavior without a contract clause and tests.

## Required Checks For Import Sessions

`MIG-S3` must run at least:

```bash
rtk rg --files
rtk rg -n "$PRIVATE_REF_PATTERN" .
rtk rg -n "submodules/(vllm|TensorRT-LLM)|TensorRT-LLM" .
rtk sh -lc 'rg --files | rg -n "\.(safetensors|pt|pth|ckpt|mp4|mov|avi)$"'
```

If `$PRIVATE_REF_PATTERN` is unset, use the fallback command set in `docs/session_1/scrub_checklist.md`.

## Handoff To Later Sessions

- `MIG-S2` consumes the remote baseline and records the public vLLM-Omni pin.
- `MIG-S3` consumes this manifest for curated source import.
- `MIG-S4` verifies Hugging Face checkpoint metadata and compatibility.
- `MIG-S5` turns imported tests and schemas into CPU-only CI.
- `MIG-S6` handles Docker and Compose.
- `MIG-S7` handles README and project hygiene.
