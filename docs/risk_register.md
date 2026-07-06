# Risk Register - GitHub Migration Public Beta

Date: 2026-07-06

Status values are blueprint-time. Sessions update rows with evidence as they
close.

| ID | Risk | Probability | Impact | Owner Session | Mitigation / Gate | Status |
|---|---|---:|---:|---|---|---|
| R-01 | Private hosts, private paths, codenames, or local-only artifact references leak into the public repo. | Medium | High | MIG-S1, MIG-S3, MIG-S7 | Define scrub rules in `MIG-S1`; run recursive `rg` scans in import and README sessions; block release at `GATE-MIG-S8-BETA` if any remain. | Open |
| R-02 | The Cosmos3 vLLM-Omni patch series conflicts with current GitHub fork `main` or upstream changes. | Medium | High | MIG-S2 | Use branch-and-compare rebase; run targeted vLLM-Omni tests; pin a public commit only after tests pass. | Open |
| R-03 | The public HF checkpoints differ from the runtime assumptions needed by the WebUI/API and vLLM-Omni fork. | Medium | High | MIG-S4 | Probe FP8/NVFP4 metadata, file layout, license, and compatibility before Docker and README depend on them. | Open |
| R-04 | The NVFP4 HF model card is empty, so public users lack setup context. | High | Medium | MIG-S4, MIG-S7 | Put checkpoint setup in this repo's README/docs; optionally create a separate model-card follow-up outside this repo. | Open |
| R-05 | CPU-only CI passes while GPU inference is broken. | Medium | High | MIG-S5, MIG-S8 | Keep CPU CI as fast gate, but require manual GPU release evidence before beta GO. | Open |
| R-06 | Docker examples accidentally bake or download weights into images. | Low | High | MIG-S6 | Use external mounts/configurable paths; scan Dockerfiles and Compose for weight-copy patterns; document explicit setup. | Open |
| R-07 | Legacy plain vLLM or TensorRT-LLM code is imported and bloats the repo or creates broken optional paths. | Medium | Medium | MIG-S3 | Exclude legacy submodules and unsupported code unless a public runtime dependency is proven. | Open |
| R-08 | The full target product surface is too broad for one public beta migration. | Medium | Medium | MIG-S3, MIG-S8 | Preserve the full target surface, but allow `MIG-S8` to mark specific modes beta-limited if manual evidence is missing. | Open |
| R-09 | README claims outrun evidence, especially around RTX 5090, FP8, NVFP4, and performance. | Medium | High | MIG-S7, MIG-S8 | Use evidence-qualified wording; link claims to evidence rows; adversarial review README before beta. | Open |
| R-10 | GitHub Actions fail due to dependency drift or missing generated files. | Medium | Medium | MIG-S5 | Pin setup versions, use lockfiles, add schema sync checks, and classify failures before changing source. | Open |
| R-11 | License boundaries are unclear between MIT repo code, model license, and dependency licenses. | Low | High | MIG-S7 | Add MIT `LICENSE`; README calls out HF model license and dependency license responsibility. | Open |
| R-12 | Public history becomes noisy if private development history is imported directly. | Low | Medium | MIG-S3 | Use fresh curated public commits and summarize provenance in public evidence terms only. | Open |
| R-13 | Docker local build fails because the pinned vLLM-Omni fork commit is not installable from public inputs. | Medium | High | MIG-S2, MIG-S6 | `MIG-S2` proves fork install/test; `MIG-S6` builds from the pinned commit and records failure class if it fails. | Open |
| R-14 | A secret or token is added to workflow files or examples. | Low | High | MIG-S5, MIG-S7 | Keep first milestone free of registry publishing and secrets; scan `.github/**`, docs, and env examples. | Open |
| R-15 | Public beta release lacks enough project hygiene for outside users to report bugs safely. | Medium | Medium | MIG-S7 | Add `SECURITY.md`, `CONTRIBUTING.md`, issue templates, and release checklist before beta GO. | Open |

