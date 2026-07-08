# Gate Record - MIG-S1 .. MIG-S8

Date: 2026-07-07 · Branch: `session-8` (not pushed; `origin/main` = seed `c3983f7`)

## Migration gates

| Gate | Status | Public evidence |
|---|---|---|
| `GATE-MIG-S1-SCOPE` | **PASS** | `docs/session_1/{inventory,import_manifest,exclusion_manifest,scrub_checklist}.md`; baseline scans clean (`evidence_map.md`) |
| `GATE-MIG-S2-VLLM` | **PASS** | Fork branch/tag `cosmos3-nano-webui-mig-s2` = `697035018b70cef76b974a909d23371a9984c3f2` (public `git ls-remote`); S2 targeted tests 118 passed |
| `GATE-MIG-S3-IMPORT` | **PASS** | 296 files curated; `compileall api`=0, torch-free `import app.main`=0, `pytest -m "not gpu"` = 486 passed; private-ref/weight/legacy scans clean |
| `GATE-MIG-S4-HF` | **PASS** (metadata verified; drift documented) | Revisions FP8 `4e181f99…` / NVFP4 `b5c9332e…`; license `openmdw-1.0`; self-contained; local==public sha; drift D1–D4 in `docs/session_4/drift_report.md` |
| `GATE-MIG-S5-CI` | **PASS** (config verified + locally green; hosted run at-publish) | `.github/workflows/ci.yml`; `deterministic_checks.md` #2–#9 (ruff 0, pytest 486, vitest 209, build/lint/typecheck green); schema-sync gates proven to fail on drift |
| `GATE-MIG-S6-DOCKER` | **PASS** (render + lean builds; vllm-omni image = S8 gate) | `deterministic_checks.md` #10/#11 (compose fp8/nvfp4 exit 0, 0-byte stderr); api+webui `docker build` exit 0; external `:ro` mounts, loopback default |
| `GATE-MIG-S7-PUBLIC` | **PASS** | `README.md` (190 lines, evidence-qualified) + `LICENSE`/`SECURITY.md`/`CONTRIBUTING.md`/`CODE_OF_CONDUCT.md` + templates + `release_checklist.md`; 10 README links resolve; X-1 fixed (`INV-9`) |
| `GATE-MIG-S8-BETA` | **OWNER GO — public beta / research preview (ratified 2026-07-07)** | This session: `acceptance_matrix.md` (14 PASS / 2 BETA-LIMITED / 0 NO-GO), `deterministic_checks.md` (all green), `evidence_review.md`, reconciled risk register (no unowned blocker); adversarial verifier PASS. Owner ratified the recommended GO. |

## Manual GPU gate status (deferred — owner decision 1)

The GPU inference surface was **beta-limited / NOT-YET-RUN at GO**. A **post-GO GPU gate on
2026-07-08 verified T2I** (FP8 **and** NVFP4, direct on vLLM-Omni and full-stack through the
api → job → artifact) on an RTX 5090; `t2v`/`t2v_audio`/`i2v`/`forward_dynamics`/`reasoning`
remain unrun (video peak VRAM > 32 GB). **Caveat:** run on a near-pin proxy image
(`vllm-omni-local:c89089a4` ≈ pin `697035…`), **not** an image built from the pinned commit
via the public Dockerfile (which is broken — `release_checklist.md` §6); the exact-pinned build
is still unproven. `INV-8` holds (README marks modes GPU-unverified; T2I FP8/NVFP4 upgradable
to verified). Any later run **must match** these pins/revisions or the evidence is invalid:

- vLLM-Omni fork commit: `697035018b70cef76b974a909d23371a9984c3f2`
- FP8 checkpoint `wfen/Cosmos3-Nano-FP8-Blockwise` @ `4e181f996abf03f3425298ef692e6e5e56fd46a4`
- NVFP4 checkpoint `wfen/Cosmos3-Nano-NVFP4-Blockwise` @ `b5c9332efbaefa72c99890b1b1150da12ca9256c`
- BF16 base `nvidia/Cosmos3-Nano` @ `fea6e03ac3d7884b4105ed8ee79fc480fca70965` (reasoning + action/forward_dynamics)

Cases deferred: `EV-MIG-GPU-FP8-T2V`, `-FP8-T2V-AUDIO`, `-FP8-I2V`, `-FP8-T2I`, `-FP8-FD`,
`-NVFP4-SURFACE`, `-REASONING`, `-JOBS-SSE`, `-ARTIFACTS` (see `eval_seed_cases.md`).
Required evidence fields per run: hardware, driver/CUDA, checkpoint repo+revision, vLLM-Omni
commit, request shape, artifact metadata, pass/fail (`NFR-6`).

**Drift D1** (characterized 2026-07-08): the in-process `diffusers_oracle` cannot load the
current public checkpoints, **but the default `vllm_omni` container path CAN** — it loads both
FP8 (`W8A16`) and NVFP4 (`W4A16`) and generates T2I — **once the checkpoints' stale top-level
`model.safetensors.index.json` is removed** (it references 7 non-existent
`diffusion_pytorch_model-*` shards; the real weight is a single consolidated file). D1's
residual is therefore a **published-checkpoint packaging bug** (stale weight index), routed to
an owner HF-side fix (R-03) — not a runtime/quant incompatibility.

**Drift D3** (external, owner follow-up): the public HF checkpoint repos ship dev-scratch
(`_s2_*`) / provenance / loader-script files (`docs/session_4/drift_report.md` D3; R-01).
This is external to this repo (a Hugging-Face-side cleanup), not a tracked-file leak here —
recorded so it is not lost from the release bundle.

**Literal deferred commands** (for the GPU session): the vLLM-Omni image build is in
`docs/release_checklist.md` §6; the GPU marker run (`COSMOS3_ENABLE_GPU_TESTS=1 pytest -m gpu`)
and the `EV-MIG-GPU-*` smokes are in §7.

## Recommended verdict and rule

**Recommendation: GO for public beta / research preview.**
**OWNER DECISION (2026-07-07): GO — ratified.** The recommendation was accepted; the beta
ships as a research preview with the GPU surface beta-limited (below). The owner did not take
the "GPU-evidence-before-exposure" NO-GO lever.

GO rule (D-6) — all clauses hold, each backed by evidence:

| GO clause | Met? | Evidence |
|---|---|---|
| Scrub clean | ✅ | `deterministic_checks.md` #12–#15 |
| CPU checks green | ✅ | `deterministic_checks.md` #2–#9 (pytest 486, vitest 209, ruff 0, build/lint/typecheck) |
| Compose fp8+nvfp4 render clean | ✅ | `deterministic_checks.md` #10/#11 |
| `LICENSE` + hygiene present & correct | ✅ | `GATE-MIG-S7-PUBLIC`; three-way license separation |
| Every runtime claim evidence-qualified | ✅ | `evidence_review.md`; README per-mode GPU-unverified (S7) |
| No unowned release-blocking risk | ✅ | reconciled `risk_register.md`: R-01 (mitigated via S8 re-scan), R-05/R-08/R-13/R-16 (owner beta-limited dispositions); no risk left open+unowned |
| GPU surface marked beta-limited | ✅ | this record + README + `acceptance_matrix.md` FR-9/NFR-6 |
| Every PRD MUST covered | ✅ | `acceptance_matrix.md` (16 MUSTs; 0 NO-GO) |

**GO is conditional on** (not blockers — post-publish / standing):
1. The standing **beta-limited GPU gate** — the full GPU surface is unverified; each mode is
   marked GPU-unverified. First post-publish task is the GPU session (run `EV-MIG-GPU-*`,
   build the pinned vLLM-Omni image, resolve drift D1).
2. **At-publish items** (`release_checklist.md` §9): enable GitHub Private vulnerability
   reporting; confirm the CI badge + `security/policy` + `discussions` links resolve once
   public; set repo About/topics; tag + release notes; **owner records GO/NO-GO**.
3. **At-publish CI confirmation** (§5): confirm `ci.yml` is green on the GitHub-hosted runner
   on the release commit (local equivalents already green).

If the owner requires GPU evidence **before** any public exposure, the verdict is **NO-GO
until the GPU session passes** — this is the single lever that flips the recommendation, and
it is the owner's call. No other release blocker is open.
