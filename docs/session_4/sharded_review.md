# Session 4 Sharded Review

## Inputs

- Session contract: `docs/session_4_contract.yaml`
- Execution contract: `docs/session_4/execution_contract.md`
- Upstream finding: `docs/session_4/upstream_state.md`
- Branch notes/checks: `docs/session_4/branch_notes.md`, `docs/session_4/checks.md`
- External diff: `<external-vllm-omni-checkout>`, branch `gpu-s4-quant-loader-isolation` vs. `upstream/main`

## Summary

Result after fixes: PASS for `GPU-S4` scope. No Critical findings. High findings were concrete, fixed in external fork commit `f7e024ddc9965622ebcfdb919e8ccb46b4232074`, and rechecked with the targeted test set, `compileall`, rebase, and branch-diff scope sweep.

Deferred items are Medium/Low only and are handed to `GPU-S5` or later hardening.

## Deduplicated Findings

### F1: Resident Quant Configs Were Not Wired Into Production Construction

- Severity: High
- Axes: correctness, architecture/maintainability
- Evidence: `checkpoint_adapters/__init__.py` could route FP8 W8A16 and NVFP4 native adapters from sidecars, but production config construction did not call `maybe_build_fp8_blockwise_w8a16_config` or `maybe_build_nvfp4_blockwise_config`. Reviewers cited `vllm_omni/diffusion/data.py` and `vllm_omni/quantization/factory.py` as the existing config boundary.
- Violated contract clause: execution contract review axes for correctness, registration locality, and ready-branch done condition.
- Smallest safe fix: wire disk recipe resolution at the existing model config propagation boundary.
- Resolution: Fixed in `f7e024dd`.
  - `TransformerConfig.from_dict` resolves top-level NVFP4 `quant_recipe`.
  - `OmniDiffusionConfig` and the structured config mirror resolve FP8 root-sidecar W8A16 only when explicitly opted in and recipe-matched.
  - Added regression tests for both routes.
- Re-check: targeted pytest set passed: 128 passed, 18 warnings.
- Confidence: High

### F2: NVFP4 Target Selection Excluded `mlp_moe_gen`

- Severity: High
- Axis: correctness
- Evidence: `modelopt_native_nvfp4.py` accepts `mlp_moe_gen` target tensors and tests include `layers.0.mlp_moe_gen.down_proj.weight`, but `nvfp4_blockwise.py` initially matched only `.mlp.{gate,up,down}_proj`.
- Violated contract clause: execution contract review axis for dtype/shape behavior and adapter/loader correctness.
- Smallest safe fix: include `mlp_moe_gen` in the config target predicate and test it.
- Resolution: Fixed in `f7e024dd`.
- Re-check: targeted pytest set passed: 128 passed, 18 warnings.
- Confidence: High

### F3: FP8 W8A16 Hot-Path Full-Weight Dequant Was Default

- Severity: High
- Axis: performance
- Evidence: `Fp8BlockwiseW8A16LinearMethod.apply()` dequantizes resident FP8 weights every forward; the first branch made W8A16 default for matching FP8 sidecars.
- Violated contract clause: execution contract performance axis: no avoidable hot-path dequant and expensive behavior must be gated.
- Smallest safe fix: keep load-time dequant as default and make W8A16 explicit opt-in until a fused or cached path exists.
- Resolution: Fixed in `f7e024dd`.
  - Default adapter path is dequant-on-load.
  - Resident W8A16 requires `VLLM_OMNI_FP8_BLOCKWISE_W8A16=1` plus root recipe match.
- Re-check: targeted pytest set passed: 128 passed, 18 warnings.
- Confidence: High

### F4: Closeout Evidence Was Incomplete During Review

- Severity: High during review; resolved by closeout
- Axis: tests/evidence
- Evidence: at review time, tasks still had publication/review/verifier/handoff unchecked and `docs/evidence_map.md` still had the upstream claim as speculative.
- Violated contract clause: execution contract done condition requires saved sharded review, adversarial verification, and handoff.
- Smallest safe fix: complete closeout artifacts and final evidence.
- Resolution: In progress at review time; this report, updated checks, later adversarial verification, and handoff close the finding.
- Confidence: High

### F5: Scope Sweep Evidence Masked `rg` Exit Status

- Severity: Low
- Axis: tests/evidence
- Evidence: the first checks artifact recorded `rg ... || true`, which hides whether `rg` failed or simply found no matches.
- Violated contract clause: project verification policy prefers deterministic evidence.
- Smallest safe fix: supplement with an unmasked wrapper that treats `rg` exit 1 as expected zero matches and any other nonzero as error.
- Resolution: Fixed in documentation and re-run. Result: `PASS: zero forbidden matches`.
- Confidence: Medium

### F6: Local `upstream` Push URL Is Not Disabled

- Severity: Low
- Axis: security/safety
- Evidence: local `git remote get-url --push upstream` returns `https://github.com/vllm-project/vllm-omni.git`.
- Violated contract clause: no branch-diff violation; weakens the forbidden direct-upstream-write boundary.
- Smallest safe fix: optionally set local `remote.upstream.pushurl` to an inert value.
- Resolution: Deferred. This session pushed only to `origin`; no upstream direct write occurred.
- Confidence: High

### F7: NVFP4 Sidecar Patterns Are Raw Regexes

- Severity: Low
- Axis: security/safety
- Evidence: `modelopt_native_nvfp4.py` accepts `target_patterns` / `forbidden_patterns` from sidecar JSON and evaluates them with `re.search`.
- Violated contract clause: no explicit contract violation; hardening issue for malformed/untrusted sidecars.
- Smallest safe fix: validate/compile sidecar patterns at parse time or replace regexes with literal/glob matching.
- Resolution: Deferred to `GPU-S5` or later hardening; not High/Critical.
- Confidence: Medium

### F8: Loader/Quantization Bidirectional Coupling

- Severity: Medium
- Axis: architecture/maintainability
- Evidence: checkpoint dispatch imports FP8 selection from quantization, while the FP8 quantization module imports adapter constants/helpers.
- Violated contract clause: review axis for ACD separation and registration locality.
- Smallest safe fix: move shared constants and pure helpers into a common module.
- Resolution: Deferred. The High correctness issue was fixed without broad refactor.
- Confidence: High

### F9: FP8 W8A16 Docstring Uses A Fixed Target Count

- Severity: Low
- Axis: architecture/maintainability
- Evidence: `modelopt_native_fp8_w8a16.py` mentions "216" resident targets.
- Violated contract clause: model-agnostic contribution style.
- Smallest safe fix: remove the fixed count or describe it as artifact-specific, not a general format invariant.
- Resolution: Deferred; not High/Critical.
- Confidence: Medium

### F10: Eager Imports In Checkpoint Adapter Package

- Severity: Low
- Axis: performance
- Evidence: checkpoint adapter `__init__.py` imports new native adapters and FP8 W8A16 selection at import time.
- Violated contract clause: performance axis for import side effects.
- Smallest safe fix: lazy-import native adapters inside the `use_safetensors` branch.
- Resolution: Deferred; not High/Critical.
- Confidence: Medium

## Final Review Decision

High findings are fixed and rechecked. Medium/Low findings are documented as residual risks for `GPU-S5` review/precheck and do not block `GATE-GPU-S4-UPSTREAM-SCOPE`.
