# Evidence Review - MIG-S8 Release Gate

Date: 2026-07-07

Each major public-facing claim is tied to a **public** evidence pointer (a command run this
session, a tracked repo file, or a public remote / model page) and tagged **verified-now**
or **manual-gate-deferred**. No private source path, host, codename, or repository is cited
(`INV-1`; evidence-map rules). The private-reference scanner is clean over `docs/session_8/**`
(`deterministic_checks.md` #12).

## Verified now (public evidence)

| Claim | Public evidence | Tag |
|---|---|---|
| The public repo tree is scrub-clean (no private host/path/codename/secret/weight) | `deterministic_checks.md` #12 (committed scanner, `SCAN_ROOTS` incl. `docs`) + #13/#14 (weight/media) + #15 (broad-scan human gate) — all clean | verified-now |
| The `vllm-omni` Cosmos3 patch line is published and pinned by an immutable public commit | `evidence_map.md`: `git ls-remote git@github.com:fengwang/vllm-omni.git` → branch/tag `cosmos3-nano-webui-mig-s2` = `697035018b70cef76b974a909d23371a9984c3f2`; S2 targeted tests 118 passed | verified-now |
| The public HF checkpoints are reachable, self-contained, and their metadata/license/revisions are recorded | `docs/session_4/hf_verification.md` + `evidence_map.md`: FP8 `4e181f99…`, NVFP4 `b5c9332e…`, license `openmdw-1.0`; base `nvidia/Cosmos3-Nano` (`other`); local shard sha256 == public LFS sha256 | verified-now |
| The curated import is complete (no hollow test pass) | `evidence_map.md`: 296 files; `compileall api`=0; torch-free `import app.main`=0; `pytest -m "not gpu"` = **486 passed** (`deterministic_checks.md` #4); excluded-module import grep clean | verified-now |
| CPU-only CI is configured and every step passes locally | `.github/workflows/ci.yml` (python+webui, `permissions: contents: read`, no secrets); `deterministic_checks.md` #2–#9 (ruff 0, pytest 486, vitest 209, build/lint/typecheck green); two schema-sync gates proven to fail on injected drift (S5) | verified-now |
| Local Docker/Compose renders clean with external, configurable mounts | `deterministic_checks.md` #10/#11 (fp8+nvfp4 `config` exit 0, 0-byte stderr); `evidence_map.md`: lean api + webui `docker build` exit 0; `:ro` bind mounts, repo-relative defaults, ports loopback-by-default | verified-now |
| README + community-health files are present, evidence-qualified, and links resolve | `evidence_map.md`/`handoff.md`: `README.md` 190 lines + logo; `LICENSE`/`SECURITY.md`/`CONTRIBUTING.md`/`CODE_OF_CONDUCT.md` + templates + `release_checklist.md`; 10 README relative links resolve to tracked files | verified-now |
| Licenses are separated three ways | `LICENSE` (MIT, repo code only) + README license section: repo MIT vs weights `openmdw-1.0` vs base `other` (`INV-7`, R-11) | verified-now |
| The X-1 auth path works end to end without changing the API shape | `handoff.md`/`evidence_map.md`: `webui/lib/proxy.ts` forwards `X-API-Key`; vitest **209 passed** incl. spoof-overwrite regression; `git diff -- api/ schemas/openapi.json` empty (`INV-9`) | verified-now |
| No release-blocking risk is unowned | `risk_register.md` reconciled this session (see `doc-reconciliation`); every release blocker Closed/Mitigated/routed with owner disposition | verified-now |

## Manual-gate-deferred (not shipped runtime behavior)

| Claim / surface | Status + public pointer | Tag |
|---|---|---|
| GPU inference for `t2v/t2v_audio/i2v/t2i`, `forward_dynamics`, `reasoning`, jobs-SSE, artifacts | **NOT-YET-RUN**; owner decision 1 (defer). `gpu-beta-limited-disposition` + `eval_seed_cases.md` `EV-MIG-GPU-*`. README marks each mode GPU-unverified (`INV-8`) | manual-gate-deferred |
| The default `vllm_omni` container loads the public FP8 **and** NVFP4 checkpoints (drift D1) | **Open beta limitation**; `docs/session_4/drift_report.md` D1; routed to the GPU session | manual-gate-deferred |
| vLLM-Omni image builds from the pinned commit and its serve entrypoint is correct | **Deferred** (heavy/CUDA); R-13; command in `release_checklist.md` §6 + handoff | manual-gate-deferred |
| The GitHub-hosted Actions run is green | **At-publish confirmation**; nothing pushed (`origin/main` = seed `c3983f7`). Local equivalents green (#2–#9). R-05 | manual-gate-deferred |
| Self-referential links/badges (CI status, `security/policy`, `discussions`) resolve; Private vulnerability reporting enabled | **At-publish**; resolve only once the repo is public. `release_checklist.md` §9 | manual-gate-deferred |
| `docker-socket-proxy` hardening + non-loopback exposure policy | **At-publish/hardening decision**; R-16 — privilege is confined + documented now (fixed-verb controller, loopback default, `X-API-Key` enforceable after X-1) | manual-gate-deferred |

## Integrity notes

- Every verified-now row cites a command run this session or a tracked/public artifact; no
  row rests on a private citation or on the implementation conversation.
- No deferred surface is presented as verified: GPU, drift D1, the GitHub-hosted CI run, and
  the at-publish links are explicitly tagged deferred.
- CPU-CI-green is stated as **locally green + configured**, with the GitHub-hosted run called
  out as the at-publish confirmation — the "CI green locally but runner unverified" failure
  mode is disclosed, not hidden.
