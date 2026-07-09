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
  + socket review disposition. Evidence: `docs/archive/phase-1/session_8/outputs/deterministic_checks.md`.
- **Deferred manual gate (owner decision — beta-limited):** §6 vLLM-Omni image build, §7 all
  GPU inference gates, drift D1.
- **At-publish (post-push):** §3 self-referential links/badges, §5 GitHub-hosted CI run, §9
  release mechanics incl. the owner's binding GO/NO-GO.
- **Recommendation:** GO for public beta / research preview, conditional on the standing GPU
  gate + the at-publish items (see `docs/archive/phase-1/session_8/outputs/gate_record.md`). Advisory —
  **owner ratifies.**

## GPU gate exercised (2026-07-08, post-GO)

Ran the deferred GPU gate on an RTX 5090 (sm_120, 32 GB). **T2I generation works end-to-end
for both FP8 and NVFP4** — direct on vLLM-Omni and full-stack through the api (`X-API-Key`
auth → job → orchestrator → artifact PNG). Per-item status in §6/§7. **Caveats (evidence is
partial and on a proxy image):**

- Image used was **`vllm-omni-local:c89089a4`** (a local build dated ≈ the pin commit
  `697035…`), **not** an image built from the pinned commit via the public
  `deploy/vllm-omni.Dockerfile` (which is **broken** — see §6). The exact-pinned-build path is
  still unproven; what is proven is that the fork code (near-pin) + the public checkpoints
  serve and generate.
- Both published checkpoints needed a local fix to load: the top-level
  `model.safetensors.index.json` is **stale** (references 7 non-existent
  `diffusion_pytorch_model-*` shards; the real weight is a single consolidated file). Removing
  it lets the container load — this is the precise nature of **drift D1 / R-03** (a
  published-checkpoint packaging bug, not a quant incompatibility). Small config/tokenizer
  files also arrived as unresolved git-LFS/Xet pointers on `git clone` and had to be fetched
  from HF's resolve endpoint (`hf download` avoids this).
- Only **T2I** (+ jobs + artifact + auth) is verified. `t2v`, `t2v_audio`, `i2v`,
  `forward_dynamics`, `reasoning` (BF16 base), and 720p **video** (peak VRAM > 32 GB) remain
  unrun.
- README per-mode markings can be upgraded from "GPU-unverified" to "T2I-verified" for FP8/NVFP4.

## GPU-S1 Dockerfile rework (2026-07-09)

Closed the build-half gap this section flagged above. `deploy/vllm-omni.Dockerfile`
now builds from public inputs only (`FROM vllm/vllm-openai:v0.24.0`, matching the
fork's own `docker/Dockerfile.cuda` pattern; fork installed by immutable commit
`697035018b70…` via `uv pip install`) — no `vllm/vllm-omni:cosmos3` prebuilt
involved. Verified live on the RTX 5090 (sm_120): the base tag passes a real bf16
CUDA-capability probe, the build completes in well under a minute (only
vllm-omni's incremental deps install — the base already ships torch/vLLM/CUDA),
and the rebuilt image serves `/v1/models` and generates a valid T2I artifact for
**both** FP8 and NVFP4 (exceeding this gate's "at least one" bar). Guardrails stay
on by default in the shipped image; **a bare `docker compose up` with no other
configuration will crash before serving** (`CosmosSafetyChecker` refuses to run
without the gated `nvidia/Cosmos-1.0-Guardrail` model/`HF_TOKEN`, which this
default does not provision — not a new constraint, the same flag was already
required for Phase-1's own proven GPU gate). This session's own smoke test used
an explicit `--no-guardrails` Compose override (undocumented in any tracked
file) for exactly that reason — full evidence, commands, and artifact metadata
in `docs/evidence_map.md` and `docs/session_1/`. `deploy/docker-compose.local-image.yml`
is deleted (owner disposition: drop, not keep as a documented convenience).

## GPU-S2 checkpoint index/LFS fix and re-pin (2026-07-09)

Closed archived Phase-1 R-03. Both `wfen/*` checkpoint repos shipped a stale
top-level `model.safetensors.index.json` (referencing 7 non-existent
shards) and forced small config/tokenizer files into LFS via blanket
extension rules, so a plain `git clone` left them as unresolved pointers.
Fixed at the source: the stale index is removed from both repos, and
`.gitattributes`/renormalize corrects LFS tracking to the owner's
size/type rule (large weights stay LFS; small plain-text files are regular
Git). A third, previously undocumented bug was also found and fixed:
`BIAS.md`/`EXPLAINABILITY.md`/`PRIVACY.md`/`SAFETY.md` (both repos) and 32
further NVFP4-side files were checking out as raw LFS-pointer text
regardless of `.gitattributes` state (no rule has ever matched `.md`;
NVFP4's text-extension rules were already removed pre-session without a
renormalize) — restored via direct LFS object fetch. FP8's dev-scratch
`_s2_*.md` files and NVFP4's `transformer/producer_provenance.json` have
the identical corruption and are deliberately left untouched (Owner
Decision 3). New revisions: FP8 `9bf5d6ae164688487bdb71947ccc6ebe70d12900`,
NVFP4 `5514c42b9759739f545e0d0dee453db8d8525fbc` — both independently
verified via a cache-isolated fresh `git clone` and `hf download` (weight
bytes excluded; not needed for this check). Every in-repo reference to the
pre-fix revisions is swept in the same session (`docs/evidence_map.md`,
this file, `docs/eval_seed_cases.md`, `docs/risk_register.md`,
`docs/model_setup.md`, `docs/handoff.md`). No large weight file was
affected (R-04 — verified empty diff for every large file across the fix).

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
      all local equivalents green (S8 #2–#9: ruff 0, pytest 486, vitest 209).
- [x] No secrets, CUDA, or self-hosted runner introduced (`permissions: contents: read`)
      (S5; re-read S8).

## 6. Docker / Compose (GATE-MIG-S6-DOCKER)

- [x] `docker compose -f deploy/docker-compose.fp8.yml config` and `…nvfp4…`
      render clean (exit 0, no unset-var warning, correct label) (S8 #10/#11).
- [x] `api` (lean) and `webui` images build from public inputs (S6).
- [x] `deploy/vllm-omni.Dockerfile` builds from the pinned fork commit (`697035018b70…`).
      **FIXED and verified (2026-07-09, `GPU-S1`):** rebuilt from
      `vllm/vllm-openai:v0.24.0` (public base with a build toolchain already present) +
      `uv pip install` of the immutable-pinned fork commit. Builds clean from public
      inputs only; no `vllm/vllm-omni:cosmos3` prebuilt involved. See the "GPU-S1
      Dockerfile rework" addendum above and `docs/evidence_map.md`.
- [x] vLLM-Omni serve entrypoint **confirmed (2026-07-08) and fixed in the image
      (2026-07-09, `GPU-S1`):**
      `vllm serve <checkpoint-dir> --omni --host 0.0.0.0 --port 8000 [--init-timeout 1800]
      [--no-guardrails]` (per the fork's `recipes/cosmos3/Cosmos3-Nano.md`). The
      Dockerfile's `CMD` now runs this directly (with `ENTRYPOINT []` cleared so it
      isn't appended to `vllm-openai`'s own `vllm serve` entrypoint) instead of the
      previously wrong `python3 -m vllm_omni.entrypoints.openai.api_server` guess.
      Verified serving both FP8 and NVFP4 T2I on the RTX 5090.

## 7. Manual GPU gates (INV-6, INV-8, R-05) — deferred (owner decision, beta-limited)

Record for each: hardware, driver/CUDA, checkpoint repo + revision, vLLM-Omni
commit, request shape, artifact metadata, pass/fail (`EV-MIG-GPU-*`). A valid run MUST use
vLLM-Omni `697035018b70…` + FP8 `9bf5d6ae1646…` / NVFP4 `5514c42b9759…` (`GPU-S2` revisions;
superseding the pre-fix `4e181f99…`/`b5c9332e…`) + BF16 base
`nvidia/Cosmos3-Nano` @ `fea6e03a…`. GPU marker run:
`COSMOS3_ENABLE_GPU_TESTS=1 uv run pytest -m gpu`; then the per-mode `EV-MIG-GPU-*` smokes.

- [x] **`t2i`** generation — **PASS (2026-07-08)** on FP8 **and** NVFP4, direct on vLLM-Omni
      (1024², ~3 s) and full-stack via the api (640², `precision:nvfp4`, artifact PNG). Proxy
      image (see top caveat).
- [ ] `t2v`, `t2v_audio`, `i2v` — **not run** (720p video peak VRAM > 32 GB; needs
      `--enable-layerwise-offload` or smaller size — separate test).
- [ ] `reasoning` on the BF16 base — **not run** (separate reasoner instance / BF16 base).
- [ ] `forward_dynamics` / action graft — **not run**.
- [x] jobs + artifact retrieval end to end — **PASS (2026-07-08)** via the api
      (`POST /v1/generation/t2i` → job `succeeded` → `GET /v1/jobs/{id}/artifact` = `200 image/png`).
      SSE `/events` + `/trajectory` not explicitly exercised.
- [x] Resolve drift **D1** — **characterized + resolved-for-serving (2026-07-08):** the
      `vllm_omni` container loads **both** public checkpoints (FP8 `W8A16`, NVFP4 `W4A16`) once
      the stale top-level `model.safetensors.index.json` is removed. D1 root cause = a
      published-checkpoint packaging bug (stale weight index), **not** a quant incompatibility.
      Owner follow-up: fix the HF repos' index (R-03).
- [ ] Any surface without passing GPU evidence is marked beta-limited in the README
      (**S7** — every mode GPU-unverified; **upgrade `t2i` FP8/NVFP4 to T2I-verified** after this run).

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
- [x] Owner records **GO** (ratified 2026-07-07) with the evidence bundle
      (`docs/archive/phase-1/session_8/outputs/**`) — public beta / research preview, GPU surface beta-limited.
