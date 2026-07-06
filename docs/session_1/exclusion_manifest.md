# Session 1 Exclusion Manifest

Date: 2026-07-06
Session: MIG-S1

## Purpose

This manifest tells later sessions what must stay out of the public repo by default. A later session may only make an exception when its contract allows the file class and the owner approves the risk.

## Default Exclusions

| Exclusion Class | Examples Or Signals | Reason | Exception Rule |
|---|---|---|---|
| Model weights | `.safetensors`, `.pt`, `.pth`, `.ckpt`, checkpoint folders, weight shards | Weights stay external on Hugging Face or operator mounts. | No exception in milestone 1 without owner approval and contract amendment. |
| Generated media | `.mp4`, `.mov`, `.avi`, generated images, generated audio, sample output folders | Generated artifacts are bulky and not source. | Use tiny public fixtures only if a later test contract allows them. |
| Archives | `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.7z`, `.rar` | Archives hide content from normal review and scans. | Extract and curate needed files instead. |
| Caches | `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.cache`, package caches | Rebuildable local state. | No exception. |
| Frontend build output | `node_modules`, `dist`, `build`, `.next`, coverage output | Rebuildable generated state or dependency cache. | No exception for milestone 1. |
| Bulky evidence | benchmark dumps, profiling output, raw logs, private evidence folders | Public docs must cite public evidence only and keep repo small. | Summarize public evidence in docs instead. |
| Temporary folders | scratch folders, local experiment outputs, editor backup files | Local-only state. | No exception. |
| Private evidence | private repo paths, private host captures, internal screenshots, unpublished patch archives | Public docs cannot cite or ship private evidence. | No exception. |
| Secrets and credentials | key files, credential stores, token assignments, private keys, env files with real values | Security risk. | Use redacted examples only. |
| Legacy plain vLLM submodule | `submodules/vllm`, vendored plain vLLM copies | First milestone uses a pinned public vLLM-Omni fork instead. | Stop for contract decision if runtime import proves a need. |
| TensorRT-LLM submodule | `TensorRT-LLM`, vendored TensorRT-LLM copies | Out of first milestone unless a public runtime dependency is proven. | Stop for contract decision if runtime import proves a need. |
| Private-path config | Defaults pointing to a real user home, lab mount, private storage, or machine path | Public setup must work without private local state. | Replace with environment variables or placeholders. |
| Docker image publishing state | Registry credentials, publish workflows, GHCR release config | First milestone is local-build only. | Defer to a later contract. |

## Extension Blocklist

Future sessions must treat these extensions as excluded by default:

```text
.safetensors
.pt
.pth
.ckpt
.mp4
.mov
.avi
.zip
.tar
.tar.gz
.tgz
.7z
.rar
```

## Path Fragment Blocklist

Future sessions must treat these path fragments as excluded by default:

```text
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
.cache
node_modules
dist
build
.next
coverage
checkpoints
weights
artifacts
outputs
samples/generated
submodules/vllm
TensorRT-LLM
```

## Allowed Placeholders

These placeholder forms are allowed in docs and examples:

```text
/path/to/Cosmos3-Nano-FP8-Blockwise
/path/to/Cosmos3-Nano-NVFP4-Blockwise
COSMOS3_FP8_MODEL_DIR
COSMOS3_NVFP4_MODEL_DIR
```

Allowed placeholders must not point to a real private machine path.

## Stop Conditions

Stop before commit when:

- A scan finds a blocked extension or path fragment in a candidate import.
- A file is needed but belongs to an excluded class.
- A file appears to be small but contains hidden binary or archive content.
- A file references a real private path, private host, credential, or secret assignment.
- A legacy submodule appears required for runtime.

The worker must classify the failure as `BUG`, `SPEC_GAP`, `AMBIGUITY`, `ENVIRONMENT`, or `TEST_BUG` before editing product files.

## Required Exclusion Scans

```bash
rtk sh -lc 'rg --files | rg -n "\.(safetensors|pt|pth|ckpt|mp4|mov|avi)$"'
rtk sh -lc 'rg --files | rg -n "\.(zip|tar|tar\.gz|tgz|7z|rar)$"'
rtk sh -lc 'rg --files | rg -n "(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|node_modules|dist|build|\.next|coverage)(/|$)"'
rtk sh -lc 'rg --files | rg -n "(^|/)(checkpoints|weights|artifacts|outputs|samples/generated)(/|$)"'
rtk sh -lc 'rg --files | rg -n "(^|/)submodules/(vllm|TensorRT-LLM)(/|$)|(^|/)TensorRT-LLM(/|$)"'
```

Matches inside this Session 1 documentation are examples. Matches in candidate import files are release-blocking until classified and removed or explicitly approved by a later contract.
