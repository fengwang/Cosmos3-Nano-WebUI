# GPU-S2 Design — HF Checkpoint Index/LFS Fix and Re-Pin Sweep

Date: 2026-07-09
Input: `docs/session_2/proposal.md`

## Context

Both `wfen/Cosmos3-Nano-{FP8,NVFP4}-Blockwise` repos ship a top-level
`model.safetensors.index.json` that references seven non-existent shards
(the real transformer weight is one consolidated file), and both
`.gitattributes` force every `.json`/`.py`/`.txt`/`.jinja` file into LFS via
blanket extension patterns regardless of size. A plain `git clone` therefore
leaves small config/tokenizer files as unresolved LFS pointers and a loader
looking for shards that don't exist. This has been proven, twice, as a real,
GPU-verified bug (the post-GO gate and `GPU-S1`'s own smoke test) — both
times worked around locally and undocumented. This session makes that fix
real, public, and at the source.

Constraint: `session_2_contract.yaml`'s `blast_radius` — external
`wfen/Cosmos3-Nano-{FP8,NVFP4}-Blockwise` repos, plus `docs/session_2/**`,
`docs/model_setup.md`, `docs/evidence_map.md`, `docs/risk_register.md`,
`docs/release_checklist.md`, `docs/eval_seed_cases.md`, `docs/handoff.md` in
this repo; `api/**`, `webui/**`, `deploy/**`, `schemas/**`, `.github/**`, and
any weight/media file are forbidden. `project_contract.md` Hard Commitments
2/3/5 (fresh-verification discipline, atomic re-pin, outward-action gate)
and invariants INV-4/5/7 apply without exception. Unlike `GPU-S1`, this
session's primary work happens **outside** this git repository, in two
external, already-public Hugging Face repos — an irreversible-ish,
outward-visible action class this project hasn't executed yet.

## Goals / Non-Goals

**Goals:**
- Both `wfen/*` repos: top-level stale index removed; LFS tracking
  corrected by the owner's size/type rule; large weight files never
  de-LFS'd.
- A fresh `git clone` and a fresh `hf download`, from a client that hasn't
  touched these repos before, resolve every small file as real content (not
  an LFS/Xet pointer) and find no stale index.
- Every in-repo pinned reference moves to the new revisions in this session;
  a whole-repository sweep finds zero stale survivors outside the one
  documented historical exception in `docs/eval_seed_cases.md`.
- An owner go-ahead is recorded immediately before each of the two pushes.

**Non-Goals** (`docs/session_2.md` Out of Scope):
- Dev-scratch **content** cleanup (D3: `_s2_*.md`, `producer_provenance.json`,
  `load_quantized.py`, `assets/FP8-Examples/**`, benchmark PNGs) — only their
  LFS storage mechanism is touched as a side effect of the repo-wide rule
  fix; their existence, content, and location do not change.
- Rewriting large weight files out of LFS.
- Dockerfile changes (`GPU-S1`, already closed).
- Upstream PR work (`GPU-S4`/`GPU-S5`).
- Full GPU load+generate proof — that's `GPU-S3`'s job. This session proves
  packaging/structural correctness (no stale index, no unresolved pointer),
  not runtime generation.

## Decisions

1. **Fresh-clone discipline, two independent clones per repo, both outside
   this git repository.** Clone (a): a working clone in the scratchpad used
   to make and push the fix. Clone (b): a separate, independent post-push
   clone/`hf download` used only to verify. Neither ever reuses the
   pre-existing `/data/models/Cosmos3-Nano-{FP8,NVFP4}-Blockwise*`
   directories — those are already-modified, uncommitted local checkouts,
   exactly the "already-patched checkout" the contract says not to rely on.
2. **LFS technique: trim `.gitattributes` + `git add --renormalize .`**
   (Approach A from brainstorming). Remove the blanket `*.json`, `*.py`,
   `*.txt`, `*.jinja` LFS lines; keep the genuine binary patterns
   (`*.safetensors`, `*.pt`, `*.pth`, `*.ckpt`, `*.mp4`, `*.png`, `*.jpg`,
   etc.) and the size-justified `text_tokenizer/tokenizer.json` override
   untouched. No `git lfs migrate export`, no history rewrite, no
   force-push.
3. **Two separate commits per repo, not one.** Commit 1: `git rm
   model.safetensors.index.json` alone. Commit 2: the `.gitattributes` edit
   plus `git add --renormalize .`. Isolating the renormalize into its own
   commit makes the "did any large file's LFS OID change" check (directly
   guarding R-04) a trivial single-commit `git lfs ls-files` diff, and keeps
   each commit independently revertable.
4. **Verification runs the real client tools, scoped to avoid tensor bytes
   — via a targeted exclude, not a blanket skip-smudge (amended, GPU-S2-A1).**
   Baseline testing (Task 1.2) showed `GIT_LFS_SKIP_SMUDGE=1` leaves *every*
   LFS-tracked file unsmudged, not just the large ones — unsafe for the
   *working* clone specifically, because `git add --renormalize .` would
   then bake raw pointer text into every small file's new "regular git"
   content instead of their real content. The tested, safe form for any
   clone whose content will be inspected or renormalized is a targeted
   `.gitattributes`-aware exclude:
   `git clone -c "lfs.fetchexclude=*.safetensors,*.pt,*.mp4,*.png,*.jpg,*.jpeg" <url>`,
   plus `hf download --exclude "*.safetensors" --exclude "*.pt"` (or
   equivalent) for the `hf` tool. Both are still real invocations of the two
   named client tools — they just don't pull the ~24–27 GB of weight bytes
   per repo, which this session's checks don't need (`GPU-S3` owns the
   functional GPU load). Neither mechanism smudges a path with no *current*
   `.gitattributes` match regardless (Decision 9) — that's a separate,
   orthogonal problem handled by Decision 9's manual restoration, not by
   clone flags. The probe inspects the resulting local directory directly
   (no top-level index; small files are real text, not
   `version https://git-lfs...` pointer stubs) and cross-checks against
   `HfApi.get_paths_info` manifest metadata (does a path report an `.lfs`
   attribute or not) as an independent second signal — reusing the
   functional-core/imperative-shell shape of
   `docs/archive/phase-1/session_4/probes/verify_hf_checkpoints.py` without
   needing its `parse_header` tensor-header reader (this session doesn't
   need precision/header inspection, only manifest-level packaging checks).
5. **Verification cache isolation.** This sandbox has already touched both
   repos (the pre-existing `/data/models/...` clones), so the default HF
   cache could mask a genuinely-fresh client's view behind the contract's
   own named Xet-caching failure mode. The verification pass points
   `HF_HOME`/`GIT_LFS_SKIP_SMUDGE` at a clean scratch directory that has
   never cached these two repos, and records that isolation as part of the
   evidence, rather than asserting freshness without demonstrating it.
6. **Order: FP8 fully first, end to end,** then replay the identical,
   by-then-validated recipe for NVFP4. Reduces the chance of hitting (and
   misdiagnosing) the same failure twice across both repos.
7. **Push gate is a hard stop, not a note.** The literal `git push` for FP8
   is never issued in the same step as anything else — it is preceded by an
   explicit, separate "push now?" confirmation. The same applies
   independently for NVFP4 after FP8's full cycle (including its own
   independent post-push verification) is done.
8. **R-02 mitigation lands as a repo-side note, not an HF-side edit.**
   Record the revision change directly in `docs/risk_register.md`'s R-02
   row; do not edit either HF repo's own README/model card (keeps the
   external blast radius to exactly index+LFS, per the "ignore
   `-dist`/don't fold in extra content" decision).
9. **Restore the four orphaned compliance docs' real content, in the same
   two commits as the LFS fix (amended, GPU-S2-A1).** `BIAS.md`,
   `EXPLAINABILITY.md`, `PRIVACY.md`, `SAFETY.md` check out as raw LFS
   pointer text in both repos, unrelated to the `.gitattributes` fix (no
   rule has ever matched `.md`, so neither the old nor the new
   `.gitattributes` state smudges them). Before renormalizing, fetch each
   file's real content directly from the LFS object store and smudge it
   manually (`git lfs fetch --include=<path>` then
   `git show HEAD:<path> | git-lfs smudge -- <path> > <path>`), then stage
   it as a normal file. FP8's `_s2_*.md` files have the identical
   corruption but are dev-scratch (Owner Decision 3) — left untouched,
   corruption and all, per the owner's explicit choice.

## Risks / Trade-offs

- **[Risk]** `git add --renormalize .` re-filters something unintended
  (pattern-removal mistake pulls a large file into the "now regular git"
  set) → **Mitigation:** Decision 3's commit split makes `git lfs ls-files`
  before/after that one commit a direct diff; assert the large-file OID set
  is unchanged before pushing (directly guards R-04, a named contract risk).
- **[Risk]** HF's Xet backend caches old pointer state in this
  already-touched sandbox, masking whether the fix works for a genuinely
  fresh client (contract's own named failure mode) → **Mitigation:**
  Decision 5 — isolated cache dir for the verification pass, recorded as
  evidence.
- **[Risk]** A push happens without a timely, explicit go-ahead (named
  adversarial case) → **Mitigation:** Decision 7 — the push command is
  never batched with other actions.
- **[Risk]** The re-pin sweep updates some but not all referencing files
  (named adversarial case) → **Mitigation:** run the sweep only after every
  planned doc edit is complete, and treat any match outside the one
  documented historical exception as a hard failure requiring another pass.
- **[Risk]** R-02 — an early adopter who already pulled the pre-fix revision
  breaks silently when the pin moves → **Mitigation:** explicitly accepted,
  one-time public-beta cost per the risk register's own mitigation;
  documented, not solved in code.
- **[Risk]** FP8 and NVFP4 diverge unexpectedly (e.g. NVFP4's `.gitattributes`
  already differs slightly from FP8's — confirmed during brainstorming) so
  the "identical recipe" assumption from Decision 6 doesn't transfer
  cleanly → **Mitigation:** re-derive NVFP4's exact diff from its own current
  `.gitattributes`/`lfs ls-files` state rather than blindly copying FP8's
  patch; both were already read in full during brainstorming, so the actual
  per-repo differences are already known, not a surprise to react to later.
- **[Risk]** (amended, GPU-S2-A1) A file with no *current* `.gitattributes`
  match but LFS-pointer-shaped committed content (an "orphan") gets silently
  renormalized with its pointer text intact, because renormalize only
  transforms paths whose attribute-driven treatment actually changes →
  **Mitigation:** Decision 9's explicit manual restoration for the four
  known orphans, plus a general pre-renormalize scan (Plan Step 2/4) that
  greps every to-become-regular file's working-tree content for the
  `version https://git-lfs` signature and fails loud if any unexpected
  orphan turns up, rather than trusting the enumeration in this design doc
  to be exhaustive.

## Migration Plan

No running production system in this repo depends on the old HF revision
directly — `GPU-S1`'s own T2I evidence used the local workaround, not the
raw pin. Rollout: fix and verify each HF repo locally first; push only after
an explicit go-ahead; re-pin this repo's docs in the same session (Hard
Commitment 3 — no session ends partially re-pinned). Rollback, if a pushed
HF commit proves wrong: push a further corrective commit to that HF repo
(a normal git remote, not registry-immutable) and re-run this repo's re-pin
sweep against whatever the corrected revision becomes; neither case involves
a force-push or history rewrite, since Decision 2 avoided that surface
entirely. Downstream: `GPU-S3` consumes the new revision hashes, the
LFS/`.gitattributes` recipe, and the fresh-clone verification evidence as
its explicit starting input (`session_2.md` Handoff section).

## Open Questions

- Exact size of each repo's `.gitattributes` diff — resolved empirically
  once the live file is edited; not a decision the design needs to
  pre-resolve.
- Whether Xet-backend caching in this sandbox would have actually masked
  anything in practice, or is a non-issue here — will be recorded as
  evidence either way (Decision 5), not assumed.

Both are implementation-time findings, not decisions the design needs to
pre-resolve.
