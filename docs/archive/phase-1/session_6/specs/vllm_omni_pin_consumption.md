# Specification - vLLM-Omni Pin Consumption

Session: MIG-S6
Capability: vLLM-Omni Pin Consumption

## ADDED Requirements

### Requirement: Generation image installs the immutable MIG-S2 pin

The generation image MUST install the vLLM-Omni fork from the immutable `MIG-S2`
tag or commit on the public fork, never a mutable branch alone (INV-3). The pinned
reference MUST be `git@github.com:fengwang/vllm-omni.git` tag
`cosmos3-nano-webui-mig-s2` (commit `697035018b70cef76b974a909d23371a9984c3f2`),
installed over HTTPS for public reproducibility.

#### Scenario: Install references the immutable tag

WHEN `deploy/vllm-omni.Dockerfile` is read
THEN it SHALL install
`git+https://github.com/fengwang/vllm-omni.git@cosmos3-nano-webui-mig-s2`
(or the equivalent commit SHA)
AND SHALL NOT install from a bare mutable branch such as
`mig-s2-cosmos3-quant-pin` without the tag/commit pin.

#### Scenario: Pin is discoverable for handoff

WHEN the deployment docs and `.env.example` are read
THEN the vLLM-Omni pin (tag and commit) SHALL be recorded so `MIG-S7`/`MIG-S8` can
cite and re-verify it.

### Requirement: The WebUI repo does not vendor or submodule the fork

Per the project contract (milestone-1: no public submodule), the repository MUST NOT
add `vllm-omni` as a git submodule or vendored source tree; it is consumed only as a
build-time install in the generation image.

#### Scenario: No submodule is introduced

WHEN the repository is inspected after this session
THEN there SHALL be no `vllm-omni` submodule entry and no vendored fork source under
version control.
