# Session 2 Failure Arbiter

Date: 2026-07-06
Session: MIG-S2

## Baseline Classification 1 - WebUI repo compileall lacks fork source

Failing command:

```bash
rtk python -m compileall vllm_omni
```

Output:

```text
Listing 'vllm_omni'...
Can't list 'vllm_omni'
```

Category: ENVIRONMENT

Evidence:

- The WebUI seed repo does not contain `vllm_omni`.
- Session 2 contract scopes fork source checks to the external vLLM-Omni fork
  repository.
- The same command run from `vllm-omni` passed at baseline.

Why other categories do not fit:

- BUG: no WebUI source is expected to provide `vllm_omni`.
- SPEC_GAP: the session plan states exact test paths may change with the fork and
  the contract blast radius names an external fork repository.
- AMBIGUITY: the intended fork checkout is now explicit in the execution contract.
- TEST_BUG: the command is valid, just run from the wrong tree for this source.

Allowed next action:

- Run fork source checks from `vllm-omni`.

Forbidden next action:

- Add or vendor `vllm_omni` into the WebUI repo.

## Baseline Classification 2 - WebUI repo targeted pytest lacks fork tests

Failing command:

```bash
rtk pytest -q tests/diffusion/model_loader/test_modelopt_native.py tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py tests/diffusion/model_loader/test_modelopt_native_nvfp4.py tests/diffusion/models/cosmos3/test_cosmos3_nvfp4_load_guard.py tests/diffusion/quantization/test_fp8_blockwise_w8a16.py tests/diffusion/quantization/test_nvfp4_blockwise_config.py
```

Output:

```text
no tests ran in 0.00s
```

Category: ENVIRONMENT

Evidence:

- The WebUI seed repo has no fork test tree.
- Session 2 deterministic tests belong to the external vLLM-Omni fork checkout.

Why other categories do not fit:

- BUG: no WebUI runtime source was expected at this point.
- SPEC_GAP: the external fork target is identified by the contract.
- AMBIGUITY: the execution contract fixes the checkout path for fork tests.
- TEST_BUG: the command is contract-specified, but the invocation tree was not
  the fork checkout.

Allowed next action:

- Run targeted pytest from `vllm-omni` after patch import.

Forbidden next action:

- Create placeholder WebUI tests to satisfy this command.

## Baseline Classification 3 - Fork pytest blocked by missing aenum

Failing command:

```bash
rtk proxy pytest -q tests/diffusion/model_loader/test_modelopt_native.py tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py tests/diffusion/model_loader/test_modelopt_native_nvfp4.py tests/diffusion/models/cosmos3/test_cosmos3_nvfp4_load_guard.py tests/diffusion/quantization/test_fp8_blockwise_w8a16.py tests/diffusion/quantization/test_nvfp4_blockwise_config.py
```

Output excerpt:

```text
ImportError: Error importing plugin "tests.helpers.fixtures.config": No module named 'aenum'
```

Category: ENVIRONMENT

Evidence:

- `vllm_omni/patch.py` imports `aenum`.
- `vllm-omni/requirements/common.txt` declares
  `aenum==3.1.16`.
- The global Python environment does not have that dependency installed.

Why other categories do not fit:

- BUG: the dependency is declared by the fork.
- SPEC_GAP: the contract requires deterministic tests but does not mandate the
  global Python environment.
- AMBIGUITY: owner selected an isolated venv for Session 2 checks.
- TEST_BUG: pytest did not collect tests because the environment is incomplete.

Allowed next action:

- Create/use `.venv-mig-s2` and install declared practical test dependencies.

Forbidden next action:

- Patch source code to remove the `aenum` import solely to satisfy the global
  environment.

## Baseline Classification 4 - Contract NVFP4 config test path is stale

Failing or unavailable target:

```text
tests/diffusion/quantization/test_nvfp4_blockwise_config.py
```

Category: AMBIGUITY

Evidence:

- The Session 2 YAML deterministic check names
  `tests/diffusion/quantization/test_nvfp4_blockwise_config.py`.
- The approved patch source contains
  `tests/model_executor/quantization/test_nvfp4_blockwise_config.py`.
- `docs/session_2.md` states that exact test paths may change with the fork and
  skipped or unavailable checks must be recorded explicitly.

Why other categories do not fit:

- BUG: no source behavior has failed.
- SPEC_GAP: the session plan anticipated path changes, but the YAML concrete path
  needs interpretation.
- ENVIRONMENT: this is a path/taxonomy issue, not missing runtime dependency.
- TEST_BUG: the test content is not known to contradict the contract.

Allowed next action:

- Prefer the actual rebased patch test path and record the substitution in
  execution evidence. If preserving the contract path is simpler and cleaner
  after rebase, move or duplicate the test only with review justification.

Forbidden next action:

- Silently skip the NVFP4 config test.

## Baseline Classification 5 - Fork pytest blocked by missing vllm package

Failing command:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_modelopt_native.py
```

Output excerpt:

```text
ImportError: Error importing plugin "tests.helpers.fixtures.config": No module named 'vllm'
```

Category: ENVIRONMENT

Evidence:

- `vllm_omni/model_executor/models/registry.py` imports from
  `vllm.model_executor.models.registry`.
- The Session 2 venv has the fork's common dependencies but no `vllm` package.
- PyPI lists public `vllm` version `0.24.0`, matching the current vLLM-Omni fork
  release line.

Why other categories do not fit:

- BUG: the fork is expected to run with a base `vllm` installation.
- SPEC_GAP: deterministic checks require the fork runtime dependencies, and a
  missing package is an environment setup issue.
- AMBIGUITY: the missing module is named directly in the traceback.
- TEST_BUG: pytest fails during plugin import before any target test logic runs.

Allowed next action:

- Install `vllm==0.24.0` into `.venv-mig-s2` and retry collection.

Forbidden next action:

- Patch product imports to avoid `vllm` solely for the Session 2 test
  environment.

## Baseline Classification 6 - vllm no-deps install is incomplete

Failing commands:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_modelopt_native.py
rtk .venv-mig-s2/bin/python -m pip check
```

Output excerpts:

```text
No module named 'cbor2'
vllm 0.24.0 requires cbor2, which is not installed.
vllm 0.24.0 has requirement torch==2.11.0, but you have torch 2.12.1.
```

Category: ENVIRONMENT

Evidence:

- `vllm==0.24.0` was installed with `--no-deps` as a minimal environment probe.
- `pip check` reports missing transitive dependencies and a torch ABI mismatch.
- Importing `vllm` emits a compiled extension warning consistent with the torch
  mismatch.

Why other categories do not fit:

- BUG: the fork source has not changed and the failure is dependency resolution.
- SPEC_GAP: the session permits environment-sensitive test failures to be
  classified; the next action is still environment setup.
- AMBIGUITY: `pip check` names the missing and mismatched packages directly.
- TEST_BUG: pytest fails during dependency import before test execution.

Allowed next action:

- Let pip install the full public `vllm==0.24.0` dependency set into
  `.venv-mig-s2`, then rerun import and targeted collection.

Forbidden next action:

- Patch tests or product code to hide missing transitive dependencies.

## Baseline Classification 7 - pytest asyncio plugin missing

Failing command:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_modelopt_native.py
```

Output excerpt:

```text
ERROR: Unknown config option: asyncio_mode
```

Category: ENVIRONMENT

Evidence:

- The fork pytest configuration uses `asyncio_mode`.
- `pyproject.toml` lists `pytest-asyncio` under the `dev` optional dependency
  group.
- The Session 2 venv installed pytest but not the dev pytest plugin set.

Why other categories do not fit:

- BUG: source behavior was not executed.
- SPEC_GAP: the fork declares the plugin in its dev dependency list.
- AMBIGUITY: pytest names the missing config handler directly.
- TEST_BUG: the config is valid when the declared plugin is installed.

Allowed next action:

- Install `pytest-asyncio` into `.venv-mig-s2` and rerun the first target.

Forbidden next action:

- Delete or ignore `asyncio_mode` from fork pytest configuration for this
  session.

## Red Check 1 - First ModelOpt-native adapter test is absent on public main

Failing command:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_modelopt_native.py
```

Output excerpt:

```text
ERROR: file or directory not found: tests/diffusion/model_loader/test_modelopt_native.py
```

Category: BUG

Evidence:

- `docs/session_2/specs/modelopt_checkpoint_adapters.md` requires
  ModelOpt-native adapter tests that do not require model weights.
- Public fork `main` does not contain the selected patch test file.
- The approved patch source range contains this test file.

Why other categories do not fit:

- SPEC_GAP: the requirement and expected first test are explicit.
- AMBIGUITY: the first test path is fixed in the execution contract.
- ENVIRONMENT: `pip check` passes and pytest is now collecting far enough to
  report the missing file.
- TEST_BUG: the test file is missing, not contradicting the contract.

Allowed next action:

- Replay the first selected patch commit that introduces
  `tests/diffusion/model_loader/test_modelopt_native.py` and matching adapter
  code.

Forbidden next action:

- Mark the adapter capability complete without importing or replacing the
  spec-derived test.

## Red Check 2 - NVFP4 adapter and load-guard tests are absent before NVFP4 patch

Failing commands:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_modelopt_native_nvfp4.py
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/models/cosmos3/test_cosmos3_nvfp4_load_guard.py
```

Output excerpt:

```text
ERROR: file or directory not found: tests/diffusion/model_loader/test_modelopt_native_nvfp4.py
ERROR: file or directory not found: tests/diffusion/models/cosmos3/test_cosmos3_nvfp4_load_guard.py
```

Category: BUG

Evidence:

- `docs/session_2/specs/cosmos3_quantization_runtime_guards.md` requires an
  explicit NVFP4 runtime guard.
- `docs/session_2/specs/modelopt_checkpoint_adapters.md` requires ModelOpt
  adapter coverage for NVFP4 layouts.
- The approved patch source contains both test files.

Why other categories do not fit:

- SPEC_GAP: the requirements and test names are explicit.
- AMBIGUITY: these two paths are listed in the execution contract.
- ENVIRONMENT: pytest is now configured and reports missing test files.
- TEST_BUG: the tests are absent rather than contradictory.

Allowed next action:

- Replay the selected NVFP4 commit introducing the tests and implementation.

Forbidden next action:

- Treat NVFP4 as covered by FP8 adapter tests alone.

## Red Check 3 - FP8 W8A16 adapter and quantization tests are absent before W8A16 patch

Failing commands:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/quantization/test_fp8_blockwise_w8a16.py
```

Output excerpt:

```text
ERROR: file or directory not found: tests/diffusion/model_loader/test_modelopt_native_fp8_w8a16.py
ERROR: file or directory not found: tests/diffusion/quantization/test_fp8_blockwise_w8a16.py
```

Category: BUG

Evidence:

- `docs/session_2/specs/cosmos3_quantization_runtime_guards.md` requires
  explicit FP8 W8A16 runtime behavior.
- The execution contract identifies these tests as the focused FP8 W8A16 checks.
- The approved patch source contains both test files.

Why other categories do not fit:

- SPEC_GAP: the requirement is explicit.
- AMBIGUITY: the test paths are listed in the execution contract.
- ENVIRONMENT: pytest can run and reports missing files.
- TEST_BUG: the tests are absent rather than invalid.

Allowed next action:

- Replay the selected FP8 W8A16 commits introducing the tests and implementation.

Forbidden next action:

- Mark FP8 W8A16 support complete without importing or replacing the
  spec-derived tests.

## Review Finding 1 - Session docs recorded private source details

Failing command:

```bash
rtk rg -n "<private absolute path pattern>|<private branch pattern>|<private source hash patterns>" docs/session_2 docs/handoff.md docs/evidence_map.md docs/risk_register.md
```

Output excerpt:

```text
docs/session_2/brainstorming.md: recorded the private source checkout path
docs/session_2/proposal.md: recorded the private source checkout path
docs/session_2/plan.md: recorded copy-pastable commands with the private source checkout path
```

Category: BUG

Evidence:

- `docs/project_contract.md` INV-1 forbids private absolute paths and
  local-only artifact references in public files.
- `docs/prd.md` FR-2/NFR-1 require public files to stay free of private hosts,
  private absolute paths, and local-only artifact references.
- Session 2 planning docs are committed public docs, not private scratch files.

Why other categories do not fit:

- SPEC_GAP: the PRD and project contract define the rule directly.
- AMBIGUITY: a real local source checkout path is unambiguously private/public-unsafe.
- ENVIRONMENT: the failure is deterministic text content, not tool setup.
- TEST_BUG: the scan matches actual public-doc content.

Allowed next action:

- Replace private source path, branch, and source-hash details with local-only
  placeholders and public fork evidence.

Forbidden next action:

- Publish final evidence or handoff while Session 2 public docs contain the
  private source checkout path.

## Review Finding 2 - NVFP4 sidecar preflight missing at loader boundary

Failing command:

```bash
rtk .venv-mig-s2/bin/python -m pytest -q tests/diffusion/model_loader/test_diffusers_loader.py::test_get_weights_iterator_validates_nvfp4_sidecar_before_weight_discovery
```

Output excerpt:

```text
AttributeError: module 'vllm_omni.diffusion.model_loader.diffusers_loader' has no attribute 'ModelOptNativeNvfp4CheckpointAdapter'
```

Category: BUG

Evidence:

- `docs/session_2/specs/modelopt_checkpoint_adapters.md` requires
  ModelOpt-native sidecar validation before weight-file discovery.
- `vllm_omni/diffusion/model_loader/diffusers_loader.py` called the FP8
  preflight validator before `_prepare_weights`, but did not call the NVFP4
  validator.
- The regression test asserts that an NVFP4 preflight error prevents
  `_prepare_weights` from running.

Why other categories do not fit:

- SPEC_GAP: the sidecar preflight timing is explicitly specified.
- AMBIGUITY: NVFP4 is one of the ModelOpt-native layouts listed in the adapter
  requirement.
- ENVIRONMENT: the test runs in the isolated venv and fails before any external
  dependency or model weight access.
- TEST_BUG: the test asserts the contract boundary, not a private implementation
  detail.

Allowed next action:

- Import/export `ModelOptNativeNvfp4CheckpointAdapter` at the loader boundary and
  call `validate_source_sidecar(source)` before `_prepare_weights`.

Forbidden next action:

- Leave NVFP4 malformed-sidecar validation to post-discovery adapter detection
  while claiming the sidecar preflight requirement is satisfied.

Disposition:

- Fixed in public fork commit `6970350` and rechecked with compileall plus the
  expanded targeted pytest suite.
