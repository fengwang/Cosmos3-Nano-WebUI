# LX-S2 Sharded Review — README Rewrite

Date: 2026-07-24
Reviewer: independent read-only agent (fresh context), 6 axes per
`docs/agent_workflow/prompts/sharded_review.md`. Diff under review:
`README.md` only (131 insertions, 92 deletions). Deterministic checker:
16/16 PASS.

## Verdict

**No Critical or High findings with concrete evidence.** All contract
invariants (INV-1, INV-5, INV-6, INV-7, INV-8) and every adversarial case hold.
The mandatory no-over-claim / no-lost-caveat review records **no surviving
over-claim and no dropped/softened/hidden caveat**. `GATE-LX-S2-README`
satisfied. One Low (since fixed) and one testing Nit, both non-blocking.

## Findings

| # | Severity | Location | Axis / Invariant | Finding | Disposition |
|---|---|---|---|---|---|
| 1 | Low | `README.md` "How it works" Mermaid edge | Correctness / INV-8 (map faithfulness) | The edge label `ORCH -->\|docker start/stop · generate\| GEN` conflated the control plane (Docker socket = container start/stop, `manager.py`+`container.py`) with the data plane (generation traffic goes to the container over HTTP, `COSMOS3_VLLM_OMNI_URL`). | **Fixed** (commit after review): the socket edge is now `docker start/stop` only, plus a separate `API -->\|generate over HTTP\| GEN` data edge. Still 5 nodes. |
| 2 | Nit | scratchpad `check_readme.py` | Tests | The gate checker does not pin the checkpoint repo ids / revisions / licenses against `docs/model_setup.md`, so a future drift there would not be caught by the gate. (The values were verified to match manually and by the adversarial pass.) | Recorded as an eval-seed candidate (`docs/eval_seed_cases.md`). Not fixed: the checker is a session tool, not committed; `model_setup.md` is out of this session's scope. |

## Axis notes (all cross-checked against source)

- **Correctness:** `make build/up-fp8/up-nvfp4/up-fp8-reasoning/health` all exist
  in `Makefile`; quickstart order complete (INV-5); checkpoint ids/revisions/
  licenses match `docs/model_setup.md`; idle keep-warm text matches
  `api/app/main.py` (default `1800`) + `api/orchestrator/manager.py`
  (`idle_timeout=1800.0`, `notify_idle` `0`-disables, `acquire` evict-before-load);
  all six "GPU-verified" occurrences t2i-scoped (E-20); all 34 link targets
  resolve.
- **Readability:** progressive disclosure sound (2 `<details>`, verbose/optional
  only, blank line after each `</summary>`); nothing essential collapsed; 4 emoji,
  all in the footer, never the sole signal; one `> [!NOTE]` (sparing); TL;DR +
  Jump-to nav present.
- **Security:** no caveat dropped/softened/hidden; five posture facts visible at
  the end and consistent with `SECURITY.md`; no secret/token/private-path/weight
  committed; no cloud CTA (INV-7/R-06).
- **Tests:** the deterministic checker covers every contract assert (links,
  no-CTA, ordered quickstart + Makefile targets, TL;DR/Mermaid≤7/`<details>`+
  blank-line/anchors, Status visible+not-collapsed+final-third+five-facts+30-min,
  t2i-only honesty subset with a wrap-robust context-window scan). Nit above.
- **Architecture:** single file; depth linked out, not inlined (FR-10); rendered
  growth (187→226 lines) is added orientation (How-it-works, Mermaid, TL;DR, two
  `<details>`), not re-bloated depth; anchors stable.
- **Performance:** N/A (docs); length growth intentional.

## Cleared tension (checked, not a finding)

The "720p text→video smoke passed on **both FP8 and NVFP4**" line
(`README.md` Features footnote + Status) is **pre-existing verbatim** from the
HEAD README and traces to phase-3 evidence (`docs/archive/phase-3/evidence_map.md`
E-17/E-18: measured 14,665 MiB FP8, 18,517 MiB NVFP4). It is explicitly **not** a
"verified" claim (the text de-promotes it). `docs/model_setup.md` records only the
narrower NVFP4 smoke, but that file is out of this session's substance scope. Not
introduced by this rewrite; recorded as a residual doc-consistency note in the
handoff.
