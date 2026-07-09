# Specification - Legacy Dependency Exclusion

Session: MIG-S3
Capability: Legacy Dependency Exclusion

## ADDED Requirements

### Requirement: No legacy submodule enters the public repo

The public repo MUST NOT contain the `submodules/vllm`, `submodules/TensorRT-LLM`,
or `submodules/vllm-omni` gitlinks or their contents.

#### Scenario: Submodule scan is clean

WHEN `rg --files | rg "(^|/)submodules/(vllm|TensorRT-LLM|vllm-omni)(/|$)|(^|/)TensorRT-LLM(/|$)"`
is run
THEN it SHALL return no match.

### Requirement: TensorRT-LLM engine code is excluded

`api/engines/trtllm/` and `tests/test_trtllm_contract.py` MUST NOT be imported, and
no kept code may import the TensorRT-LLM engine.

#### Scenario: trtllm engine absent and unreferenced

WHEN the imported tree is listed and scanned
THEN `api/engines/trtllm/` and `tests/test_trtllm_contract.py` SHALL be absent
AND no kept file SHALL contain an `import engines.trtllm` or
`from engines.trtllm` statement.

### Requirement: The kept import graph loads without excluded modules

The imported API SHALL import cleanly with no excluded module present and without
`torch`, `tensorrt_llm`, `vllm`, or CUDA installed.

#### Scenario: App imports torch-free

WHEN `PYTHONPATH=api python -c "import app.main"` is run in a torch-free
environment
THEN it SHALL exit 0
AND it SHALL NOT require `torch`, `tensorrt_llm`, the `vllm` package, or CUDA.

### Requirement: vLLM-Omni is consumed as a decoupled client, not a submodule

The imported code SHALL treat vLLM-Omni as an external HTTP service (the Session 2
public pin is wired at the S6 deploy layer). It MUST NOT import the `vllm_omni`
Python package or depend on a vendored submodule.

#### Scenario: vllm_omni engine is an HTTP client

WHEN `api/engines/vllm_omni/` is read
THEN it SHALL communicate with vLLM-Omni over HTTP via an operator-configurable
base URL
AND it SHALL NOT contain `import vllm_omni` or `from vllm_omni` package imports.
