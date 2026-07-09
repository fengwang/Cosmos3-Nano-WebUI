# Session 2 - HF Checkpoint Index/LFS Fix and Re-Pin Sweep

Contract: `docs/session_2_contract.yaml`
Risk: high
Routing: branch_and_compare

## Objective

Fix both `wfen/Cosmos3-Nano-FP8-Blockwise` and
`wfen/Cosmos3-Nano-NVFP4-Blockwise` Hugging Face repos (remove the stale
weight index, correct LFS tracking) and sweep every in-repo pinned reference
to the resulting new revisions.

## Why This Session Exists

Both public checkpoints carry a stale top-level
`model.safetensors.index.json` that references seven non-existent shards, and
their small config/tokenizer files are LFS-tracked, so a plain `git clone`
leaves those files as unresolved pointers. The post-GO GPU gate worked
around this locally; a public operator following the README cannot. Fixing
the HF repos changes their revision hashes, so every reference to the old
pins in this repo must move together in the same session. Advances archived
Phase-1 risk R-03 (`docs/archive/phase-1/risk_register.md`).

## In Scope

1. Fresh clone of each of `wfen/Cosmos3-Nano-FP8-Blockwise` and
   `wfen/Cosmos3-Nano-NVFP4-Blockwise`.
2. `git rm` the top-level `model.safetensors.index.json` in each repo.
3. Rewrite `.gitattributes` per the LFS rule from `docs/prd.md` Owner
   Decision 4 (files >10 MB or non-plain-text use LFS; small plain-text
   files use regular Git). Migrate the small files out of LFS
   (`git lfs migrate export` or a `.gitattributes` change plus
   `git add --renormalize .`), keeping the large weight files in LFS.
4. Commit and push each repo.
5. Verify with a **fresh** `git clone` **and** `hf download` — not the local
   checkout used to develop the fix — that config files are real and the
   checkpoint loads.
6. Sweep the whole repository and update every pinned-revision reference —
   at minimum `docs/model_setup.md` §1, `docs/evidence_map.md`,
   `docs/release_checklist.md` §7, and `docs/eval_seed_cases.md`, plus any
   other file the sweep turns up.

## Out of Scope

- Dev-scratch cleanup (drift D3: `_s2_*.md`, `producer_provenance.json`,
  `load_quantized.py`, `assets/FP8-Examples/**`, benchmark PNGs) — owner
  decided this is out of scope for this pass.
- Rewriting the large weight files into non-LFS (would bloat repo history).
- Dockerfile changes (`GPU-S1`).
- Upstream PR work (`GPU-S4`, `GPU-S5`).

## Deliverables

- Fixed `wfen/Cosmos3-Nano-FP8-Blockwise` and
  `wfen/Cosmos3-Nano-NVFP4-Blockwise` repos with new revision hashes.
- Fresh-clone and `hf download` verification evidence for both.
- Every in-repo pinned-reference location updated to the new revisions in
  the same session — at minimum the four files named above, confirmed by a
  whole-repository sweep.

## Deterministic Checks

```bash
git clone <fresh tmp dir> https://huggingface.co/wfen/Cosmos3-Nano-FP8-Blockwise
git clone <fresh tmp dir> https://huggingface.co/wfen/Cosmos3-Nano-NVFP4-Blockwise
hf download wfen/Cosmos3-Nano-FP8-Blockwise --revision <new sha>
hf download wfen/Cosmos3-Nano-NVFP4-Blockwise --revision <new sha>
rtk rg -n "4e181f99|b5c9332e" .
```

The last command sweeps the whole repository, not only the four named docs,
using an 8-character prefix so it also catches abbreviated citations (for
example `4e181f99…`), not only full 40-character SHAs. The only expected
match after the sweep is `docs/eval_seed_cases.md`'s own "replacing the
pre-fix …" historical reference under Public Checkpoint IDs; any other
match means a stale pin survived.

## Exit Criteria

- `GATE-GPU-S2-CHECKPOINT` passes.
- Both repos load cleanly from a fresh clone/download with no manual index
  removal.
- No stale pin remains in any of the four referencing docs.
- Owner go-ahead is recorded before the push to either `wfen/*` repo.

## Handoff

Hand off the new revision hashes, the exact LFS/`.gitattributes` recipe used,
and the fresh-clone verification evidence to `GPU-S3`.
