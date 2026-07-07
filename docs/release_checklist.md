# Public Beta Release Checklist

Status: gate for `GATE-MIG-S8-BETA` (owner GO / NO-GO). Created in `MIG-S7`.
This checklist collects the pre-release checks. Runtime/GPU items are **manual
gates** — CPU CI does not cover them. Reference: `docs/project_contract.md` §4
(Gates), `docs/evidence_map.md`, `docs/risk_register.md`.

## MIG-S8 gate status (2026-07-07)

Reviewed and reconciled this session (branch `session-8`, not pushed). Legend: **[x]** =
verified now with evidence; **[ ]** = manual gate or at-publish (resolves after the repo is
public or after the GPU session).

- **Verified now:** §1 scrub/safety, §2 licensing, §3 docs/claims (except self-referential
  links), §4 hygiene, §5 "no secrets/CUDA", §6 compose render + api/webui build, §8 auth path
  + socket review disposition. Evidence: `docs/session_8/outputs/deterministic_checks.md`.
- **Deferred manual gate (owner decision — beta-limited):** §6 vLLM-Omni image build, §7 all
  GPU inference gates, drift D1.
- **At-publish (post-push):** §3 self-referential links/badges, §5 GitHub-hosted CI run, §9
  release mechanics incl. the owner's binding GO/NO-GO.
- **Recommendation:** GO for public beta / research preview, conditional on the standing GPU
  gate + the at-publish items (see `docs/session_8/outputs/gate_record.md`). Advisory —
  **owner ratifies.**

## 1. Scrub and safety (INV-1, INV-2)

- [x] Private-reference scan clean over the whole tree:
      `uv run python tests/test_private_ref_scan.py` → **0 findings** (S8 #12).
- [x] No model weights, generated media, caches, or bulky archives tracked
      (`git ls-files | rg -i "\.(safetensors|pt|pth|ckpt|mp4|webm)$"` → **empty**, S8 #13/#14).
- [x] Weight-copy scan over `deploy/` clean (`make scan`) — clean at S6; tree weight scan
      clean at S8 (#14).
- [x] `.gitignore` excludes build/env/model artifacts; `git status` clean (S7; S8 #1
      `## session-8`, clean tree).

## 2. Licensing (INV-7, R-11)

- [x] `LICENSE` (MIT) present and scoped to repo code only (S7).
- [x] README and `LICENSE` separate repo MIT from model weight licenses
      (`openmdw-1.0` for FP8/NVFP4; `other` for `nvidia/Cosmos3-Nano`) (S7).
- [x] Third-party dependency licenses acknowledged (`docs/model_setup.md`) (S7).

## 3. Docs and claims (R-01, R-09)

- [x] `README.md` non-empty; logo renders; beta / research-preview posture stated (S7).
- [x] Every runtime claim (GPU, FP8/NVFP4, RTX 5090, performance) is
      evidence-qualified or marked as a beta limitation — no unsupported
      production or performance claim (S7 claim review; S8 evidence review).
- [x] All README relative links resolve to tracked files (S7: 10/10).
- [ ] Self-referential links/badges (CI status, `security/policy`, `discussions`)
      resolve once the repo is public — **at-publish** re-check.

## 4. Community hygiene (R-15)

- [x] `SECURITY.md` routes vulnerabilities to a private channel and forbids
      public-issue disclosure (S7).
- [x] `CONTRIBUTING.md` mirrors CI and links the Code of Conduct (S7).
- [x] `CODE_OF_CONDUCT.md` present with a working enforcement contact (S7).
- [x] Issue templates + `config.yml` (`blank_issues_enabled: false`) + PR template
      present; templates request no secrets or private data (S7).

## 5. CPU CI (GATE-MIG-S5-CI, R-10)

- [ ] `.github/workflows/ci.yml` passes on the release commit (push/PR):
      Python (ruff + `pytest -m "not gpu"` incl. schema + scrub gates) and WebUI
      (schema sync + build + lint + typecheck + test). **At-publish** — nothing pushed;
      all local equivalents green (S8 #2–#9: ruff 0, pytest 485, vitest 209).
- [x] No secrets, CUDA, or self-hosted runner introduced (`permissions: contents: read`)
      (S5; re-read S8).

## 6. Docker / Compose (GATE-MIG-S6-DOCKER)

- [x] `docker compose -f deploy/docker-compose.fp8.yml config` and `…nvfp4…`
      render clean (exit 0, no unset-var warning, correct label) (S8 #10/#11).
- [x] `api` (lean) and `webui` images build from public inputs (S6).
- [ ] `deploy/vllm-omni.Dockerfile` builds from the pinned fork commit
      (`697035018b70…`) — **manual gate (heavy/CUDA), deferred to the GPU session**.
      Command: `docker compose -f deploy/docker-compose.fp8.yml build vllm-omni`
      (image `cosmos3-nano-vllm-omni:local`; or
      `docker build -f deploy/vllm-omni.Dockerfile -t cosmos3-nano-vllm-omni:local .`).
- [ ] Confirm the vLLM-Omni image's real serve entrypoint (the `CMD` is a best-effort
      guess overridable via Compose `command:`) — **manual gate, deferred**.

## 7. Manual GPU gates (INV-6, INV-8, R-05) — deferred (owner decision, beta-limited)

Record for each: hardware, driver/CUDA, checkpoint repo + revision, vLLM-Omni
commit, request shape, artifact metadata, pass/fail (`EV-MIG-GPU-*`). A valid run MUST use
vLLM-Omni `697035018b70…` + FP8 `4e181f99…` / NVFP4 `b5c9332e…` + BF16 base
`nvidia/Cosmos3-Nano` @ `fea6e03a…`. GPU marker run:
`COSMOS3_ENABLE_GPU_TESTS=1 uv run pytest -m gpu`; then the per-mode `EV-MIG-GPU-*` smokes.

- [ ] `t2v`, `t2v_audio`, `i2v`, `t2i` generation on the served checkpoint.
- [ ] `reasoning` on the BF16 base.
- [ ] `forward_dynamics` / action graft.
- [ ] jobs + SSE + artifact/trajectory retrieval end to end.
- [ ] Resolve drift **D1** (does the default `vllm_omni` container load the public
      FP8 **and** NVFP4 checkpoints).
- [ ] Any surface without passing GPU evidence is marked beta-limited in the README
      (**done at S7** — every mode marked GPU-unverified; re-affirm after the GPU run).

## 8. Hardening review (R-16)

- [x] Docker-socket privilege reviewed; `COSMOS3_API_KEY` + loopback binding
      documented (S6/S7). **`MIG-S8` disposition:** confined fixed-verb controller +
      loopback default accepted for beta; `docker-socket-proxy` + non-loopback exposure
      policy = **post-beta hardening** (owner-dispositioned).
- [x] Auth path verified end to end (WebUI `X-API-Key` → API) with a key set (X-1 fixed;
      S7 vitest 209 incl. spoof-overwrite regression).

## 9. Release mechanics — at-publish (owner)

- [ ] Repo `About`, topics, and description set; unused GitHub features hidden.
- [ ] Enable GitHub **Private vulnerability reporting** (Settings → Code security) so
      `SECURITY.md`'s advisory flow and the issue-template security redirect resolve.
- [ ] Tag + release notes summarizing beta scope and known limitations.
- [ ] Owner records **GO / NO-GO** with the evidence bundle (`docs/session_8/outputs/**`).
