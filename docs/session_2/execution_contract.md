# GPU-S2 Execution Contract

Date: 2026-07-09
Session contract: `docs/session_2_contract.yaml` (risk: high, routing:
branch_and_compare)

## Planned File Changes

- External `wfen/Cosmos3-Nano-FP8-Blockwise` — 2 commits (remove stale
  index + restore 4 orphaned compliance docs; fix LFS tracking), pushed
  after an explicit go-ahead. (Amended, GPU-S2-A1: the compliance-doc
  restoration was discovered during Task 1.2's baseline check, not part of
  the original brainstorming pack — see `docs/session_2_contract.yaml`.)
- External `wfen/Cosmos3-Nano-NVFP4-Blockwise` — 2 commits (same shape,
  independently derived), pushed after its own explicit go-ahead.
- `docs/model_setup.md` — §1 revisions, §8/§9 workaround guidance.
- `docs/evidence_map.md` — new evidence rows.
- `docs/release_checklist.md` — §7 revisions.
- `docs/eval_seed_cases.md` — Public Checkpoint IDs.
- `docs/risk_register.md` — R-02/R-03/R-04 status.
- `docs/handoff.md` — session close.
- `docs/session_2/**` — this planning pack (already written) +
  `probes/verify_gpu_s2_checkpoints.py` + `probes/evidence.json`/`summary.md`
  + `sharded_review.md`, `adversarial_verification.md`, `failure_arbiter.md`
  (only if needed) added as the session proceeds.

## Allowed Blast Radius

Exactly `session_2_contract.yaml`'s `blast_radius.allowed_files`: the two
external `wfen/*` repos, `docs/session_2/**`, `docs/model_setup.md`,
`docs/evidence_map.md`, `docs/risk_register.md`, `docs/release_checklist.md`,
`docs/eval_seed_cases.md`, `docs/handoff.md`. Forbidden: `api/**`,
`webui/**`, `deploy/**`, `schemas/**`, `.github/**`, and any model weight or
generated media file. No file outside this list will be edited without
stopping to flag it first. `tools/checkpoint_prep/safetensors_io.py` is read
(imported) only, never edited.

## First Test to Write

There is no unit-test harness for a Hugging Face repo's packaging. The first
check is Plan Step 1's baseline: a cache-isolated, `GIT_LFS_SKIP_SMUDGE=1`
fresh clone of each repo at its current HEAD, confirming the stale index is
present — establishing the "before" state the fix must change. The first
check with a pass/fail tied to an actual change is Plan Step 2's R-04 guard:
the `git lfs ls-files` large-weight-file diff across the renormalize commit
must be empty, checked before that commit is even made. The first genuinely
new *code* artifact is `docs/session_2/probes/verify_gpu_s2_checkpoints.py`;
its first test is its own `--check` mode's pure-classifier assertions
(fixture manifests → expected classification), written and green before the
probe is ever pointed at the network.

## Checks to Run After Each Task

- After each repo's Commit 1 (index removal): `test ! -e
  model.safetensors.index.json` in that working clone.
- After each repo's Commit 2 (renormalize): the R-04 large-file-OID diff
  (empty) and the "newly entered LFS" diff (empty), both computed *before*
  committing.
- After each push: an independent, cache-isolated fresh `git clone` +
  targeted `hf download` (excluding weight bytes) resolves the new HEAD,
  finds no stale index, and shows small files as real content, not LFS/Xet
  pointers.
- After the probe is written: `--check` exits 0 with no network; the full
  probe run against both new revisions produces `evidence.json`/`summary.md`
  with zero flagged files.
- After the doc sweep: `rg -n --hidden --glob '!.git' "4e181f99|b5c9332e" .`
  from the repository root (`--hidden` required — see amendment
  `GPU-S2-A3`) — the only matches are `docs/eval_seed_cases.md`'s own
  historical note and this session's own planning/evidence prose.
- Full deterministic check list from `session_2_contract.yaml`, re-run once
  at the end against the final state of both external repos and this repo.

## Review Axes (risk = high → mandatory sharded review)

correctness, security, tests, architecture, performance — per
`session_2_contract.yaml` and `docs/agent_workflow/prompts/sharded_review.md`.
Each reviewer is read-only and reports severity, evidence, violated contract
clause (if any), smallest safe fix, and confidence. Fix Critical/High
findings only before re-checking; Medium needs 2+ reviewers or strong
evidence; Nits are optional. Security axis specifically covers: no
secret/token ever appears in a committed file or commit message across
either external repo; the outward-action gate (push go-ahead) was genuinely
observed, not merely asserted.

## Adversarial Verifier Brief

Fresh context; sees only `session_2_contract.yaml`, `docs/project_contract.md`,
the diff (both external repos' commit history plus this repo's doc changes),
and `docs/session_2/`'s recorded evidence — not this implementation
conversation. Its job: try to falsify the claim that
`GATE-GPU-S2-CHECKPOINT` is satisfied. Specifically probe the contract's four
named adversarial cases:

1. Was the fix verified only against the pre-existing, already-patched
   `/data/models/...` local checkouts, rather than a genuinely fresh
   clone/download from a client with no prior cache of these repos?
2. Did the LFS-tracking fix accidentally de-LFS any large weight file —
   check the recorded before/after `git lfs ls-files` OID diff for every
   `*.safetensors`/`*.pt` file, not just a sample.
3. Does the re-pin sweep miss a referencing file — independently re-run
   `rg -n "<old-fp8-sha>|<old-nvfp4-sha>"` across the whole tree and confirm
   the only hit is the one documented historical note.
4. Did either push happen before a recorded, explicit owner go-ahead
   immediately preceding it — check the session transcript ordering, not
   just that a go-ahead exists somewhere.
5. (Amended, GPU-S2-A1) Do `BIAS.md`/`EXPLAINABILITY.md`/`PRIVACY.md`/
   `SAFETY.md` actually contain their real content post-fix in both repos —
   not just a claim that they were "restored" — and do the three FP8-only
   `_s2_*.md` dev-scratch files remain deliberately untouched (still
   corrupted), not accidentally fixed or accidentally further broken.

## Done Condition

`GATE-GPU-S2-CHECKPOINT` passes: both `wfen/*` checkpoint repos load cleanly
from a fresh clone/download (no stale index, no unresolved small-file LFS
pointer, no large file de-LFS'd) at their new revisions; every in-repo
pinned reference matches the new revisions, confirmed by a whole-repository
sweep with zero stale survivors outside the one documented historical
exception; an owner go-ahead was recorded immediately before each of the two
pushes. Sharded review and adversarial verification both complete with no
unresolved Critical/High finding.
