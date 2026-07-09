# Eval Seed Cases - GPU Release Readiness and Upstream Quant Contribution

Date: 2026-07-08

These cases seed deterministic checks and manual release gates for
`GPU-S1`..`GPU-S5`. They assume the checkpoint revisions change during
`GPU-S2`; any case that names a revision must be re-pointed at the new
revision in the same session that changes it (`project_contract.md`
Hard Commitment 3).

## Public Checkpoint IDs

- FP8 (generation): `wfen/Cosmos3-Nano-FP8-Blockwise` @
  `9bf5d6ae164688487bdb71947ccc6ebe70d12900` — pinned by `GPU-S2`, replacing
  the pre-fix `4e181f996abf03f3425298ef692e6e5e56fd46a4`
  recorded in `docs/archive/phase-1/evidence_map.md`.
- NVFP4 (generation): `wfen/Cosmos3-Nano-NVFP4-Blockwise` @
  `5514c42b9759739f545e0d0dee453db8d8525fbc` — pinned by `GPU-S2`, replacing
  the pre-fix `b5c9332efbaefa72c99890b1b1150da12ca9256c`.
- BF16 base (reasoner + action/forward_dynamics, unaffected by `GPU-S2`):
  `nvidia/Cosmos3-Nano` @ `fea6e03ac3d7884b4105ed8ee79fc480fca70965`.
- vLLM-Omni fork commit (unaffected by `GPU-S1`, which only changes how it
  is installed, not which commit is pinned):
  `697035018b70cef76b974a909d23371a9984c3f2`.

## Deterministic Checks

| ID | Purpose | Inputs | Expected properties | Gate |
|---|---|---|---|---|
| EV-GPU-DOCKERFILE-BUILD | Confirm the public Dockerfile builds and serves. | `docker compose -f deploy/docker-compose.fp8.yml build vllm-omni`, `up`, `curl /v1/models`. | Build exits 0 from public inputs only (no cosmos3 prebuilt); `/v1/models` responds. | GPU-S1 |
| EV-GPU-CHECKPOINT-FRESH-CLONE | Confirm both HF repos resolve cleanly from a fresh clone/download. | `git clone` and `hf download` of both `wfen/*` repos into a clean directory. | No unresolved LFS/Xet pointers; no stale top-level `model.safetensors.index.json`. | GPU-S2 |
| EV-GPU-REPIN-SWEEP-COMPLETE | Confirm no stale checkpoint revision remains anywhere in the repo after re-pinning. | `rg` for both pre-fix revision SHAs across the whole tracked tree. | Zero matches outside this eval file's own historical reference above. | GPU-S2 |
| EV-GPU-UPSTREAM-STATE-CHECK | Confirm the upstream-state question is answered with evidence before contribution code exists. | `git log`/`rg` against `vllm-project/vllm-omni` `main`. | A recorded finding (present or absent) exists before any isolation/rebase commit. | GPU-S4 |
| EV-GPU-QUANT-ISOLATION-COMPILE | Confirm the isolated quant-loader branch compiles without Cosmos3-specific code. | `python -m compileall vllm_omni` on the isolated, rebased branch; `rg` for Cosmos3-specific imports. | Compiles clean; no Cosmos3-specific import in the isolated files. | GPU-S4 |
| EV-GPU-PR-PRECHECK | Confirm the fork's `precheck-pr` skill is clean against the submission branch. | `precheck-pr` quick, then full, run in the `fengwang/vllm-omni` fork checkout. | Clean on both passes before submission. | GPU-S5 |
| EV-GPU-PR-CI-GREEN | Confirm upstream CI and DCO requirements pass. | `.github/workflows/{pre-commit,build_wheel}.yml`, `git log --show-signature`. | CI green; every commit DCO-signed. | GPU-S5 |

## Manual GPU Release Gates

Manual GPU cases require the evidence fields below.
`EV-GPU-FP8-T2I`, `EV-GPU-NVFP4-T2I`, `EV-GPU-T2V-SMOKE`, and
`EV-GPU-JOBS-ARTIFACT` must use the revisions/commit that `GPU-S1` and
`GPU-S2` actually produced, not the pre-fix values listed under Public
Checkpoint IDs above. `EV-GPU-S1-BUILD-T2I-SMOKE` is the one exception: it
runs before `GPU-S2`'s fix exists, so the pre-fix checkpoint revision with
the already-known local workaround (`docs/model_setup.md` §9) is acceptable
there.

| ID | Purpose | Checkpoint | Request shape | Expected properties | Gate |
|---|---|---|---|---|---|
| EV-GPU-S1-BUILD-T2I-SMOKE | Confirm the from-source image itself can generate a T2I artifact, independent of the checkpoint fix. | FP8 or NVFP4 (either) | Short prompt, documented seed. | Valid image artifact on the RTX 5090 from the `GPU-S1` image; the pre-fix revision with the known index-removal workaround is acceptable here. | GPU-S1 |
| EV-GPU-FP8-T2I | FP8 text-to-image, from-source build + fresh checkpoint. | FP8 | Short prompt, documented seed. | Valid image artifact, direct and full-stack through the api, with no manual workaround. | GPU-S3 |
| EV-GPU-NVFP4-T2I | NVFP4 text-to-image, from-source build + fresh checkpoint. | NVFP4 | Short prompt, documented seed. | Valid image artifact, direct and full-stack through the api, with no manual workaround. | GPU-S3 |
| EV-GPU-T2V-SMOKE | Best-effort small text-to-video smoke. | FP8 or NVFP4 | Short prompt, low frame count, documented seed. | Valid video artifact, or a recorded reason it was scoped out (PRD FR-6, SHOULD). | GPU-S3 |
| EV-GPU-JOBS-ARTIFACT | Full-stack job and artifact retrieval on the from-source build. | Either checkpoint | Async generation request observed through the api or WebUI. | Job reaches a terminal state; artifact is downloadable. | GPU-S3 |

## GPU-S2 Retrospective Additions (2026-07-09)

Harvested per `docs/agent_workflow/prompts/eval_harvest.md`. Two of the
three gaps below were caught by the sharded review or adversarial
verification, not by this session's own deterministic checks or first
sweep — the retrospective distinction matters: it's evidence the review
layers are doing real work, not rubber-stamping.

| ID | Purpose | Inputs | Expected properties | Gate | Caught by |
|---|---|---|---|---|---|
| EV-GPU-SWEEP-HIDDEN-FILES | Confirm a whole-repo pin-sweep command actually scans dotfiles, not just visibly-listed files. | A tracked dotfile (e.g. `.env.example`) containing a target string; the literal sweep command from the session contract. | The sweep command finds the match. `rg`'s default directory walk skips dotfiles — any sweep command lacking `--hidden` (or an equivalent) silently under-reports. | Any session with a whole-repo string/pin sweep | Adversarial verification (missed by this session's own first sweep and by sharded review, both of which used the un-hidden form) |
| EV-GPU-CHECKPOINT-ORPHAN-CONTENT | Confirm a checkpoint repo's small files contain real content, not LFS-pointer text, independent of whether a *current* `.gitattributes` rule matches them. | A file whose committed git blob is LFS-pointer-shaped but whose path matches no current LFS pattern (an "orphan" — e.g. from a rule removed without a renormalize). | `HfApi.get_paths_info`'s `.lfs` attribute correctly flags it regardless of current attributes; `hf_hub_download`/Hub resolve endpoints do **not** — they transparently smudge LFS pointers even for unmatched paths, so a content-download-based check can never detect this class of bug. | Any session verifying HF checkpoint packaging | Sharded review (correctness axis; empirically reproduced against a real orphan file) |
| EV-GPU-PROBE-BIDIRECTIONAL-LFS | Confirm an automated LFS-placement check catches a large/binary file that unexpectedly lost its LFS backing (de-LFS regression), not only a small file that's wrongly LFS-backed. | A manifest entry for a known-large path with `is_lfs=False`. | The check flags it; a one-directional implementation (checking only "small file wrongly LFS" and never the reverse) silently passes a de-LFS regression — exactly the risk R-04-style contracts exist to guard. | Any session writing an automated LFS/packaging verification probe | Sharded review (correctness + tests axes, 2 independent reviewers, same finding) |

**New repo rule candidates** (not applied this session — `project_contract.md`
and `AGENTS.md` are outside `GPU-S2`'s blast radius; recorded here and in
`docs/handoff.md` for the owner/a future session with authority to edit
them):
- `project_contract.md` §7's "Verification Policy" recommends `rg` sweeps
  for stale pins; it should note that `rg` skips dotfiles by default and
  name `--hidden` (or equivalent) as required, not optional.
- Any future verification probe that checks "is this HF-hosted file's
  content real" should use `HfApi`-level blob/attribute metadata, not a
  Hub-level content-download API — the latter transparently resolves LFS
  pointers regardless of git-attribute state and cannot detect this class
  of packaging bug.

## GPU-S1 Retrospective Additions (2026-07-09)

`EV-GPU-DOCKERFILE-BUILD` and `EV-GPU-S1-BUILD-T2I-SMOKE` above both passed —
see `docs/evidence_map.md` and `docs/session_1/gate_record.md` for the
executed evidence. These two new cases were harvested from gaps the
sharded review and adversarial verification surfaced while executing them,
and apply to any future session that touches `deploy/vllm-omni.Dockerfile`
or a similarly-structured build (`GPU-S4` if it produces Docker-adjacent
artifacts; any later rework of this file).

| ID | Purpose | Inputs | Expected properties | Gate |
|---|---|---|---|---|
| EV-GPU-DOCKERFILE-NO-COSMOS3-TEXTUAL | Complement the layer-hash cosmos3-reuse check, which has a blind spot: `COPY --from=<image>` repackages content into a new layer diffID, so a layer-set comparison alone would false-PASS a `COPY --from=vllm/vllm-omni:cosmos3` instruction. | `rg -i cosmos3 deploy/vllm-omni.Dockerfile deploy/docker-compose*.yml` (excluding this repo's own `cosmos3-nano-*:local` tags). | Zero matches referencing the forbidden prebuilt as a `FROM`, `image:`, or `COPY --from=` source. | Any session changing this Dockerfile |
| EV-GPU-DOCKERFILE-GUARDRAILS-DEFAULT | Confirm the shipped `CMD` fails **closed**, not open, without gated guardrail access, and that this is a deliberate, disclosed posture rather than a silent regression. | Start the container with the shipped default `CMD` (no override); separately with `--no-guardrails`. | Default crashes before serving (`CosmosSafetyChecker` refuses to run); `--no-guardrails` serves and generates. Both outcomes recorded, neither silently assumed. | Any session changing this Dockerfile's `CMD`/entrypoint |

## Evidence Fields

For every manual GPU case, record:

- hardware and driver/CUDA context
- WebUI repo commit
- vLLM-Omni fork commit (must be `697035018b70cef76b974a909d23371a9984c3f2`
  unless a session contract explicitly changes the pin)
- checkpoint repo ID and revision (the `GPU-S2` revision, not the pre-fix
  one)
- request mode, prompt or fixture name, dimensions, frames, fps, steps, seed
- artifact path, dimensions, streams, duration, and pass/fail result
- known limitation if the case is not passed
