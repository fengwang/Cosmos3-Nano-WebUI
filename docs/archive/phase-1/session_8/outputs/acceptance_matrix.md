# Acceptance Matrix - MIG-S8 Release Gate

Date: 2026-07-07 · Gate: `GATE-MIG-S8-BETA`

One row per PRD (`docs/prd.md` §4) requirement. Verdicts: **PASS** (verified with public
evidence now), **BETA-LIMITED** (deferred manual gate; unverified surface marked, `INV-8`),
**NO-GO** (release blocker). SHOULD-level rows are marked and are not release blockers.

## Functional requirements

| Req | Level | Requirement (short) | Owning gate | Public evidence | Verdict |
|---|---|---|---|---|---|
| FR-1 | MUST | Migration contract pack exists (`prd`, `project_contract`, `evidence_map`, `risk_register`, `eval_seed_cases`, `session_{1..8}.md`+`.yaml`) | S1–S8 | All present under `docs/` (this tree); `session_{1..8}.md` + `session_{1..8}_contract.yaml` present | **PASS** |
| FR-2 | MUST | Public docs/files free of private hosts, paths, codenames, secrets, tokens, local-only artifacts | S1/S3/S7/S8 | `deterministic_checks.md` #12 (scanner clean over `api/webui/tests/schemas/docs/.github`) + #15 (broad-scan human gate clean) | **PASS** |
| FR-3 | MUST | Rebased `vllm-omni` patch line published to the fork, pinned by public commit/tag | S2 | `evidence_map.md`: branch/tag `cosmos3-nano-webui-mig-s2` → `697035018b70…` (public `git ls-remote`); S2 targeted tests 118 passed | **PASS** (pin public; image build/GPU = S8 gate) |
| FR-4 | MUST | Curated WebUI/API import (source, schemas, tests, tools, docs; exclude archives/caches/weights) | S3 | `evidence_map.md`: 296 files imported; `compileall api`=0, torch-free `import app.main`=0, `pytest -m "not gpu"` clean; scans clean | **PASS** |
| FR-5 | MUST | Verify HF FP8/NVFP4 artifacts before beta: repo IDs, license, layout, compatibility expectations, drift | S4 | `evidence_map.md` + `docs/session_4/hf_verification.md`: revisions FP8 `4e181f99…`/NVFP4 `b5c9332e…`, license `openmdw-1.0`, self-contained, local==public sha; drift D1–D4 documented (D3 = external HF dev-scratch files, owner follow-up) | **PASS** (metadata verified + drift documented) |
| FR-6 | MUST | CPU-only GitHub Actions for lint/tests/schema/render checks | S5 | `.github/workflows/ci.yml` (python+webui jobs, `permissions: contents: read`); local equivalents green (`deterministic_checks.md` #2–#9); two schema-sync gates proven to fail on drift (S5) | **PASS** (config verified + locally green; GitHub-hosted run = at-publish, checklist §5) |
| FR-7 | MUST | Local-build Docker/Compose with configurable checkpoint paths; no private model paths | S6 | `deterministic_checks.md` #10/#11 (compose fp8/nvfp4 render exit 0, 0-byte stderr); `evidence_map.md`: api(258MB)+webui(287MB) build, external `:ro` mounts, repo-relative defaults | **PASS** (render+lean builds; vllm-omni image build = S8 gate) |
| FR-8 | MUST | README + project hygiene present (pitch, quickstart, weights setup, limitations, licenses, security, contributing, templates, checklist) | S7 | `evidence_map.md`/`handoff.md`: `README.md` (190 lines), `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue/PR templates, `docs/release_checklist.md`; 10 README links resolve | **PASS** |
| FR-9 | MUST | Before beta, run+record manual GPU validation for the full surface **OR explicitly mark unverified surface beta-limited** | S8 | Owner decision 1 (defer GPU); `gpu-beta-limited-disposition` spec + `gate_record.md`; README marks each mode GPU-unverified (S7). Requirement's beta-limited branch is satisfied | **BETA-LIMITED** (satisfied via the explicit beta-limited branch; GPU run is the standing manual gate) |
| FR-10 | MUST | No legacy plain vLLM / TensorRT-LLM submodules unless a public runtime need is recorded | S3 | `evidence_map.md`/R-07: `submodules/` + `api/engines/trtllm/` excluded; torch-free `import app.main` works; no `trtllm`/`tensorrt` reference remains | **PASS** |
| FR-11 | SHOULD | Keep the first beta branch history clean/curated | S3 | R-12: curated allowlist copy, fresh per-area commits on `session-3`; no private git history imported | **PASS** (SHOULD) |
| FR-12 | SHOULD | Evidence-qualified README language for RTX 5090/FP8/NVFP4 | S7 | R-09: README carries beta banner, per-mode GPU-unverified markers, no perf/production claim, links `evidence_map.md` | **PASS** (SHOULD) |

## Non-functional requirements

| Req | Level | Requirement (short) | Owning gate | Public evidence | Verdict |
|---|---|---|---|---|---|
| NFR-1 | MUST | No secret/token/private host/path/model weight/cache/large artifact committed | S1/S3/S7/S8 | `deterministic_checks.md` #12–#15 (scans clean); `.gitignore` hardened (S7); no tracked weight/media | **PASS** |
| NFR-2 | MUST | Every release-blocking recommendation has an evidence row or is speculative with a re-verification gate | S8 | `evidence_review.md` (each claim → public evidence row); `risk_register.md` reconciled — no unowned release blocker (see `doc-reconciliation`) | **PASS** |
| NFR-3 | MUST | First milestone usable without private network access | S3/S6 | Public HF repos + public fork pin + local build; CPU CI needs no private net (`deterministic_checks.md` #2–#11) | **PASS** (structural; GPU runtime = deferred gate) |
| NFR-4 | MUST | Docker/README setup works with configurable local checkpoint dirs from public HF repos | S6/S7 | `deterministic_checks.md` #10/#11; external `:ro` bind mounts + repo-relative defaults; `docs/model_setup.md` env surface | **PASS** |
| NFR-5 | MUST | CPU CI failures classified before fixed (env/dep/test/source/schema/drift) | S5/S8 | Failure-Arbiter precedent (S5 FA-2, S6 FA-1, S7); this session's checks had 0 failures; `failure_arbiter.md` policy in place | **PASS** (policy + precedent; no failure to classify this session) |
| NFR-6 | MUST | GPU checks record hardware, driver/CUDA, checkpoint repo+revision, vLLM-Omni commit, request shape, artifact metadata, result | S8 | Evidence-field template in `eval_seed_cases.md` "Evidence Fields"; `gpu-beta-limited-disposition` records the required fields; **no GPU run performed** (deferred) | **BETA-LIMITED** (recording template exists; actual records are the deferred manual gate) |

## Summary

- **16 MUSTs:** 14 PASS, 2 BETA-LIMITED (FR-9, NFR-6 — the GPU surface, marked beta-limited
  per owner decision + `INV-8`), **0 NO-GO**.
- **2 SHOULDs:** both PASS.
- No PASS rests on private evidence. No acceptance bar was lowered: FR-9/NFR-6 are recorded
  BETA-LIMITED (not PASS) with the standing manual gate, and FR-9's own text permits the
  beta-limited branch.
- Release-recommendation input: every PRD MUST is covered and none is NO-GO → the GO rule's
  MUST-coverage clause is met (final verdict in `gate_record.md`, pending the reconciliation
  check that no release-blocking risk is unowned).
