# Eval Seed - MIG-S2 NVFP4 Sidecar Preflight

Session: MIG-S2
Caught by: sharded review
Severity caught: High

## Prompt Seed

When ModelOpt-native checkpoint adapters are introduced, verify that every
adapter family with a sidecar validator is called before weight-file discovery.

## Inputs

- `vllm_omni/diffusion/model_loader/diffusers_loader.py`
- `vllm_omni/diffusion/model_loader/checkpoint_adapters/**`
- Session adapter specs

## Expected Verifier Behavior

The verifier MUST fail if the loader preflights only one ModelOpt-native sidecar
family while another registered native adapter exposes `validate_source_sidecar`.
Malformed sidecars must raise before `_prepare_weights` or equivalent
weight-discovery code runs.

## Regression Test Shape

```bash
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_diffusers_loader.py::test_get_weights_iterator_validates_nvfp4_sidecar_before_weight_discovery
```

## Expected Result

The test passes. If it fails, classify as BUG against the Session 2 requirement
"Sidecar validation fails before weight-file discovery" and wire the missing
preflight before discovering weights.
