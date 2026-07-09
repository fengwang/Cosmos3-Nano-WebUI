# Session 3 Adversarial Verification

Per `docs/agent_workflow/prompts/adversarial_verifier.md`: fresh-context verifiers, no
visibility into the implementation conversation or the sharded review — only the session
contract, project contract, diff, and evidence.

## Round 1: FAIL

**Verdict: FAIL.** Two disproven/unsupported claims, both confirmed real:

1. **Disproven:** `docs/evidence_map.md`'s T2V row and `docs/session_3/sharded_review.md`'s
   C1 write-up both claimed T2V's evidence was "re-run against the corrected checkpoint
   mount." The verifier checked `git log` on `evidence_t2v_smoke.json` across every commit
   between `GPU-S2` and `GPU-S3` (not just the tip-to-tip diff) and found no commit after
   the mount fix touched that file — because the re-run had in fact happened and produced
   byte-identical content, so there was nothing new to commit, but nothing in the evidence
   schema made that provable versus "never re-run at all." Correct finding: the claim
   wasn't independently verifiable from the committed artifacts, regardless of whether it
   happened to be true.
2. **Disproven:** `docs/release_checklist.md`'s private-reference-scan checkbox claimed "0
   findings." Running `uv run python tests/test_private_ref_scan.py` at that HEAD returned
   11 findings — a real regression introduced by two later commits (new test fixtures and
   the sharded-review write-up itself), never re-checked before either was written.

See `docs/session_3/failure_arbiter.md` F3 for the classification and fixes: added a
required `run_at` provenance timestamp to every evidence fragment (`lib.py`'s
`EvidenceRecord`), genuinely re-ran T1 and T3–T7 so every fragment carries a timestamp
provably after the mount fix, and fixed the scan regression (non-matching test fixtures,
the scanner's own documented ellipsis convention for naming a private-path class in prose
without retriggering the pattern-match).

**Everything else the round-1 verifier checked held up:** blast radius, no secrets/shell
injection, no generated media committed, guardrails-override mechanism matches the R-10
decision, test-suite mutation resistance (4/5 hand-mutations caught; the one miss matched
an already self-disclosed deferred gap), and live re-verification of the checkpoint-mount
fix itself (confirmed the *current* `docker compose config` resolution is correct).

## Round 2: FAIL

**Verdict: FAIL.** A fresh verifier, with no visibility into Round 1's report, independently
found:

1. **Disproven:** Round 1's own closing summary ("confirmed the current `docker compose
   config` resolution is correct") overclaimed — running the contract's own literal, bare
   `docker compose --env-file .env -f deploy/docker-compose.fp8.yml config` (no Python
   wrapper) still resolves to the stale `.env`-pinned directory, live, at HEAD. The
   round-1 verifier had actually run this bare form too (per its own "checks run" list) but
   didn't flag it as a live problem, since the fix's OWN probes (which route through
   `compose_lifecycle.py`'s override) do resolve correctly — Round 1's summary conflated
   "the fix works inside this session's tooling" with "the mount resolves correctly," which
   isn't the same claim. Real, previously-undiscovered gap: the contract's own documented
   reproduction command has no such protection. **Opened as `R-11`** (see
   `docs/risk_register.md`) rather than silently left — not fixable within `GPU-S3`'s blast
   radius, since fixing it means editing `session_3_contract.yaml`/`session_3.md`/`.env`,
   none of which this session may touch.
2. **Disproven:** `docs/release_checklist.md`'s "0 findings" scan claim, again — a *third*
   occurrence of the same class, this time in `docs/session_3/failure_arbiter.md`'s own
   prose describing the *second* occurrence's fix. Fixed by removing the literal
   path-shaped string entirely rather than trying another convention that might also slip.
3. **Unsupported claim, accepted as a real precision gap:** the commit message describing
   the T1/T3–T7 re-run called it uniformly "genuinely fresh" — T1's `run_at` reflects a
   resume-aware re-verification against already-correct content (the real transfer was
   ~9 hours earlier, confirmed via each checkpoint's `.metadata` sidecars), not a second
   full download. Clarified in `docs/evidence_map.md`.
4. **Unsupported claim, investigated and resolved (not a defect):** all four T2I artifacts
   share an identical `691,968`-byte size despite four distinct sha256 hashes. Verified the
   four full 64-character hashes are pairwise distinct (not a truncated-display collision
   hiding duplicate content) and that the byte count matches `480×480×3` raw RGB
   (`691,200`) plus `768` bytes of fixed overhead — consistent with a fixed-size/uncompressed
   PNG encoding, not a caching or duplicate-artifact bug. Documented in `docs/evidence_map.md`.

See `docs/session_3/failure_arbiter.md` for the classification. Fix commit: `d5560d2`.

## Round 3: [pending]
