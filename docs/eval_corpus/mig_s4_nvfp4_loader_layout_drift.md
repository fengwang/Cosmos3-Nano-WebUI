# Eval Seed - MIG-S4 Public Checkpoint vs Loader Contract Drift

Session: MIG-S4
Caught by: deterministic probe (layout + recipe vs imported loader code); classified Failure Arbiter FA-2
Severity caught: High (would-be: a README/Docker claim that in-process generation works on the public checkpoints)

## Prompt Seed

The public checkpoints must be verified against the **actual imported loader code**, not
against an assumed layout. Two silent incompatibilities exist between the current public
artifacts and the in-process `diffusers_oracle`/`diffusers_action` engines
(`session_4_contract.yaml` adversarial case "HF repo exists but file layout does not match
loader expectations"):

- FP8: `quantization_config.json` `recipe` is `fp8_blockwise_mixed`, but
  `config.py:precision_from_quant_config` requires the exact string `recipe == "fp8"` →
  `verify_precision` raises `ValueError`.
- NVFP4: no `modelopt_state.pt` and no top-level `quantization_config.json`;
  `discover_transformer_dir` requires both → raises `FileNotFoundError`. NVFP4 ships a
  vLLM-Omni-native export (`nvfp4_blockwise_mixed_v1.json`) whose safetensors carry no
  `weight_quantizer` keys.

## Inputs

- The public manifests + `quantization_config.json` recipe (SHA-gated `local == public`).
- The imported loader contract: `discover_transformer_dir` (`loader.py:43-49`) and
  `precision_from_quant_config` (`config.py:41-47`).

## Expected Verifier Behavior

1. Evaluate `discover_transformer_dir`'s requirement (`*.safetensors` + `modelopt_state.pt`
   + `config.json`) over each public `transformer/` listing.
2. Read the public `quantization_config.json` `recipe` and apply the runtime rule
   (`startswith("nvfp4")` or exact `== "fp8"`, else raises).
3. Conclude the in-process oracle is **not loadable as-is** for either current public
   checkpoint; scope the impact (default engine is `vllm_omni`, a separate container loader);
   route to a drift row + the GPU/serving gates (`MIG-S6`/`MIG-S8`). Do NOT let a public doc
   claim in-process generation works on these artifacts without validation.
4. A green "self-contained + reachable" check is **not** sufficient; the recipe-string and
   sidecar contract must be checked against the loader code.

## Regression Command Shape

```bash
python3 docs/session_4/probes/verify_hf_checkpoints.py --check   # pure-core rules
python3 - <<'PY'
import json
c=json.load(open("/path/to/Cosmos3-Nano-FP8-Blockwise/quantization_config.json"))
r=str(c.get("recipe",""))
assert not (r=="fp8" or r.startswith("nvfp4")), f"recipe {r!r} would pass exact-match; drift resolved?"
print("recipe", r, "-> in-process verify_precision raises (drift D1 present)")
PY
```
