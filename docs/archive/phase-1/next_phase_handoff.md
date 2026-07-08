# Next-Phase Handoff — vLLM-Omni Image, HF Checkpoint Fix, Upstream Quant PR

Date: 2026-07-08 · Status: **blueprint input** (owner will write a phase blueprint, then
split into sessions). Deferred from the post-S8 GPU deployment debugging.

This captures the hard-won context so the next phase starts cold-but-informed. Three
tasks, deferred deliberately because two are outward-facing/irreversible and all three are
heavy. Owner decisions already made are marked **[decided]**.

## Context already established (post-GO GPU gate, 2026-07-08)

Verified on an RTX 5090 (sm_120, 32 GB): **T2I generation works end-to-end for both FP8 and
NVFP4** — direct on vLLM-Omni and full-stack through the api (`X-API-Key` → job → artifact).
Details + evidence live in `release_checklist.md` (§6/§7 + "GPU gate exercised"),
`session_8/outputs/gate_record.md`, `risk_register.md` (R-03/R-05/R-13), `model_setup.md`
(§7/§9), and `evidence_map.md`. Three things blocked a clean, reproducible deployment and
became the tasks below:

1. The public `deploy/vllm-omni.Dockerfile` does not build (used a prebuilt image as a
   stopgap).
2. The published `wfen/*` checkpoints don't clone/load cleanly (stale weight index + LFS
   layout).
3. The FP8/NVFP4 blockwise quant support lives only in the `fengwang/vllm-omni` fork.

The local stopgap used for the T2I proof — keep for reference, **do not ship**:
`deploy/docker-compose.local-image.yml` (points the `vllm-omni` service at a prebuilt image
+ the real `vllm serve … --omni` command).

---

## Task A — Build `deploy/vllm-omni.Dockerfile` from public inputs (no `vllm/vllm-omni:cosmos3`)

**Goal:** the public Dockerfile builds a working vLLM-Omni image from the pinned fork commit,
using only public inputs, so operators need no prebuilt image.

**Current state (broken):** `pip install --break-system-packages` is unsupported by the base
image's pip 22.0 (Ubuntu 22.04) → build dies at step 3/3; the `-runtime` CUDA base has no
build toolchain; and the `CMD` (`python3 -m vllm_omni.entrypoints.openai.api_server`) is the
wrong entrypoint.

**Recipe [from the fork's `docker/Dockerfile.cuda`] — the key insight:** the fork does **not**
compile from a raw CUDA-devel base. It is `FROM vllm/vllm-openai:v0.24.0` (public upstream base
that already ships torch + CUDA + vLLM) then `uv pip install .` of the vLLM-Omni package. So
"from the ground up, avoiding the cosmos3 prebuilt" =
- `FROM vllm/vllm-openai:<version>` (public base; verify it supports **sm_120 / Blackwell** —
  the working proxy image used CUDA 13.0; match what the pinned fork commit needs),
- install the fork **by immutable commit** `697035018b70cef76b974a909d23371a9984c3f2` (INV-3),
  e.g. `uv pip install "git+https://github.com/fengwang/vllm-omni.git@697035…"` (or COPY the
  pinned checkout + `uv pip install .`),
- fix the serve entrypoint to **`vllm serve <model-dir> --omni --host 0.0.0.0 --port 8000`**
  (the confirmed entrypoint), or leave `CMD` out and let Compose `command:` own it (current
  pattern). No weights baked (INV-2).

**Done when:** `docker compose -f deploy/docker-compose.fp8.yml build vllm-omni` builds from
public inputs (no cosmos3 prebuilt), `up` serves `/v1/models`, and a T2I request generates a
PNG on the 5090. Then drop the `docker-compose.local-image.yml` stopgap (or keep only as a
"reuse a prebuilt image" convenience) and update `release_checklist.md` §6.

**Gotchas:** confirm the `vllm/vllm-openai` tag's CUDA/torch matches the fork commit and
supports sm_120; the build is heavy (~15–40 min) and iterative; `--no-guardrails` needs the
fork build (present at the pin); guardrails-on needs the gated `nvidia/Cosmos-1.0-Guardrail`
+ `HF_TOKEN`.

---

## Task B — Fix the published `wfen/*` HF checkpoints (index + LFS layout)

**[decided] Scope:** (1) **remove** the stale top-level `model.safetensors.index.json`;
(2) fix `.gitattributes`/LFS tracking per the rule below. **Not** this pass: drift-D3
dev-scratch cleanup (`_s2_*.md`, `producer_provenance.json`, `load_quantized.py`,
`assets/FP8-Examples/…`, benchmark PNGs) — owner chose index+LFS only.

**[decided] LFS rule:** files **>10 MB** OR **non-plain-text** (`.safetensors`, `.png`,
`.jpg/.jpeg`, `.mp3`, `.mp4`, `.webm`, `.pt/.pth/.ckpt`, …) → **LFS**; small plain-text
(`.json`, `.txt`, `.md`, `.jinja`, tokenizer files) → **regular git** (so they resolve on
plain `git clone`).

**Root cause (both repos, `wfen/Cosmos3-Nano-FP8-Blockwise` + `…-NVFP4-Blockwise`):**
- The top-level `model.safetensors.index.json` references 7 non-existent shards
  (`transformer/diffusion_pytorch_model-0000N-of-00007.safetensors`); the real transformer
  weight is a single consolidated `transformer/{diffusion_pytorch_model,model}.safetensors`.
  A diffusers pipeline loads per-component, so this top-level index shouldn't exist →
  **remove it** (verified: the loader then uses the consolidated files).
- The small config/tokenizer/`.md` files are LFS-tracked, so a `git clone` (with HF's Xet
  backend) leaves them as **unresolved pointers** that fail to parse. Migrating them out of
  LFS (regular git) fixes clone-then-load.

**Approach (write access confirmed):** fresh clone each repo → `git rm` the top-level index →
rewrite `.gitattributes` per the rule → migrate the small files out of LFS
(`git lfs migrate export --include="*.json,*.txt,*.md,*.jinja,tokenizer*"` or a
`.gitattributes` change + `git add --renormalize .`), keeping the big weights in LFS → commit
+ push. **Verify with a fresh `git clone` AND `hf download`** that config files are real and
the checkpoint loads + T2I in the **Task A** docker with **no** manual index-removal or
pointer-fetching.

**Critical follow-on:** fixing each repo produces **new revisions**, so the pinned revisions
`4e181f996abf…` (FP8) / `b5c9332efbae…` (NVFP4) will change. **Update every pinned-revision
reference** in the WebUI repo after the fix: `docs/model_setup.md` §1, `docs/evidence_map.md`,
`docs/session_8/outputs/gate_record.md` "must match" list, `docs/eval_seed_cases.md`,
`docs/release_checklist.md` §7.

**Gotchas:** don't rewrite the big weights into non-LFS (history bloat); HF push uses the
git-lfs/Xet setup; test with a *fresh* clone (not the existing local one, which already has
local fixes applied); D3 dev-scratch remains (out of scope) — note it in the model card if
desired.

---

## Task C — Upstream PR: FP8/NVFP4 blockwise quant support → `vllm-project/vllm-omni`

**[decided] Scope:** contribute the **model-agnostic quant loaders only**, decoupled from
Cosmos3-specific code; must not break existing functionality.

**Candidate files (from the fork at pin `697035…`; isolate + rebase onto upstream `main`):**
- `vllm_omni/quantization/fp8_blockwise_w8a16.py`
- `vllm_omni/quantization/nvfp4_blockwise.py`
- registration hooks in `vllm_omni/quantization/{__init__.py, factory.py, component_config.py}`
- `vllm_omni/diffusion/model_loader/checkpoint_adapters/{modelopt.py, modelopt_native.py,
  modelopt_native_fp8_w8a16.py, modelopt_native_nvfp4.py}`
- the NVFP4 W4A4 `weight_scale` NaN-clamp hunk in `vllm_omni/patch.py` (isolate the relevant
  part only)

**Process (per fork `CONTRIBUTING.md` → readthedocs contributing + the `precheck-pr` skill):**
1. **Verify upstream state first** — does `vllm-project/vllm-omni` `main` already carry any of
   these quant methods / the ModelOpt-native detection? Contribute only the **missing** pieces,
   decoupled from Cosmos3-specific loader code, so the PR does not require the whole model.
2. **Fork/branch:** push a feature branch to `fengwang/vllm-omni` (fork of upstream); open the
   PR against `vllm-project/vllm-omni` `main`. Rebase the isolated quant commits onto current
   upstream `main` (the fork is at the pin; upstream has advanced).
3. **Pre-submit gate:** run the repo's **`precheck-pr` skill** (quick then full) —
   `.claude/skills/precheck-pr/SKILL.md`; it validates PR-title prefix (e.g. `[Kernel]` /
   `[Core]` / `[Misc]` — quant linear methods are likely `[Kernel]`), runs the code-quality
   sweep, and checks dead code / accuracy / benchmark-claim integrity. It never posts.
4. **CI + hygiene:** pass `.github/workflows/{pre-commit,build_wheel}.yml`; `.pre-commit-config.yaml`
   clean; **DCO sign-off** (`git commit -s`); add unit tests for the quant methods; confirm no
   regression in existing (non-quant / other-model) paths.

**Done when:** a clean, decoupled, DCO-signed PR is open on `vllm-project/vllm-omni` adding
FP8-blockwise-W8A16 + NVFP4-blockwise-W4A16 support, `precheck-pr` clean, CI green.

**Gotchas / why its own session:** this is a public contribution to a major project
(attributed to the owner) → needs plan mode, careful decoupling from Cosmos3 code, upstream
CLA/DCO, and maintainer review. Highest-risk, most-outward task.

---

## Dependencies, suggested split, prerequisites

**Dependencies:** A and B are validated **together** (B's clean-clone test runs in A's docker);
each can be *done* independently. C is independent of A/B (shares only the quant-loader
understanding) and can run in parallel.

**Suggested session split (owner's blueprint decides — not prescriptive):**
- **α — Task A:** Dockerfile from-source build (GPU/build; self-contained; most context here).
- **β — Task B:** HF checkpoint fix + re-pin the repo docs (needs HF write creds; changes pins).
- **γ — Task C:** upstream quant PR (needs upstream-state verification + CONTRIBUTING compliance
  + owner authority for the outward PR).
- **Joint validation after α+β:** fresh `hf download` @ new revisions → load + T2I (ideally also
  `t2v` at a small size) on the 5090, via the from-source docker, no manual workarounds.

**Prerequisites / authority:**
- RTX 5090 host (present) for build + validation; ~tens of GB disk + network for base image and
  checkpoints.
- HF write access to `wfen/*` (owner-confirmed) + local `git lfs` / Xet + `hf` auth.
- Upstream PR: DCO sign-off; a `fengwang/vllm-omni` fork of `vllm-project/vllm-omni` (exists);
  confirm any CLA.

**Reference pins/paths (as of 2026-07-08; FP8/NVFP4 pins change after Task B):**
- vLLM-Omni fork commit: `697035018b70cef76b974a909d23371a9984c3f2`
- FP8 `wfen/Cosmos3-Nano-FP8-Blockwise` @ `4e181f996abf03f3425298ef692e6e5e56fd46a4`
- NVFP4 `wfen/Cosmos3-Nano-NVFP4-Blockwise` @ `b5c9332efbaefa72c99890b1b1150da12ca9256c`
- BF16 base `nvidia/Cosmos3-Nano` @ `fea6e03ac3d7884b4105ed8ee79fc480fca70965`
- Serve entrypoint: `vllm serve <checkpoint-dir> --omni --host 0.0.0.0 --port 8000
  [--init-timeout 1800] [--no-guardrails]`; api T2I dims ∈ `{256,480,640,720,960,1280}`.
- Fork recipe/Dockerfile references: `docker/Dockerfile.cuda`,
  `recipes/cosmos3/Cosmos3-Nano.md` (in the local `fengwang/vllm-omni` checkout).

**Not carried into scope:** drift D3 dev-scratch cleanup on the HF repos; `t2v`/`t2v_audio`/
`i2v`/`forward_dynamics`/`reasoning` GPU validation; 720p video (peak VRAM > 32 GB → needs
`--enable-layerwise-offload` or smaller size). Track these as separate follow-ups.
