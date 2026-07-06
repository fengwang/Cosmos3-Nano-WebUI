# Session 3 Private-Reference Scrub Report

Date: 2026-07-06
Session: MIG-S3

## Private-Reference Pattern (effective `$PRIVATE_REF_PATTERN` for MIG-S3)

`$PRIVATE_REF_PATTERN` was unset, so this session derived a concrete pattern from
the private source instead of the Session 1 baseline fallback alone:

```
10\.147\.[0-9.]+            # private intranet host (vLLM-Omni submodule)
/data/home_feng             # private home
/workspace/gitea            # private checkout root
\bgitea\b                   # private git host
cosmos3-nano-quantization   # sibling private repo
-wfen                       # private checkpoint variant suffix
Blockwise-dist              # private local distribution checkpoint suffix
submodules/(vllm|TensorRT-LLM) | TensorRT-LLM   # legacy submodule refs (contract scan)
hf_[A-Za-z0-9]{20,} | sk-[A-Za-z0-9_-]{20,} | BEGIN [A-Z ]*PRIVATE KEY   # secrets
```

Plus the Session 1 fallback (`/home/…`, `/Users/…`, `/mnt/…`, token/secret shapes).

## `/data/models` Decision (owner Q_A)

`/data/models` is **kept** as the documented public container-mount convention and
as the trust-boundary allowlist root in path-traversal tests. It is a generic
container mount, not a home dir or secret. Real checkpoint locations are operator
env inputs (`COSMOS3_MODEL_DIR`, `COSMOS3_BASE_ACTION_DIR`, `COSMOS3_BF16_BASE_DIR`,
`COSMOS3_DEVICE`, `COSMOS3_VLLM_BIN`, …). Only truly-private specifics were scrubbed.

## Matches Found And Dispositions

| File | Match | Disposition |
|---|---|---|
| `api/engines/vllm/reasoner_preflight.py` (×2) | `submodules/vllm/.../models/cosmos3.py` | reworded to "the vLLM Cosmos3 model definition" |
| `api/engines/vllm/reasoner_preflight.py` | ` ``-dist`` checkpoints` | reworded to "blockwise-quantized checkpoints" |
| `api/app/main.py` | default `…-FP8-Blockwise-dist` | -> `…-FP8-Blockwise` (public HF name) |
| `api/engines/diffusers_oracle/config.py` (×2) | `…-NVFP4-wfen` | -> `…-NVFP4-Blockwise` |
| `api/engines/diffusers_oracle/loader.py` | `NVFP4-wfen` / `FP8-wfen` layout | -> `-Blockwise` |
| `api/engines/diffusers_action/loader.py` (×3) | `*-wfen`, `…-NVFP4-wfen`, default `…-FP8-wfen` | -> `-Blockwise` |
| `api/engines/vllm/loader.py` | ` ``-dist`` checkpoint` | -> "quantized blockwise checkpoint" |
| `tools/checkpoint_prep/copy_shared.py` | `_BF16_BASE_REF = "/data/models/Cosmos3-Nano/"` | env-driven `COSMOS3_BF16_BASE_DIR` (same default; INV-4) |
| `pyproject.toml` | `cosmos3-nano-quantization base image` | -> "proven Cosmos3-Nano quantization base image" |
| `tests/test_action_loader_unit.py` | `…-NVFP4-wfen` input | -> `…-NVFP4-Blockwise` |
| `tests/api/test_reasoner_preflight_unit.py` | `submodules/vllm/.../models/cosmos3.py` | reworded to "the vLLM Cosmos3 model definition's" |
| `.gitmodules` (private host `10.147.19.203`) | — | not imported (dropped with `submodules/`) |

## Non-Blocking, Non-Sensitive Items (documented, not scrubbed)

- **Internal design-doc citations** (`Refs: docs/session_N/specs/*.md`,
  `design.md D-N`, `evidence_map INV-N`) in ~42 `api/` files and a few tests.
  These are code comments citing generic design-doc names; they are NOT hosts,
  secrets, machine paths, or codenames, and no contract scan (private-ref, legacy,
  artifact) matches them. They reference `docs/session_N` (same relative shape the
  public migration repo uses) and dangle harmlessly. Classified **non-sensitive
  cosmetic cruft**; cleanup deferred to MIG-S7 (README/docs polish). Recorded here
  so reviewers and the adversarial verifier see an explicit disposition.
- **`/data/models/Cosmos3-Nano[/transformer]`** literals — kept per Q_A (mount
  convention + public base name; no `-wfen`/`-dist`/home).

## Final Scans (all CLEAN)

Over `api webui schemas tests tools pyproject.toml uv.lock`:

- private-ref pattern (above): **no match**
- Session 1 fallback (homes/hosts/tokens): **no match**
- weight/media extensions `.(safetensors|pt|pth|ckpt|mp4|mov|avi)`: **no match**
- archives `.(zip|tar|tgz|7z|rar)`: **no match**
- caches/build (`__pycache__|.pytest_cache|node_modules|dist|build|.next|coverage`): **no match**
- legacy submodule (files + content) `submodules/(vllm|TensorRT-LLM)|TensorRT-LLM`: **no match**
- `.gitmodules`: **absent**

All release-blocking private-reference classes are clear.
