# GPU-S2 Brainstorming — HF Checkpoint Index/LFS Fix and Re-Pin Sweep

Date: 2026-07-09
Contract: `docs/session_2_contract.yaml`
Status: Approved by owner (Feng), proceeding to proposal/design/specs/tasks/plan.

## Context Explored

- Read `docs/prd.md`, `docs/session_2.md`, `docs/session_2_contract.yaml`,
  `docs/project_contract.md`, `docs/evidence_map.md`, `docs/model_setup.md`,
  `docs/release_checklist.md`, `docs/eval_seed_cases.md`,
  `docs/risk_register.md`, `docs/handoff.md`.
- Repo state at start: clean, branch `GPU-S1` at tip `fe3d4c3`
  ("fix blast radius"), not yet merged into `phase-2`. `GATE-GPU-S1-DOCKERFILE`
  is closed per `docs/handoff.md`.
- Environment check (all green): `git-lfs` 3.7.1, `hf` CLI 1.21.0,
  `huggingface_hub` 1.21.0 (Python), `git` 2.54.0. Network egress to
  `huggingface.co` works (HTTP 200). `HF_TOKEN` is set (`~/.cache/huggingface/token`
  present); `hf auth whoami` and `ssh -T git@hf.co` both resolve to the `wfen`
  account — push access to both target repos is live from this sandbox.
  Disk is not a constraint (429G on `/data`, 1.2T on `/workspace`).
- Inspected the live checkpoint state directly via pre-existing local clones at
  `/data/models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise` (real `git@hf.co:wfen/...`
  remotes, HEAD `4e181f9…`/`b5c9332…` matching the documented pins exactly):
  - Confirmed the stale-index bug as documented: a top-level
    `model.safetensors.index.json` (already locally renamed to
    `.stale-bak` as the known workaround; `git status` shows it as
    `D model.safetensors.index.json` / `?? model.safetensors.index.json.stale-bak`,
    uncommitted).
  - Read both repos' `.gitattributes` and `git lfs ls-files` output in full.
    Both force **every** `.json`/`.py`/`.txt`/`.jinja` file into LFS via
    blanket extension patterns, regardless of size — dozens of small files
    (`config.json`, `checkpoint.json` at 2 bytes, `load_checkpoint.py`,
    `load_quantized.py`, `chat_template.json`, every `assets/*.json` fixture,
    NVFP4's `producer_provenance.json`, etc.) are incorrectly LFS-tracked.
    Only `text_tokenizer/tokenizer.json` (11.4 MB, over the 10 MB line) has a
    deliberate standalone override — that one is already correct and stays.
    `model.safetensors.index.json` itself and `video_preprocessor_config.json`
    are, by accident, already plain git blobs (committed before the blanket
    `*.json` rule existed) — direct proof the "rewrite order" failure mode
    named in the contract's `failure_modes_to_watch` has already happened
    once in this repo's history.
  - Confirmed the actual weight layout: FP8's `transformer/` has a single
    consolidated `diffusion_pytorch_model.safetensors` (~19.5 GB) +
    `modelopt_state.pt`; NVFP4's has `model.safetensors` (~14.7 GB) +
    `nvfp4_blockwise_mixed_v1.json` + `producer_provenance.json`. Neither has
    a second index anywhere else in the tree — the fix is exactly the
    top-level file, matching `docs/model_setup.md` §9 and the D1 drift
    report.
  - Found extra local directories beyond the live clones: `*-dist` (flat
    snapshots, no `.git`, with materially more content than the live repos —
    full `README.md`, `SAFETY.md`, `quantization_config.json`, a `reasoner/`
    subdir for NVFP4) and `*-local` (a git clone with older, divergent
    history — `initial commit` → `initialize Blockwise FP8 quantization
    model` → `lfs track files more than 10M` — and an empty working tree).
    Owner confirmed (see Q&A) these are stale leftovers, not inputs to this
    session.
  - Found a directly reusable precedent:
    `docs/archive/phase-1/session_4/probes/verify_hf_checkpoints.py`, a
    torch-free, functional-core/imperative-shell probe that inspects these
    same two repos via `HfApi` manifest metadata (file list, sizes, LFS
    sha256) without downloading large blobs, reusing
    `tools/checkpoint_prep/safetensors_io.py:parse_header` (confirmed still
    live at the top level, not archived).
- Confirmed git identity used for prior pushes to both `wfen/*` repos is
  `Feng <wang_feng@live.com>` (matches this sandbox's global git config) — no
  identity change needed.
- Confirmed `GPU-S1` is not merged into `phase-2`, and already touched several
  of the same docs `GPU-S2` must re-pin (`evidence_map.md`,
  `release_checklist.md`, `eval_seed_cases.md`, `risk_register.md`,
  `handoff.md`) — a real branch-topology decision, not just a formality.

## Clarifying Questions and Answers

1. **Branch base** — `GPU-S1` isn't merged into `phase-2` yet and already
   touched several of the same docs files this session must re-pin. Branch
   off `GPU-S1`'s tip, off `phase-2` fresh, or merge `GPU-S1` into `phase-2`
   first?
   → **Off `GPU-S1`'s tip** (`fe3d4c3`). Inherits `GPU-S1`'s already-updated
   docs, avoids duplicate merge conflicts later.
2. **Push execution mode** — SSH and `HF_TOKEN` auth to the `wfen` account
   both work from this sandbox. Push here with a gate, or prepare-only and
   hand off?
   → **I push, gated per-repo.** Full clone→fix→verify cycle happens in this
   session; a discrete, explicit "push now?" go/no-go is required
   immediately before each literal `git push` — separately for FP8 and for
   NVFP4 — even though the overall plan is already approved.
3. **Local `*-dist`/`*-local` directories** — stale leftovers to ignore, or
   relevant content to fold in?
   → **Ignore both.** Treat them as stale local leftovers from earlier work;
   do fresh clones from the hub for the actual fix. Matches the contract's
   existing scope decision (dev-scratch cleanup / new content is out of
   scope this pass).
4. **LFS-fix scope re: dev-scratch files** — the blanket `.gitattributes`
   rule covers dev-scratch paths too (`assets/FP8-Examples/**`, NVFP4's
   `producer_provenance.json`, etc.); fixing it flips those files' storage
   mechanism (LFS pointer → regular git blob) even though "dev-scratch
   cleanup" is out of scope this session. Apply the fix repo-wide, or exclude
   dev-scratch paths?
   → **Repo-wide fix.** Every small plain-text file moves out of LFS,
   including inside dev-scratch areas. Content, paths, and presence of those
   files stay 100% untouched — only the storage mechanism changes, keeping
   `.gitattributes` internally consistent.

## Approaches Considered

**LFS-tracking fix mechanism:**
- **Approach A (chosen):** Trim `.gitattributes` to remove the blanket
  `*.json`/`*.py`/`*.txt`/`*.jinja` LFS rules (keep the genuine binary
  patterns — `*.safetensors`, `*.pt`, `*.pth`, `*.ckpt`, `*.mp4`, `*.png`,
  `*.jpg`, etc. — plus the size-justified `text_tokenizer/tokenizer.json`
  override), then `git add --renormalize .` in one additive commit. No
  history rewrite, no force-push.
- **Approach B (rejected):** `git lfs migrate export --include=<patterns>` —
  rewrites all history and needs a force-push; larger blast radius for the
  exact failure mode R-04 names (accidentally de-LFS'ing a large weight
  file).
- **Approach C (rejected):** Per-file `.gitattributes` overrides instead of
  removing the blanket extension rules. Same end state but fragile — a new
  small file added later would silently regress back into LFS.

**Verification depth ("the checkpoint loads"):**
- **Approach A (chosen):** `GIT_LFS_SKIP_SMUDGE=1` for the working clone —
  the fix never touches large-file bytes, so they're never needed locally.
  For fresh-clone/`hf download` verification, extend the Phase-1 `HfApi`
  probe pattern: confirm small files resolve as real content (not LFS
  pointers) via manifest + LFS-sha metadata, confirm the top-level index is
  gone, confirm the transformer dir has no dangling shard references — all
  without pulling the ~24-27 GB of tensor bytes per repo. Full GPU
  functional load+generate remains `GPU-S3`'s job, not duplicated here.
- **Approach B (fallback, not needed unless A is ambiguous):** Full
  `hf download` of every file plus a functional load attempt in this
  session.

**Execution order (chosen):** FP8 fully first — clone, fix, local verify,
go-ahead, push, independent fresh-clone verify — confirm the recipe end to
end, then replay identically for NVFP4.

**R-02 mitigation, documenting the revision change (chosen):** Record the
revision bump in this repo's `docs/risk_register.md` R-02 row (already in
blast radius) rather than editing either HF repo's own README/model card —
keeps the external blast radius to exactly index+LFS, consistent with Q3's
answer not to fold in extra HF-side content this pass.

## Design Decisions Reached

1. Branch `GPU-S2` off `GPU-S1`'s tip (`fe3d4c3`) — done.
2. All external-repo work happens in fresh clones under the scratchpad
   directory, never reusing `/data/models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise*`
   — those are pre-existing, already-modified local copies, exactly the
   "already-patched checkout" the contract says not to rely on for
   verification.
3. New verification probe at `docs/session_2/probes/`, functional-core /
   imperative-shell: pure "is this manifest/`.gitattributes` correct"
   calculations separated from the `HfApi`/git actions that fetch the
   evidence, reusing `tools/checkpoint_prep/safetensors_io.py:parse_header`
   (read-only import, no edits to `tools/`).
4. Push sequencing: verify locally, then a discrete "push FP8 now?" go/no-go
   immediately before that literal `git push`, independently fresh-verify,
   then repeat with its own discrete go/no-go for NVFP4.
5. Interpretation recorded for the record: "LFS tracking fix" scope is
   repo-wide, including dev-scratch paths' storage mechanism; "dev-scratch
   cleanup out of scope" means their content/paths/presence stay untouched,
   not that their LFS mechanism is frozen inconsistent.
6. Sweep: the contract's literal `rtk rg -n "4e181f99|b5c9332e" .`, plus
   explicit checks of `model_setup.md` §1, `evidence_map.md`,
   `release_checklist.md` §7, `eval_seed_cases.md`, `risk_register.md`, and
   `handoff.md`.
7. Commit cadence: commit at each clean task checkpoint, matching repo
   history and `GPU-S1` precedent.

## Outcome

Owner approved this direction ("it is good. proceed"). Proceeding to
`docs/session_2/proposal.md`.
