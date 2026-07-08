# Sharded Review - MIG-S8 Release Gate

Date: 2026-07-07 · Risk: high · Axes: correctness · security · tests · architecture ·
performance(completeness). Five read-only reviewer subagents over the S8 deliverables +
session diff. **Reviewer output treated as untrusted** — each returned concrete file:line /
command evidence with 28–42 tool uses; no rubber-stamp (0-tool-call) review was accepted
(S7 integrity lesson).

## Findings (deduplicated, most severe first)

| ID | Sev | Finding | Axes | Disposition |
|---|---|---|---|---|
| R-F1 | **High** | A `/workspace/…` local absolute path in `evidence_map.md:21` (INV-1 / §6). The committed scanner's `PRIVATE_PATH_PATTERNS` had no `/workspace/` class, so #12 was clean by construction (contract adversarial case "scan scoped too narrowly"). | security | **FIXED in-radius** — replaced with public phrasing; corrected #15 scan re-verified the in-radius surface clean. |
| R-F2 | **Med→High** | Deterministic check #15 was recorded as prose "clean" and its abspath sub-scan used an `rg` negative look-around (unsupported by Rust regex) swallowed by `2>/dev/null` → **silently broken**, indistinguishable from a real clean. | tests, security | **FIXED** — `failure_arbiter.md` FA-1 (TEST_BUG); #15 rewritten as #15a/#15b/#15c with exact commands + exit codes + true result. |
| R-F3 | **Med** | 24 `/workspace/…` local paths in **out-of-radius** historical docs (`docs/session_2/**` = 22 `vllm-omni`; `session_3/plan.md`+`session_4/plan.md` = 2 repo self-path). Tracked → ship at publish. | security | **RESOLVED via amendment S8-A1** — owner-approved; scrubbed to repo-relative / `/path/to/` placeholders; re-scan clean. `failure_arbiter.md` FA-2. |
| R-F4 | **Med** | The "must match" GPU clauses omitted the pinned BF16 base revision, so a later run could use a drifted base and still "match" (contract adversarial case "different checkpoint revision"). | architecture | **FIXED in-radius** — added `nvidia/Cosmos3-Nano` @ `fea6e03a…` to gate_record / eval_seed_cases / release_checklist. |
| R-F5 | **Med** | Drift **D3** (external HF repos ship dev-scratch `_s2_*`/provenance/loader files) surfaced in no S8 deliverable; outputs said "D1/D2/D4". | architecture, completeness | **FIXED in-radius** — "D1/D2/D4"→"D1–D4"; D3 added to gate_record limitations (external owner follow-up) + FR-5 note. |
| R-F6 | **High (in-flight)** | S8 `handoff.md` + `sharded_review.md` + `adversarial_verification.md` referenced but not yet written; literal deferred GPU/build commands cited as "in handoff" but absent. | completeness, architecture | **Resolving** — this file created; literal commands added to `release_checklist.md` §6/§7 + gate_record; handoff is task 6.2 (produced at close). |
| R-F7 | **Low** | R-01/R-05/R-16 status cells led with "Open"/"still open" though a disposition followed; gate_record risk clause omitted R-01. | completeness | **FIXED in-radius** — leading tokens re-worded to lead with the S8 disposition; R-01 added to the gate_record no-unowned-risk clause. |
| R-F8 | **Nit** | Weight/media extension set inconsistent; scanner lacked `.webm`. Moot (0 `.webm` files exist). | tests | **RESOLVED via amendment S8-A2** — `.webm` added to the scanner's `WEIGHT_MEDIA_EXTS` (folded into the FA-3 patch). `failure_arbiter.md` FA-3. |

Correctness reviewer: **no findings** (independently re-derived the 16 PRD MUSTs, 14 PASS / 2
BETA-LIMITED / 0 NO-GO arithmetic, pytest 485 / vitest 209 / compose exits, and all pins).

## Fixes applied this review (all docs-only, in-radius)

- `docs/evidence_map.md:21` — removed the `/workspace/…` local path (R-F1).
- `docs/session_8/outputs/deterministic_checks.md` — #15 rewritten with exact commands +
  exit codes (#15a/b/c); Notes record the FA-1 TEST_BUG + the FA-3 scanner gap (R-F2/R-F8).
- `docs/session_8/outputs/gate_record.md` — BF16 base revision added; drift D1→"D1–D4" + D3
  limitation + literal-command pointer; R-01 added to the no-unowned-risk clause (R-F4/F5/F7).
- `docs/session_8/outputs/acceptance_matrix.md` — FR-5 drift "D1/D2/D4"→"D1–D4 (incl. D3)".
- `docs/eval_seed_cases.md`, `docs/release_checklist.md` — BF16 base revision in the "MUST
  use" clauses; literal vLLM-Omni build + GPU-marker commands in §6/§7 (R-F4/F6).
- `docs/risk_register.md` — R-01/R-05/R-16 status cells lead with the S8 disposition (R-F7).
- `docs/session_8/failure_arbiter.md` — FA-1 (TEST_BUG), FA-2 (SPEC_GAP, owner), FA-3
  (scanner recommendation).

## Owner-approved amendments (applied this session)

- **S8-A1 (FA-2 / R-F3):** owner approved extending the blast radius to
  `docs/session_{2,3,4}/**`; the 24 `/workspace/…` local paths were scrubbed (sibling checkout
  → repo-relative `vllm-omni`; repo self-path → `/path/to/Cosmos3-Nano-WebUI`). Re-scan clean.
- **S8-A2 (FA-3 / R-F8):** owner approved a product-code amendment; a `workspace_path` pattern
  + `.webm` were added to `tests/test_private_ref_scan.py` with RED-before-GREEN unit tests, so
  the gate catches this class going forward. Eval seed `mig_s8_scanner_abspath_blindspot`.

Both recorded in `docs/session_8_contract.yaml` (`blast_radius.allowed_files`).

## Verdict

No **Critical**. All findings **resolved** in-session: the in-radius High/Med items were fixed,
and the two out-of-radius items were fixed under owner-approved amendments S8-A1/S8-A2. The GO
recommendation stands, conditional only on the standing GPU + at-publish items.
