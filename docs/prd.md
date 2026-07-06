# PRD - GitHub Migration Public Beta

Date: 2026-07-06
Status: Approved blueprint, documentation first
Owner: Feng
Related: `docs/project_contract.md`, `docs/evidence_map.md`,
`docs/risk_register.md`, `docs/eval_seed_cases.md`,
`docs/session_{1..8}.md`

## 1. Problem

Cosmos3-Nano-WebUI is being moved from a private development setting to GitHub as
a public beta. The target public repository starts as a small seed repository,
while the project needs a usable API, WebUI, local Docker workflow, test suite,
README, and clear public setup path.

The migration must avoid common open-source release failures:

- Public files must not depend on private hosts, private absolute paths, or
  unpublished local state.
- Model weights must not be committed to Git or baked into Docker images.
- Runtime claims about FP8, NVFP4, RTX 5090, vLLM-Omni, and Docker must be tied
  to public evidence or to explicit re-verification gates.
- The patched vLLM-Omni work must be rebased and published to the GitHub fork
  before the WebUI repo can depend on it.
- GitHub Actions should provide a reliable CPU-only quality gate, while GPU and
  checkpoint inference remain manual release gates for the first public beta.

## 2. Goal

Create a public beta migration plan and contract pack for Cosmos3-Nano-WebUI.
The first public milestone should let a user clone the repo, install the API and
WebUI, download or mount the FP8/NVFP4 checkpoints from Hugging Face, build local
Docker stacks, and understand which GPU paths were verified manually.

The plan targets the full product surface:

- API and WebUI for `t2v`, `t2v_audio`, `i2v`, `t2i`,
  `forward_dynamics`, reasoning, jobs/SSE, health, metrics, artifacts, and
  history.
- A pinned GitHub `vllm-omni` fork commit used by Docker/build config.
- External FP8 and NVFP4 checkpoints hosted on Hugging Face.
- CPU-only GitHub Actions for lint, typecheck, unit tests, schema checks, and
  Docker/Compose rendering.
- Manual GPU gates for RTX 5090 inference before public beta release.
- MIT licensing for the WebUI/API code, with model and dependency licenses called
  out separately.

## 3. Owner Decisions

These decisions are binding for this migration blueprint:

1. Session IDs are `MIG-S1` through `MIG-S8`.
2. This is a fresh GitHub migration blueprint, not a port of older phase docs.
3. Public docs use public-verifiable evidence only. Private source evidence is
   not cited in public docs.
4. The import is curated: runtime source, deploy files, schemas, tests, tools,
   and fresh public docs are migrated. Bulky artifacts, archives, caches,
   temporary folders, private evidence, and local-only generated outputs are not.
5. `vllm-omni` is handled in a dedicated session. The local Cosmos3 patch series
   must be rebased or merged into `git@github.com:fengwang/vllm-omni.git`, then
   pinned by commit or tag.
6. The WebUI repo does not keep `vllm-omni` as a public submodule in the first
   milestone. Docker/build config consumes a pinned GitHub fork commit.
7. Model weights stay external. The README and compose examples point to:
   `wfen/Cosmos3-Nano-FP8-Blockwise` and
   `wfen/Cosmos3-Nano-NVFP4-Blockwise`.
8. No model weights are committed to Git or published inside Docker images.
9. Docker is local build-only for the first milestone. No GHCR or other registry
   publishing is required.
10. GitHub Actions are CPU-only for the first milestone. GPU checks are manual
    release gates.
11. Public posture is beta / research preview, not production-ready release.
12. README work is planned as a later migration session. This documentation pass
    creates the blueprint only.
13. Use only `Cosmos3-Nano-WebUI` as the public project name.
14. Do not migrate legacy plain vLLM or TensorRT-LLM submodules in the first
    milestone unless a later session proves a runtime dependency.
15. Add core project hygiene in the public beta: `LICENSE`, `SECURITY.md`,
    `CONTRIBUTING.md`, issue templates, and a release checklist.

## 4. Requirements

Requirement keywords follow RFC 2119. A claim that is not public-verifiable at
blueprint time is written as a verification task or release gate, not as a
shipped capability.

### Functional

- **FR-1 (MUST)** Create and maintain the migration contract pack:
  `docs/prd.md`, `docs/project_contract.md`, `docs/evidence_map.md`,
  `docs/risk_register.md`, `docs/eval_seed_cases.md`,
  `docs/session_{1..8}.md`, and `docs/session_{1..8}_contract.yaml`.
- **FR-2 (MUST)** Keep public docs and migrated files free of private hosts,
  private absolute paths, private codenames, secrets, tokens, and local-only
  artifacts.
- **FR-3 (MUST)** Publish or prepare a rebased Cosmos3 `vllm-omni` patch line in
  the GitHub fork, with deterministic tests and a pinned commit or tag for this
  repo to consume.
- **FR-4 (MUST)** Curate the WebUI/API import so the public repo contains the
  runtime source, schemas, tests, tools, and docs needed for a public beta, while
  excluding archives, caches, bulky evidence, and model weights.
- **FR-5 (MUST)** Verify public Hugging Face FP8 and NVFP4 artifacts before beta
  release. Verification must record repo IDs, license metadata, file layout,
  checkpoint compatibility expectations, and any drift from the WebUI runtime
  assumptions.
- **FR-6 (MUST)** Configure CPU-only GitHub Actions for repeatable public checks:
  Python lint/tests, WebUI lint/typecheck/unit tests, OpenAPI/schema checks, and
  Docker/Compose rendering where feasible.
- **FR-7 (MUST)** Provide local-build Docker/Compose files that use configurable
  checkpoint paths or documented mounts. Compose files must not reference private
  model paths.
- **FR-8 (MUST)** Plan README and project hygiene for the public beta:
  clear one-line pitch, logo use, quickstart, external weights setup, limitations,
  license notices, security reporting, contribution guide, issue templates, and
  release checklist.
- **FR-9 (MUST)** Before public beta, run and record manual GPU validation for
  the full target surface on supported hardware, or explicitly mark any unverified
  surface as beta-limited.
- **FR-10 (MUST)** The public repo must not import legacy plain vLLM or
  TensorRT-LLM submodules in the first milestone unless a session records a
  public, testable runtime need.
- **FR-11 (SHOULD)** Keep the first beta branch history clean and curated rather
  than importing private development history.
- **FR-12 (SHOULD)** Use evidence-qualified README language for RTX 5090, FP8,
  and NVFP4 support. Strong performance or compatibility claims require linked
  verification evidence from the migrated public repo.

### Non-Functional

- **NFR-1 (MUST)** No secret, token, private host, private absolute path, model
  weight, cache, or large generated artifact is committed.
- **NFR-2 (MUST)** Every release-blocking recommendation in the contract has an
  evidence row or is marked speculative with a re-verification gate.
- **NFR-3 (MUST)** The first public milestone is usable without private network
  access.
- **NFR-4 (MUST)** Docker and README setup paths work with configurable local
  checkpoint directories populated from public Hugging Face repos.
- **NFR-5 (MUST)** CPU CI failures are classified before they are fixed:
  environment, dependency, test, source, generated schema, or spec drift.
- **NFR-6 (MUST)** GPU checks record hardware, driver/CUDA context where
  available, checkpoint repo and revision, vLLM-Omni fork commit, request shape,
  artifact metadata, and pass/fail result.

## 5. Acceptance Criteria

The GitHub migration public beta is ready only when all are true:

1. The contract pack exists and uses `MIG-S1` through `MIG-S8`.
2. The public repo has no private path, private host, secret, model weight, or
   bulky private evidence artifact.
3. The Cosmos3 `vllm-omni` patch line is available in the GitHub fork and this
   repo consumes a pinned public commit or tag.
4. API, WebUI, schemas, tests, deploy files, and tools are imported in curated
   form with a clean public file tree.
5. HF FP8 and NVFP4 checkpoint metadata and compatibility assumptions are
   verified and documented.
6. CPU-only GitHub Actions pass for the configured checks.
7. Local Docker/Compose renders without private paths and can be built from public
   inputs.
8. README and project hygiene files are present and consistent with public beta
   scope.
9. Manual GPU gates are recorded for the full target surface, or unsupported
   cases are clearly marked as not yet verified.
10. `docs/evidence_map.md`, `docs/risk_register.md`, and
    `docs/eval_seed_cases.md` are updated to the final migration state.

## 6. Non-Goals

- Do not write application code during the blueprint documentation pass.
- Do not commit or push the blueprint pack unless explicitly requested later.
- Do not publish Docker images in the first beta milestone.
- Do not require GPU GitHub Actions before public beta.
- Do not commit model weights, generated videos, large evidence folders, caches,
  or private source archives.
- Do not cite private source paths or private development evidence in public docs.
- Do not migrate legacy plain vLLM or TensorRT-LLM submodules in the first
  milestone without a recorded public runtime need.
- Do not claim production readiness.

## 7. Session Plan

| # | Session | Risk | Primary gate |
|---|---|---|---|
| 1 | Public repo inventory and migration scope | low | `GATE-MIG-S1-SCOPE` |
| 2 | vLLM-Omni patch rebase and GitHub fork pin | high | `GATE-MIG-S2-VLLM` |
| 3 | Curated WebUI/API source import and scrub | high | `GATE-MIG-S3-IMPORT` |
| 4 | Hugging Face checkpoint verification and model setup docs | high | `GATE-MIG-S4-HF` |
| 5 | CPU-only CI and test stabilization | medium | `GATE-MIG-S5-CI` |
| 6 | Local-build Docker/Compose migration | high | `GATE-MIG-S6-DOCKER` |
| 7 | README, project hygiene, and beta polish | medium | `GATE-MIG-S7-PUBLIC` |
| 8 | Release gate, evidence review, and handoff | high | `GATE-MIG-S8-BETA` |

