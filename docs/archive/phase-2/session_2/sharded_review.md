# GPU-S2 Sharded Review

5 independent read-only reviewers (correctness, security/safety, tests,
architecture, performance) against `git diff fe3d4c3..HEAD` plus the two
live external `wfen/*` repos, per
`docs/agent_workflow/prompts/sharded_review.md`. Each reviewer independently
cloned both external repos and/or re-ran the probe rather than trusting this
session's own narrative. Findings below are deduplicated across reviewers;
severity is my own synthesis judgment where it differs, with the reason
stated.

## Findings

### F1 — Verification probe had no detection path for a de-LFS regression (R-04)
- **Severity:** High.
- **Reviewers:** Correctness (1), Tests (1) — 2 independent reviewers,
  identical root cause.
- **Evidence:** `classify_lfs_placement`'s original form only checked
  `is_lfs and not expect_lfs`, never the reverse (`expect_lfs and not
  is_lfs` — a large/binary file that lost its LFS backing). The manifest
  fetch never recorded LFS `sha256`, and the probe only ever queried the
  post-fix revision, so no pre-fix-vs-post-fix comparison was possible even
  in principle. `run_self_check()` had zero assertions with `is_lfs=False`
  on an expected-LFS path.
- **Violated clause:** `session_2_contract.yaml`'s named adversarial case
  ("The LFS migration accidentally de-LFSes a large weight file");
  `docs/session_2/specs/checkpoint-fresh-verification-probe.md`'s
  "Confirms Large Files Remain LFS-Backed" requirement — already specified,
  never implemented.
- **Impact:** the probe reporting `passed: true` gave no actual automated
  protection against exactly the risk (R-04) it was supposed to help guard;
  the only real guard was a one-off manual `git diff --stat` outside the
  probe.
- **Fix applied:** rewrote `classify_lfs_placement` to check both
  directions; added `classify_large_file_stability` comparing pre-fix and
  post-fix LFS `sha256` for every large/oversized file pattern; `probe_repo`
  now fetches both revisions' manifests; `probe_passed` treats a `sha256`
  mismatch as a hard failure. Added corresponding self-check assertions for
  both new branches. Re-ran the full probe against both live repos: **no**
  large-file stability findings — the sha256-identical result now comes
  from the probe itself, not a one-off manual diff.
- **Confidence:** High.

### F2 — Content-based orphan check was a structural no-op
- **Severity:** High.
- **Reviewers:** Correctness (1), empirically reproduced by me during
  disposition (see below).
- **Evidence:** The original probe downloaded small-file content via
  `hf_hub_download` and checked for the LFS-pointer text signature.
  Reproduced independently: `hf_hub_download` for FP8's `_s2_postfix.md`
  (deliberately left as a raw LFS-pointer git blob, per Owner Decision 3)
  returned the fully-resolved 235-byte real content, not pointer text.
  Hugging Face's resolve endpoint smudges LFS pointers regardless of the
  *current* `.gitattributes` state — a different, more permissive rule than
  a raw `git clone`'s smudge filter, which only fires for a path some
  current attribute rule matches. The content check could therefore never
  produce `ORPHANED_POINTER` for any path, masking rather than verifying.
- **Violated clause:** `specs/hf-checkpoint-lfs-layout.md`'s orphan
  scenarios; design.md Decision 4's intent to inspect real content.
- **Impact:** `evidence.json`'s `content` field was never meaningful
  evidence; the working signal (`is_lfs`, confirmed to correctly detect
  pointer-shaped blobs independent of attributes) was already present but
  underused.
- **Fix applied:** removed the `hf_hub_download`-based content check
  entirely (`fetch_small_file_prefixes`, `classify_content`, the `content`
  finding dimension). `classify_lfs_placement`'s `is_lfs` signal is the
  single, correct source of truth for "is this blob pointer-shaped" — this
  also resolves the Performance reviewer's Finding 1 (unnecessary full-file
  downloads to read a 64-byte prefix), since that download path no longer
  exists.
- **Confidence:** High (empirically reproduced).

### F3 — Spec scenario for the NVFP4 dev-scratch orphan was stale
- **Severity:** High (reclassified from the architecture reviewer's framing
  as a possible live bug — verified it is not; the actual repo state is
  correct, only the spec text was wrong).
- **Reviewers:** Architecture (1).
- **Evidence:** `docs/session_2/specs/hf-checkpoint-lfs-layout.md`'s
  "Dev-scratch file storage mechanism is corrected, content untouched"
  scenario stated `transformer/producer_provenance.json` "is a regular Git
  blob, not an LFS pointer" after the fix. That was written during the
  specification phase, before this session discovered the deeper
  orphaned-pointer bug and the owner narrowed in-scope restoration to
  exclude this specific file (matching FP8's `_s2_*.md` treatment) — see
  brainstorming.md's Amendment section and the NVFP4-scope question. The
  spec was never updated to match. Independently confirmed via `HfApi` on
  the live, pushed NVFP4 HEAD (`5514c42b97…`): the path's `.lfs` attribute
  is still populated (`pointer_size=128`), i.e. still pointer-shaped at the
  git-blob level — the actual repo state is correct; only the spec text
  disagreed with it.
- **Violated clause:** `project_contract.md` §7 ("prefer deterministic
  evidence over narrative claims"); internal consistency between spec and
  implementation.
- **Impact:** the spec, read on its own, would have led a future reader to
  believe this file was fixed when it was deliberately left alone — exactly
  the kind of doc/reality drift this whole session exists to close.
- **Fix applied:** rewrote the scenario to state the file is byte-identical
  to the pre-fix revision including remaining LFS-pointer-shaped content,
  with an inline note explaining the amendment and the `hf
  download`/`HfApi` resolve-transparently nuance from F2.
- **Confidence:** High — directly verified against the live pushed state,
  not inferred.

### F4 — `checkpoint-fresh-verification-probe.md` described a mechanism the shipped probe never used
- **Severity:** Medium.
- **Reviewers:** Correctness (1).
- **Evidence:** The spec's "Tors-Free And No Large Download" requirement
  described `GIT_LFS_SKIP_SMUDGE=1 git clone` / `hf download` client-tool
  invocations; the shipped probe is pure `HfApi`-based and never shells out
  to `git`/`hf` at all. `GPU-S2-A1`'s amendment commit updated 7 sibling
  docs but missed this one.
- **Violated clause:** none normative; documentation accuracy only.
- **Impact:** misleading to a future maintainer reading the spec next to
  the code.
- **Fix applied:** bundled with F1/F2's fix (same file, same review pass) —
  rewrote the requirement and its two scenarios to describe the actual
  `HfApi`-only mechanism.
- **Confidence:** High.

### Low/Nit findings (recorded, not fixed — below the Medium/High fix threshold this pass)
- `is_large_or_binary`'s pure-pattern branch (a file under the size
  threshold that's still LFS by type, e.g. `modelopt_state.pt` at ~655 KB)
  had no self-check case exercising it independent of the size branch
  (Tests, Medium) — **fixed as a one-line addition while already rewriting
  the surrounding self-check for F1**, so not carried forward.
- `probe_passed`'s bad-placement path had no self-check case independent of
  its structurally-identical bad-content twin (Tests, Low) — **fixed for
  the same reason** (the content dimension it paralleled no longer exists
  after F2, and the placement path now has direct coverage).
- The re-pin sweep's "only match is the one historical exception" spec
  scenario reads more strictly than the actual, reasonable disposition
  applied (archive + this-session's-own-planning-doc matches are also
  excluded, not just the one eval_seed_cases.md line) — the sweep's actual
  execution and `docs/risk_register.md` R-03's closure note are accurate
  and evidenced, but the spec's wording could be read as stricter than what
  was actually delivered (Tests, Medium). Not fixed this pass — recorded
  for the handoff; a future re-pin sweep should either tighten the sweep or
  loosen the spec wording, not leave them mismatched.
- The verify-step `hf download --exclude` list in `plan.md` omits the media
  patterns (`*.mp4`/`*.png`/`*.jpg`) the sibling `git clone`'s
  `lfs.fetchexclude` already excludes, so a literal re-run of that one
  documented command would pull ~24-81 MB of demo assets it doesn't need
  (Performance, Low). Not fixed this pass — cosmetic inefquency in a
  documented one-off command, not code; recorded for the handoff.

## No-Findings Axes

- **Security/safety:** no Critical/High findings. One Medium control-gap
  noted: the "recorded owner go-ahead" (INV-7) has no artifact independent
  of the session transcript itself — `risk_register.md`'s R-02 row asserts
  a go-ahead occurred but isn't independent evidence of it. The reviewer
  found no evidence a gate was actually skipped (commit timestamps are
  consistent with an independent verify-then-ask-then-push cycle for both
  repos), and confirmed zero secrets/tokens/private paths anywhere in the
  diff, the probe, or the newly-restored/exposed file content in either
  live repo. Recommended follow-up (not applied this pass, Medium):
  append one line to `evidence_map.md` at go-ahead time in future sessions
  ("Owner go-ahead for `<repo>` push received `<timestamp>`") so the gate
  is artifact-checkable, not transcript-only.
- **Performance:** no Critical/High findings; the two Low findings above
  (F2's fix incidentally resolves one of them) are recorded, not blocking.

## Disposition

Per the session's fix policy (Critical/High only, then re-check): **F1**,
**F2**, and **F3** were fixed in this pass (all in
`docs/session_2/probes/verify_gpu_s2_checkpoints.py` and
`docs/session_2/specs/*.md`); **F4** was bundled in because it was in the
same file and trivial. The probe's `--check` self-test and full run against
both live repos were re-verified green after the fixes — both repos still
`PASSED: True`, now with the R-04 large-file-stability check actually
exercised (not just asserted) and the broken content check removed rather
than left as false assurance. The Low/Nit items and the one Medium security
control-gap are recorded here and carried into `docs/handoff.md`, not fixed
in this session.
