# Public Beta Release Checklist

Status: gate for `GATE-MIG-S8-BETA` (owner GO / NO-GO). Created in `MIG-S7`.
This checklist collects the pre-release checks. Runtime/GPU items are **manual
gates** — CPU CI does not cover them. Reference: `docs/project_contract.md` §4
(Gates), `docs/evidence_map.md`, `docs/risk_register.md`.

## 1. Scrub and safety (INV-1, INV-2)

- [ ] Private-reference scan clean over the whole tree:
      `uv run python tests/test_private_ref_scan.py` → 0 findings.
- [ ] No model weights, generated media, caches, or bulky archives tracked
      (`git ls-files | rg -i "\.(safetensors|pt|pth|ckpt|mp4|webm)$"` → empty).
- [ ] Weight-copy scan over `deploy/` clean (`make scan`).
- [ ] `.gitignore` excludes build/env/model artifacts; `git status` clean.

## 2. Licensing (INV-7, R-11)

- [ ] `LICENSE` (MIT) present and scoped to repo code only.
- [ ] README and `LICENSE` separate repo MIT from model weight licenses
      (`openmdw-1.0` for FP8/NVFP4; `other` for `nvidia/Cosmos3-Nano`).
- [ ] Third-party dependency licenses acknowledged (`docs/model_setup.md`).

## 3. Docs and claims (R-01, R-09)

- [ ] `README.md` non-empty; logo renders; beta / research-preview posture stated.
- [ ] Every runtime claim (GPU, FP8/NVFP4, RTX 5090, performance) is
      evidence-qualified or marked as a beta limitation — no unsupported
      production or performance claim (claim review over README + docs).
- [ ] All README relative links resolve to tracked files.
- [ ] Self-referential links/badges (CI status, `security/policy`, `discussions`)
      resolve once the repo is public — re-check after the repo is published.

## 4. Community hygiene (R-15)

- [ ] `SECURITY.md` routes vulnerabilities to a private channel and forbids
      public-issue disclosure.
- [ ] `CONTRIBUTING.md` mirrors CI and links the Code of Conduct.
- [ ] `CODE_OF_CONDUCT.md` present with a working enforcement contact.
- [ ] Issue templates + `config.yml` (`blank_issues_enabled: false`) + PR template
      present; templates request no secrets or private data.

## 5. CPU CI (GATE-MIG-S5-CI, R-10)

- [ ] `.github/workflows/ci.yml` passes on the release commit (push/PR):
      Python (ruff + `pytest -m "not gpu"` incl. schema + scrub gates) and WebUI
      (schema sync + build + lint + typecheck + test).
- [ ] No secrets, CUDA, or self-hosted runner introduced (`permissions: contents: read`).

## 6. Docker / Compose (GATE-MIG-S6-DOCKER)

- [ ] `docker compose -f deploy/docker-compose.fp8.yml config` and `…nvfp4…`
      render clean (exit 0, no unset-var warning, correct label).
- [ ] `api` (lean) and `webui` images build from public inputs.
- [ ] `deploy/vllm-omni.Dockerfile` builds from the pinned fork commit
      (`697035018b70…`) — **manual gate (heavy/CUDA), `MIG-S8`**.
- [ ] Confirm the vLLM-Omni image's real serve entrypoint (the `CMD` is a best-effort
      guess overridable via Compose `command:`).

## 7. Manual GPU gates (INV-6, INV-8, R-05) — `MIG-S8`

Record for each: hardware, driver/CUDA, checkpoint repo + revision, vLLM-Omni
commit, request shape, artifact metadata, pass/fail (`EV-MIG-GPU-*`).

- [ ] `t2v`, `t2v_audio`, `i2v`, `t2i` generation on the served checkpoint.
- [ ] `reasoning` on the BF16 base.
- [ ] `forward_dynamics` / action graft.
- [ ] jobs + SSE + artifact/trajectory retrieval end to end.
- [ ] Resolve drift **D1** (does the default `vllm_omni` container load the public
      FP8 **and** NVFP4 checkpoints).
- [ ] Any surface without passing GPU evidence is marked beta-limited in the README.

## 8. Hardening review (R-16)

- [ ] Docker-socket privilege reviewed; `COSMOS3_API_KEY` + loopback binding
      documented; `docker-socket-proxy` and non-loopback exposure policy decided.
- [ ] Auth path verified end to end (WebUI `X-API-Key` → API) with a key set (X-1 fixed).

## 9. Release mechanics

- [ ] Repo `About`, topics, and description set; unused GitHub features hidden.
- [ ] Tag + release notes summarizing beta scope and known limitations.
- [ ] Owner records **GO / NO-GO** with the evidence bundle.
