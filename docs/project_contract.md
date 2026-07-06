# Project Contract - GitHub Migration Public Beta

Date: 2026-07-06
Status: Active blueprint

Compilation: two-pass. The first pass drafted from the owner requirements,
clarifying decisions, current public GitHub remote state, public Hugging Face
model pages, and the README guidance in `references/readme.howto.md`. The second
pass removed private-source evidence, demoted runtime claims that lack public
verification to gates, removed legacy submodules from the first milestone, and
rewrote ambiguous release language as testable acceptance criteria. This document
is the revised output only.

Authority chain: read this file before implementing any migration session.
Session-specific authority comes from `docs/session_{n}_contract.yaml`. If a
session contract conflicts with this file, stop and record the conflict before
editing.

## 1. Objective

Migrate Cosmos3-Nano-WebUI to GitHub as a public beta / research preview. The
migration must produce a curated public repo, a pinned public vLLM-Omni fork
dependency, external Hugging Face checkpoint setup, CPU-only GitHub Actions,
local-build Docker/Compose, public project hygiene, and manual GPU release gates.

## 2. Hard Commitments

1. **Session identity:** session contracts are `MIG-S1` through `MIG-S8`.
2. **Public evidence only:** public docs cite only public remotes, public model
   pages, repo files, commands run during migration, and owner decisions. Private
   source evidence is not cited.
3. **Curated import:** migrate selected runtime source, schemas, tests, deploy
   files, tools, and fresh public docs. Do not mirror private history or archives.
4. **vLLM-Omni first-class dependency:** the Cosmos3 patch line must be rebased
   or merged into the GitHub fork and pinned by public commit or tag before this
   repo depends on it.
5. **No public vLLM-Omni submodule in milestone 1:** WebUI Docker/build config
   consumes the pinned GitHub fork commit. The WebUI repo does not vendor or
   submodule `vllm-omni` in the first public beta.
6. **External weights:** checkpoints are downloaded or mounted by operators from
   public Hugging Face repos. No weights are committed or baked into images.
7. **CPU CI first:** GitHub Actions run CPU-only checks. GPU inference is a
   manual release gate for beta.
8. **Local Docker first:** users build images locally. Publishing Docker images is
   deferred.
9. **MIT for repo code:** WebUI/API code uses MIT unless a later owner decision
   changes it. Model and dependency licenses are separate and must be called out.
10. **Full surface target, beta language:** the migration targets all current API
    and WebUI modes, but public claims stay evidence-qualified until migrated
    checks pass.
11. **No legacy submodule import:** plain vLLM and TensorRT-LLM submodules are
    not part of the first milestone unless a session proves a required runtime
    dependency.
12. **No private labels:** public docs use `Cosmos3-Nano-WebUI` only.

## 3. Invariants

- **INV-1:** Public files contain no private hosts, private absolute paths,
  private codenames, secrets, tokens, or local-only artifact references.
- **INV-2:** Model weights and generated media artifacts are never committed to
  Git and are never baked into Docker images.
- **INV-3:** The WebUI repo consumes vLLM-Omni through a pinned public GitHub fork
  commit or tag.
- **INV-4:** Checkpoint locations are configurable operator inputs. Defaults use
  placeholders or repo-relative examples, not private paths.
- **INV-5:** CPU CI is deterministic and does not require CUDA, model weights, or
  private network access.
- **INV-6:** GPU and performance claims require manual validation evidence from
  the migrated public repo state.
- **INV-7:** README and docs distinguish repo code license from model and
  dependency licenses.
- **INV-8:** Public beta can ship with manual GPU gates, but unverified surfaces
  must be marked clearly.
- **INV-9:** Public API route names and request shapes are not changed during
  import unless the session contract allows it and tests cover it.
- **INV-10:** Any production dependency added during migration has an explicit
  reason and appears in CI or local build verification.

## 4. Gates

- **GATE-MIG-S1-SCOPE:** Public repo state, public remote state, migration scope,
  file inclusion/exclusion rules, and private-reference policy are recorded.
- **GATE-MIG-S2-VLLM:** The Cosmos3 vLLM-Omni patch line is rebased or merged into
  the GitHub fork, deterministic tests pass, and a public commit or tag is pinned
  for this repo.
- **GATE-MIG-S3-IMPORT:** API, WebUI, schemas, tests, tools, and non-Docker deploy
  support are imported in curated form, with private-reference and weight scans
  passing.
- **GATE-MIG-S4-HF:** FP8 and NVFP4 Hugging Face checkpoints are verified for
  public metadata, license, file layout, and compatibility expectations. Any
  drift is dispositioned before Docker/README claim it.
- **GATE-MIG-S5-CI:** CPU-only GitHub Actions pass and cover Python, WebUI,
  schema, and render-only Docker/Compose checks.
- **GATE-MIG-S6-DOCKER:** Local-build Docker/Compose uses the pinned vLLM-Omni
  fork and external checkpoint mounts without private paths, and render/build
  checks pass.
- **GATE-MIG-S7-PUBLIC:** README and hygiene files are present, links resolve,
  setup language is public-beta accurate, and claims match evidence.
- **GATE-MIG-S8-BETA:** Evidence, risks, release checklist, and manual GPU gates
  are reviewed. The owner records GO or NO-GO for public beta.

## 5. Session Routing

Risk classification follows the requested risk router.

| Session | Risk | Routing | Human gate |
|---|---|---|---|
| MIG-S1 Public inventory and scope | low | single_agent | No |
| MIG-S2 vLLM-Omni rebase and pin | high | branch_and_compare | On rebase conflict or test failure |
| MIG-S3 Curated source import and scrub | high | worker_plus_reviewers | On scrub failure |
| MIG-S4 Hugging Face verification | high | branch_and_compare | On artifact drift |
| MIG-S5 CPU CI | medium | worker_plus_reviewers | No |
| MIG-S6 Docker/Compose | high | worker_plus_reviewers | On GPU runtime blocker |
| MIG-S7 README and hygiene | medium | worker_plus_reviewers | On licensing or claim dispute |
| MIG-S8 Release gate | high | worker_plus_reviewers | Yes |

High-risk sessions require deterministic checks, sharded review over the review
axes, adversarial verification of claims, and any named owner gate before merge.

## 6. Change Control

- Do not edit outside a session contract's `blast_radius.allowed_files`.
- Do not add model weights, generated media, caches, private evidence, or bulky
  archives.
- Do not add private path examples to public docs. Use placeholders such as
  `/path/to/Cosmos3-Nano-FP8-Blockwise` only in examples.
- Do not change the public product surface during import unless the session
  contract allows it.
- Do not add Docker image publishing, GPU CI, or a public submodule without a
  contract amendment.
- Treat `.github/**`, Dockerfiles, Compose files, dependency manifests, and
  release docs as change-controlled surfaces.

## 7. Verification Policy

- Classify failures before fixing: environment, dependency, source, test, schema,
  Docker, model artifact, or spec drift.
- Prefer deterministic evidence: `git ls-remote`, file tree manifests, `rg`
  scans, lockfile checks, schema diffs, unit tests, workflow dry runs, Compose
  config rendering, and checkpoint metadata probes.
- GPU checks are manual gates. Record hardware, driver/CUDA context when
  available, checkpoint repo and revision, vLLM-Omni commit, request shape,
  artifact metadata, and result.
- Claims in README and docs must point to evidence rows or be phrased as
  limitations.

## 8. Done Condition

The migration blueprint is done when all requested docs exist, public evidence
rules are enforced, every session has a contract, all release-blocking risks are
routed, and the first public beta has a clear path from empty GitHub seed to
curated source import, pinned vLLM-Omni dependency, verified HF checkpoints,
CPU CI, local Docker, README/hygiene, manual GPU gates, and owner GO/NO-GO.

