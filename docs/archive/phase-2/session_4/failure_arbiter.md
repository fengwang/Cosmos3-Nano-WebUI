# Session 4 Failure Arbiter

## FA-1: System Python Pytest Missing `aenum`

- Command: `rtk python -m pytest -q tests/diffusion/quantization/test_fp8_blockwise_w8a16.py`
- Category: ENVIRONMENT
- Evidence: pytest failed before collecting the target test because `vllm_omni/patch.py` imports `aenum.extend_enum`, and system Python raised `ModuleNotFoundError: No module named 'aenum'`.
- Why BUG does not fit: no product code had been changed, and `requirements/common.txt` already lists `aenum==3.1.16`.
- Why SPEC_GAP does not fit: the contract allows external fork targeted checks but does not require the system Python environment.
- Why AMBIGUITY does not fit: the failure is a missing installed dependency, not multiple valid interpretations.
- Why TEST_BUG does not fit: the test did not assert the wrong behavior; it did not reach the test module.
- Allowed next action: use the fork checkout's existing `.venv-mig-s2/bin/python`, which has `aenum` installed, for targeted pytest and compile checks.
- Forbidden next action: change product code or add a production dependency to this repository.

## FA-2: Review-Blocking Quant Config Wiring And FP8 Default Performance

- Trigger: sharded review after the first pushed branch commit `bb4e170c5ac40fdac630c8c2030216521b9cc297`.
- Category: BUG
- Evidence:
  - Correctness/architecture reviewers independently found that `ModelOptNativeFp8W8A16CheckpointAdapter` and `ModelOptNativeNvfp4CheckpointAdapter` could be selected by checkpoint sidecars, but the new resident quant configs were only defined and unit-tested in isolation; production model construction did not call `maybe_build_fp8_blockwise_w8a16_config` or `maybe_build_nvfp4_blockwise_config`.
  - Correctness review found `nvfp4_blockwise.is_target_prefix()` excluded `mlp_moe_gen` even though the NVFP4 adapter accepts and tests `mlp_moe_gen` as a quantized target family.
  - Performance review found FP8 W8A16 selected by default even though `Fp8BlockwiseW8A16LinearMethod.apply()` dequantizes the full resident weight every forward pass.
- Why BUG fits: the implementation violated the execution contract's ready-branch, registration-locality, dtype/shape, and performance review axes. The specs already required an isolated branch that compiles, is model-agnostic, and is ready for `GPU-S5`; a branch that can route packed tensors into unconfigured modules is not ready.
- Why SPEC_GAP does not fit: no missing behavior needed to be invented. The correct behavior was implied by the existing helper names/tests and the review axes: adapter selection and quant-config selection must agree, and expensive resident FP8 dequant must be gated.
- Why AMBIGUITY does not fit: multiple reviewers found the same production wiring gap with concrete file/line evidence.
- Why ENVIRONMENT does not fit: the failures reproduced deterministically in CPU tests.
- Why TEST_BUG does not fit: new red tests matched the branch's intended behavior and reviewer evidence:
  - NVFP4 `mlp_moe_gen` target inclusion.
  - `TransformerConfig.from_dict({"quant_recipe": "nvfp4_blockwise_mixed_v1"})` builds the W4A16 config.
  - FP8 W8A16 is explicit opt-in via `VLLM_OMNI_FP8_BLOCKWISE_W8A16=1`.
  - `OmniDiffusionConfig(model=<fp8 root>)` wires the FP8 W8A16 config only when the opt-in and root recipe both match.
- Fix applied:
  - Wire NVFP4 top-level `quant_recipe` resolution through `TransformerConfig.from_dict`.
  - Wire FP8 root-sidecar W8A16 opt-in through `OmniDiffusionConfig` and its structured config mirror.
  - Include `mlp_moe_gen` in NVFP4 target-inclusion selection.
  - Change FP8 W8A16 from default to explicit opt-in; load-time dequant is the default.
- Re-check:
  - Red run before fix: 8 expected failures in the new/updated regression tests.
  - Green targeted set after fix: 128 passed, 18 warnings.
  - `python -m compileall vllm_omni`: PASS.
  - Unmasked forbidden-scope sweep: PASS, zero matches.

## FA-3: Main Repo Private-Reference Scan Found Local Workspace Paths

- Command: `rtk make scan`
- Category: BUG
- Evidence: `make scan` failed with 33 private-reference findings in `docs/session_4/**`, all local checkout paths such as `<external-vllm-omni-checkout>` and `<webui-repo>`.
- Why BUG fits: the project evidence-map rules and repository expectations require public docs not to cite private absolute paths. The session docs violated that rule.
- Why SPEC_GAP does not fit: the rule is explicit in `docs/evidence_map.md` and enforced by `make scan`.
- Why AMBIGUITY does not fit: the scanner identified exact offending strings.
- Why ENVIRONMENT does not fit: the scan is deterministic and repo-local.
- Why TEST_BUG does not fit: the scanner correctly caught public-doc leakage.
- Fix applied: mechanically rewrote session documentation to use `<external-vllm-omni-checkout>` and `<webui-repo>` placeholders instead of local absolute paths.
- Re-check: `rtk make scan` passed with `PRIVATE-REF SCAN: clean (0 findings)`.
