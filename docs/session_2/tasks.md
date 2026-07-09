# GPU-S2 Tasks — HF Checkpoint Index/LFS Fix and Re-Pin Sweep

Input: `docs/session_2/design.md`, `docs/session_2/specs/*.md`

## 1. Pre-Flight / Baseline

- [ ] 1.1 Re-confirm network egress to `huggingface.co`, `HF_TOKEN`/SSH auth
      as `wfen`, and `git-lfs` availability still hold (state may have
      changed since brainstorming).
- [ ] 1.2 Establish baseline: a cache-isolated, `GIT_LFS_SKIP_SMUDGE=1` fresh
      clone of each repo at its **current** (pre-fix) HEAD, in a scratch
      directory that has never touched these repos before. Confirm the
      stale-index file is present and record the pre-fix manifest (this is
      the "before" evidence, independent of the pre-existing
      `/data/models/...` copies).

## 2. FP8 Fix (depends on 1)

- [ ] 2.1 Fresh working clone of `wfen/Cosmos3-Nano-FP8-Blockwise` into the
      scratchpad (`GIT_LFS_SKIP_SMUDGE=1`).
- [ ] 2.2 Commit 1: `git rm model.safetensors.index.json`.
- [ ] 2.3 Edit `.gitattributes`: remove the blanket `*.json`, `*.py`,
      `*.txt`, `*.csv`, `*.jinja` LFS lines; keep every binary pattern and
      the `text_tokenizer/tokenizer.json` size-justified override unchanged.
- [ ] 2.4 Commit 2: the `.gitattributes` edit plus `git add --renormalize .`.
      Diff `git lfs ls-files`' large-weight-file rows between the commit
      before and after this one — the OID column must be unchanged (R-04
      guard) before proceeding.
- [ ] 2.5 Local verification: small files in the working clone are real
      content (not `version https://git-lfs...` pointer stubs); no
      top-level index remains.
- [ ] 2.6 **Stop.** Explicit "push FP8 now?" go/no-go with the owner —
      never batched with any other action.
- [ ] 2.7 Push both commits — only after the go-ahead in 2.6.
- [ ] 2.8 Independent, cache-isolated fresh `git clone` and `hf download`
      (excluding weight-file bytes) against the new HEAD; confirm no
      unresolved pointers and no stale index; record the new revision SHA.

## 3. NVFP4 Fix (depends on 2 — same recipe, re-derived, not copied)

NVFP4's current `.gitattributes` already has no blanket `*.json`/`*.py`/
`*.txt`/`*.jinja` rule (confirmed during brainstorming) — its small files are
LFS-tracked only because they were committed before that rule was removed
and never renormalized. Re-verify this live rather than assuming it still
holds.

- [ ] 3.1 Fresh working clone of `wfen/Cosmos3-Nano-NVFP4-Blockwise` into the
      scratchpad (`GIT_LFS_SKIP_SMUDGE=1`).
- [ ] 3.2 Commit 1: `git rm model.safetensors.index.json`.
- [ ] 3.3 Re-inspect NVFP4's live `.gitattributes`. If it is already
      correctly scoped (expected), skip straight to 3.4. If it is not (state
      has drifted since brainstorming), re-derive its own diff from its
      current content — do not copy FP8's `.gitattributes` patch verbatim.
- [ ] 3.4 Commit 2: `git add --renormalize .` (plus any `.gitattributes` edit
      3.3 found necessary). Diff `git lfs ls-files`' large-weight-file rows
      before/after — OID column unchanged (R-04 guard).
- [ ] 3.5 Local verification (same checks as 2.5).
- [ ] 3.6 **Stop.** Explicit "push NVFP4 now?" go/no-go, independent of
      FP8's — never batched with any other action.
- [ ] 3.7 Push — only after the go-ahead in 3.6.
- [ ] 3.8 Independent, cache-isolated fresh `git clone` and `hf download`
      against the new HEAD; confirm no unresolved pointers and no stale
      index; record the new revision SHA.

## 4. Verification Probe (start once FP8's recipe is validated; finalize after both repos are done)

- [ ] 4.1 Write `docs/session_2/probes/verify_gpu_s2_checkpoints.py`:
      functional-core/imperative-shell, `HfApi`-manifest-based (no tensor
      download), a `--check` mode with pure, network-free assertions, no
      `torch`/`diffusers` import — per
      `docs/session_2/specs/checkpoint-fresh-verification-probe.md`.
- [ ] 4.2 Run `--check` (offline self-test) — must exit 0.
- [ ] 4.3 Run the full probe against both new revisions; write
      `docs/session_2/probes/evidence.json` and `summary.md`.

## 5. Whole-Repository Re-Pin Sweep (depends on 2, 3)

- [ ] 5.1 Update `docs/model_setup.md` §1 (both new revisions) and §8/§9
      (the "known packaging workarounds" section no longer applies at the
      new revisions — update the operator guidance and download example
      accordingly instead of leaving it describing a now-fixed bug as
      current).
- [ ] 5.2 Add fresh evidence rows to `docs/evidence_map.md` (both repos'
      fix + fresh-clone/`hf download` verification).
- [ ] 5.3 Update `docs/release_checklist.md` §7 with the new revisions.
- [ ] 5.4 Update `docs/eval_seed_cases.md`'s "Public Checkpoint IDs" — new
      revisions as current, pre-fix SHAs preserved only as the existing
      historical note.
- [ ] 5.5 Update `docs/risk_register.md`: close/advance R-02 (revision
      change documented), R-03 (re-pin sweep executed), R-04 (no large file
      de-LFS'd, evidenced by 2.4/3.4's OID diff).
- [ ] 5.6 Run the sweep: `rg -n "4e181f99|b5c9332e" .` from the repository
      root. Confirm the only match is `docs/eval_seed_cases.md`'s own
      historical note; any other match blocks session close until fixed.

## 6. Review and Verification (risk = high → mandatory)

- [ ] 6.1 Sharded review across correctness, security, tests, architecture,
      and performance axes.
- [ ] 6.2 Fix High/Critical findings only; re-run the targeted checks they
      affect.
- [ ] 6.3 Adversarial verification with a fresh-context reviewer that sees
      only the contract, diff, and evidence.
- [ ] 6.4 If any check fails the same way twice, invoke the Failure Arbiter
      before attempting another fix.

## 7. Session Close

- [ ] 7.1 Re-run the full deterministic check list from
      `session_2_contract.yaml`.
- [ ] 7.2 Verify `GATE-GPU-S2-CHECKPOINT`'s done condition against the
      recorded evidence.
- [ ] 7.3 Write/update `docs/handoff.md`.
- [ ] 7.4 Add eval seeds to `docs/eval_seed_cases.md`
      (`EV-GPU-CHECKPOINT-FRESH-CLONE`, `EV-GPU-REPIN-SWEEP-COMPLETE`, plus
      anything newly caught or missed this session).
- [ ] 7.5 State remaining risks and warnings for `GPU-S3`.
