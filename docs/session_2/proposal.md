# GPU-S2 Proposal — HF Checkpoint Index/LFS Fix and Re-Pin Sweep

Date: 2026-07-09
Input: `docs/session_2/brainstorming.md`

## Motivation

Both public `wfen/Cosmos3-Nano-{FP8,NVFP4}-Blockwise` checkpoints ship a
stale top-level `model.safetensors.index.json` that references seven
non-existent shards, and their small config/tokenizer files are LFS-tracked
via blanket extension rules, so a plain `git clone` leaves those files as
unresolved pointers. The post-GO GPU gate and `GPU-S1`'s own smoke test both
worked around this with a local, undocumented fix; a public operator
following the README cannot reproduce that workaround. Fixing the HF repos
changes their revision hashes, so every in-repo reference to the old pins
must move together in the same session (`project_contract.md` Hard
Commitment 3). Advances archived Phase-1 risk R-03.

## Agreed Changes

From `docs/session_2/brainstorming.md`:

1. Fresh-clone each of `wfen/Cosmos3-Nano-FP8-Blockwise` and
   `wfen/Cosmos3-Nano-NVFP4-Blockwise` into the scratchpad (never reusing the
   pre-existing, already-modified `/data/models/...` local copies); `git rm`
   the top-level `model.safetensors.index.json`.
2. Trim `.gitattributes` to remove the blanket `*.json`/`*.py`/`*.txt`/`*.jinja`
   LFS rules (keep genuine binary patterns plus the size-justified
   `text_tokenizer/tokenizer.json` override), then `git add --renormalize .`
   in one additive commit — no `git lfs migrate export`, no history rewrite,
   no force-push. Applied repo-wide, including dev-scratch paths' storage
   mechanism (their content/paths/presence stay untouched).
3. FP8 first, end to end (clone → fix → local verify → owner go-ahead → push
   → independent fresh-clone verify), then replay the identical recipe for
   NVFP4.
4. Verify via a new torch-free, functional-core probe
   (`docs/session_2/probes/`, extending the Phase-1
   `verify_hf_checkpoints.py` pattern and reusing
   `tools/checkpoint_prep/safetensors_io.py:parse_header`) that confirms, via
   `HfApi` manifest metadata rather than a full tensor download: no top-level
   stale index, no small file left as an unresolved LFS pointer, large files
   still LFS-backed.
5. Sweep the whole repository (`rtk rg -n "4e181f99|b5c9332e" .`) and update
   every pinned-revision reference: `docs/model_setup.md` §1,
   `docs/evidence_map.md`, `docs/release_checklist.md` §7,
   `docs/eval_seed_cases.md`, `docs/risk_register.md` (R-02 revision-change
   note, R-03/R-04 disposition), `docs/handoff.md`.
6. A discrete, explicit "push now?" go/no-go immediately before each literal
   `git push` to a `wfen/*` repo — separate for FP8 and NVFP4 — regardless of
   overall plan approval already given.
7. Commit at each clean task checkpoint, matching `GPU-S1` precedent.

## Capabilities

### New Capabilities

- **`hf-checkpoint-lfs-layout`** — the corrected packaging contract for the
  two `wfen/*` repos: no top-level stale weight index; LFS tracking assigned
  by the owner's size/type rule (>10 MB or non-plain-text → LFS; small
  plain-text → regular git) rather than blanket extension patterns; large
  weight files never de-LFS'd; a push requires a recorded owner go-ahead
  immediately before it happens. Does not exist as a specified contract
  today — only as an undocumented local workaround.
- **`checkpoint-fresh-verification-probe`** — a repeatable, torch-free,
  functional-core/imperative-shell probe
  (`docs/session_2/probes/verify_gpu_s2_checkpoints.py`) that checks a
  checkpoint repo's manifest for stale-index absence and correct LFS
  placement using `HfApi` metadata only, without downloading tensor bytes.
  New code; no prior equivalent exists for this specific check (Phase-1's
  probe checked loadability/drift, not LFS-tracking correctness).

### Modified Capabilities

- **`pinned-checkpoint-references`** — every in-repo reference to the
  FP8/NVFP4 checkpoint revision currently points at the pre-fix SHAs
  (`4e181f99…`, `b5c9332e…`). Requirement changes to: every reference in
  `docs/model_setup.md` §1, `docs/evidence_map.md`, `docs/release_checklist.md`
  §7, `docs/eval_seed_cases.md`, `docs/risk_register.md`, and
  `docs/handoff.md` points at the new post-fix revisions, confirmed by a
  whole-repository sweep with zero survivors outside the one documented
  historical exception in `docs/eval_seed_cases.md`.

### Removed Capabilities

None — this session fixes packaging/reference contracts; it does not retire
any existing capability.

## Impact

- **External systems:** `wfen/Cosmos3-Nano-FP8-Blockwise` and
  `wfen/Cosmos3-Nano-NVFP4-Blockwise` on Hugging Face — new commits, new
  HEAD revisions, tracked here by reference only (`project_contract.md` §2
  Hard Commitment 7).
- **Files (this repo):** `docs/model_setup.md`, `docs/evidence_map.md`,
  `docs/release_checklist.md`, `docs/eval_seed_cases.md`,
  `docs/risk_register.md`, `docs/handoff.md`; new
  `docs/session_2/**` planning pack and `docs/session_2/probes/**`.
- **No impact** to `api/**`, `webui/**`, `deploy/**`, `schemas/**`,
  `.github/**`, or any model weight/generated media file — all explicitly
  forbidden by `session_2_contract.yaml`'s `blast_radius`.
- **Downstream sessions:** `GPU-S3` inherits the new revision hashes, the
  LFS/`.gitattributes` recipe, and the fresh-clone verification evidence
  (per `session_2.md`'s Handoff section) as direct inputs to its own joint
  GPU validation.
