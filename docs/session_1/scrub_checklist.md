# Session 1 Scrub Checklist

Date: 2026-07-06
Session: MIG-S1

## Purpose

This checklist gives later sessions a repeatable way to find private references, secrets, model weights, generated media, local-only artifacts, and unsupported legacy submodules.

The contract command is:

```bash
rtk rg -n "$PRIVATE_REF_PATTERN" .
```

Because `$PRIVATE_REF_PATTERN` is unset in the current shell, this checklist defines a fallback pattern and command set.

## Pattern Groups

### Private Absolute Paths

Signals:

- real user home directories
- machine-local mount paths
- private storage roots
- private checkpoint roots

Allowed placeholder examples:

```text
/path/to/Cosmos3-Nano-FP8-Blockwise
/path/to/Cosmos3-Nano-NVFP4-Blockwise
```

### Private Hosts And Codenames

Signals:

- private hostnames
- internal-only repo names
- unpublished project codenames
- private lab, cluster, or storage names

Session 1 does not know the private names. Later sessions must extend `$PRIVATE_REF_PATTERN` when they know specific names.

### Secrets And Credentials

Signals:

- private key headers
- Hugging Face token-like strings
- OpenAI-style secret-key strings
- assignments to credential-like names
- env files with real values

Redacted examples are allowed. Real values are release-blocking.

### Model Weights And Generated Media

Signals:

- `.safetensors`
- `.pt`
- `.pth`
- `.ckpt`
- `.mp4`
- `.mov`
- `.avi`
- checkpoint, weight, artifact, output, or generated sample folders

### Legacy Submodules

Signals:

- `submodules/vllm`
- `TensorRT-LLM`
- vendored copies of legacy plain vLLM or TensorRT-LLM

## Fallback Private-Reference Scan

Use this when `$PRIVATE_REF_PATTERN` is unset:

```bash
rtk sh -lc 'PRIVATE_REF_PATTERN="(/home/[A-Za-z0-9._-]+|/Users/[A-Za-z0-9._-]+|/mnt/[^[:space:]]+|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY|([A-Za-z0-9_]*token|secret|password|api[_-]?key)[[:space:]]*[:=])"; rg -n -i "$PRIVATE_REF_PATTERN" . --glob "!docs/session_1/**"'
```

Expected baseline result for the current repo: no matches, exit `1`.

If this command finds matches in imported source, config, tests, tools, deploy files, workflows, or README content, classify before fixing and block the commit until the match is removed or explicitly allowed by contract.

## Contract Pattern Scan

Use this when `$PRIVATE_REF_PATTERN` is set by the operator:

```bash
rtk rg -n "$PRIVATE_REF_PATTERN" .
```

Expected result: no release-blocking matches.

If matches appear only inside Session 1 pattern documentation, classify them as documentation examples. If matches appear in runtime, config, workflow, README, or imported docs, classify before fixing.

## Artifact And Weight Scans

Whole-repo baseline scan excluding Session 1 documentation examples:

```bash
rtk sh -lc 'rg --files | rg -n "\.(safetensors|pt|pth|ckpt|mp4|mov|avi)$"'
rtk sh -lc 'rg --files | rg -n "(^|/)(checkpoints|weights|artifacts|outputs|samples/generated)(/|$)"'
```

Expected baseline result for the current repo: no matches, exit `1`.

Candidate import scan:

```bash
rtk sh -lc 'rg --files path/from/import | rg -n "\.(safetensors|pt|pth|ckpt|mp4|mov|avi)$"'
rtk sh -lc 'rg --files path/from/import | rg -n "(^|/)(checkpoints|weights|artifacts|outputs|samples/generated)(/|$)"'
```

Expected candidate result: no matches unless the active session contract explicitly allows a tiny public fixture.

## Archive And Cache Scans

Whole-repo baseline scan excluding Session 1 documentation examples:

```bash
rtk sh -lc 'rg --files | rg -n "\.(zip|tar|tar\.gz|tgz|7z|rar)$"'
rtk sh -lc 'rg --files | rg -n "(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|node_modules|dist|build|\.next|coverage)(/|$)"'
```

Expected baseline result for the current repo: no matches, exit `1`.

## Legacy Submodule Scan

Whole-repo baseline scan excluding documentation examples:

```bash
rtk sh -lc 'rg --files | rg -n "(^|/)submodules/(vllm|TensorRT-LLM)(/|$)|(^|/)TensorRT-LLM(/|$)"'
```

Expected baseline result for the current repo: no matches, exit `1`.

Candidate import scan:

```bash
rtk sh -lc 'rg --files path/from/import | rg -n "(^|/)submodules/(vllm|TensorRT-LLM)(/|$)|(^|/)TensorRT-LLM(/|$)"'
```

Expected candidate result: no matches unless a later session records a public runtime need and contract amendment.

## Result Classification

| Result | Classification | Action |
|---|---|---|
| No matches | PASS | Continue. |
| Match in Session 1 scan docs only | PASS with note | Record as documentation example if needed. |
| Match in allowed placeholder path | PASS with note | Confirm it is not a real path. |
| Match in imported source, config, workflow, README, or runtime docs | BUG or SPEC_GAP | Classify before editing; remove or amend contract. |
| Scan command fails because variable is unset | ENVIRONMENT | Use fallback command. |
| Scan command matches its own regex example | TEST_BUG | Rewrite the check to avoid self-match or exclude scan docs. |
| Match requires a product decision | AMBIGUITY | Stop and choose one explicit interpretation before editing. |

## Release-Blocking Matches

The following matches block the active session until classified and fixed or explicitly approved:

- real private absolute paths
- private hosts
- private codenames
- real credentials or secret assignments
- model weights
- generated media
- caches
- archives
- bulky evidence
- legacy submodules
- Docker image publishing credentials or workflows in milestone 1

## Baseline Result From Session 1

At checklist creation time:

- `$PRIVATE_REF_PATTERN` was unset, classified as `ENVIRONMENT`.
- The fallback private-reference scan excluding Session 1 docs found no matches.
- The model weight and generated media scan excluding Session 1 docs found no matches.
- The archive and cache path scans found no matches.
- The legacy submodule scan excluding docs found no matches.

The exact command output is recorded by the session transcript and summarized in `docs/session_1/inventory.md` and `docs/handoff.md`.
