# Session 3 Failure Arbiter Log

Classified per `docs/agent_workflow/prompts/failure_arbiter.md`. Only failures that
recurred, needed a category decision, or came from adversarial verification are logged
here — routine first-time fixes during the Task Loop are covered inline in their commit
messages.

## F1 — NVFP4 `hf download` timeout (first occurrence)
**Category: ENVIRONMENT.** The download and integrity-check logic were both correct; the
3600s budget was simply too tight for this checkpoint's actual transfer time. Not a code
bug — `hf download` resumes from already-fetched blobs on retry rather than restarting, so
the fix was to widen the timeout to 7200s and retry, not to rewrite the download/check
logic. See commit `863eea9`.

## F2 — Every generation probe mounted the stale, pre-fix checkpoint
**Category: BUG.** `compose_lifecycle.bring_up()` relied on `docker compose --env-file .env`
alone, and `.env` pins `COSMOS3_FP8_DIR`/`COSMOS3_NVFP4_DIR` to a stale local directory that
silently outranks the compose file's own repo-relative default. This is a clear contract
violation (`session_3_contract.yaml`'s fresh-download invariant and its own named
adversarial case), not an ambiguity or environment issue — the code needed to explicitly
override the mount and verify it, not just trust the default. Fixed with an explicit env
override plus a preflight assertion; regression test is the preflight itself (verified live
that it both passes for the correct path and raises for a wrong one). See commit `0fc75de`.

## F3 — Adversarial verification round 1: FAIL
**Category: BUG (two, both self-contained).**

1. **Unprovable re-run claim.** `evidence_map.md`/`sharded_review.md` asserted the T2V
   evidence was "re-run against the corrected mount," but no new commit touched
   `evidence_t2v_smoke.json` after the mount fix (re-running produced byte-identical
   content, so nothing changed to commit) — the verifier correctly found this claim
   unsupported by the committed artifacts, independent of whether it happened to be true.
   This is a design gap in the evidence schema, not a one-off documentation slip: nothing
   in `EvidenceRecord` distinguished "genuinely re-run, same result" from "never re-run."
   Fixed by adding a required `run_at` provenance timestamp to every fragment (commit
   `4317245`), then genuinely re-running T1/T3–T7 so every fragment carries a timestamp
   provably after both the mount fix and this fix (commit `fecdec3`).
2. **`make scan` regression.** Commits `c18a236` (new test fixtures using absolute-path-
   shaped strings that happened to match the scanner's own private-path rules) and
   `3a78132` (documenting the H5 finding by naming the leaked prefix literally instead of
   using the scanner's own documented non-matching convention for this) each re-triggered
   the private-reference scanner's own rules after I had already fixed the same class of
   issue once. Root cause: I re-ran `make scan` after the specific INV-1 fix commits but not
   after every later commit. Fixed by using
   non-matching placeholder paths in the test fixtures and the scanner's own documented
   ellipsis convention (`/home/…`-shaped) for naming the class in prose, without
   retriggering the pattern-match (commit `4317245`).

**Process lesson (harvested to `docs/eval_seed_cases.md`/eval corpus):** re-run
deterministic checks (`make scan`, the test suite) after *every* commit that touches
tracked files, not only the commits judged relevant at the time — exactly the same lesson
`GPU-S2` harvested about `rg --hidden`, recurring in a different form.
