# Eval Seed - MIG-S6 A Build Variant Claims a Dependency Its Extra Doesn't Provide

Session: MIG-S6
Caught by: sharded review (architecture axis)
Severity caught: High (build succeeds but the capability it exists for is missing)

## Prompt Seed

A Dockerfile build variant (`--build-arg WITH_REASONING=1`) claimed in its comment/spec to
"install the vLLM reasoning stack," but its install was `uv sync --extra oracle`, and the
`oracle` extra (and `uv.lock`) contain **no `vllm`** — the reasoner needs `from vllm import
LLM` and a `vllm serve` subprocess. The image would build cleanly yet be unable to reason:
the classic "build succeeds, required dependency absent" trap, masked until GPU runtime
(where it would look like a runtime bug, not a packaging bug).

## Inputs

- `deploy/api.Dockerfile` (`WITH_REASONING` branch), `pyproject.toml` (`oracle` extra),
  `uv.lock`
- `api/engines/vllm/loader.py` (`from vllm import LLM`), `api/orchestrator/planes.py`
  (`vllm serve` via `COSMOS3_VLLM_BIN`)

## Expected Verifier Behavior

1. Grep the resolved dependency set the build installs for the claimed component:
   `grep -c vllm pyproject.toml uv.lock` → 0 while the code imports `vllm`.
2. Conclude the build target does not deliver the capability it advertises.
3. Fix by either installing the dep (here: add `uv pip install vllm==0.23.0` — the pin the
   code references — in the reasoning branch; it is not in `uv.lock`, so it is a build-time
   install) OR correcting the claim to say the dep is not installed. Do NOT leave the
   comment/spec asserting a capability the build omits.
4. Mark GPU build + torch/vLLM/CUDA compatibility as the deferred (S8) validation.

## Regression Command Shape

```bash
# The advertised dependency must actually be in the install set for the variant:
grep -Eiq 'vllm' pyproject.toml uv.lock || grep -q 'pip install vllm' deploy/api.Dockerfile
```

## Expected Result

Every capability a build variant advertises is backed by an actual install line (locked or
explicit build-time), or the docs are corrected to not claim it.

## Promotion Target

- REVIEW.md / sharded-review (architecture) check: for any conditional build variant,
  verify the resolved dependency set contains what the variant's docs claim — "build
  succeeds" is not evidence the capability is present.
