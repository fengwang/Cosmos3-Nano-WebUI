# AM-S1 Adversarial Verification

Date: 2026-07-24. Method: fresh-context verifier (no sight of the implementation
conversation), given only `docs/session_1_contract.yaml`, the working-tree diff,
and `docs/session_1/{decision_record,evidence/*}`. Task: **falsify** that
`GATE-AM-S1-SPIKE` is satisfied. Carve-outs honored: the
`evidence_map`/`risk_register`/`eval_seed_cases`/`handoff` updates are a separate
later step; owner sign-off is a human gate (legitimately PENDING).

## Verdict: **PASS**
The technical parts of the done condition are satisfied, the record is internally
self-consistent and numerically reconciled, no forbidden file was modified, and
owner sign-off is the only remaining (human) gate. Every contract `adversarial_case`
was attempted and could not be sustained.

## Attempted falsifications (all refuted)
1. **Feasibility↔quality conflation** → REFUTED. Reasoning is *not* claimed to work
   (recorded as image-gen, verdict `(c)`, zero-BF16 UNRESOLVED). Action is *not*
   claimed to work (surface "present-but-unwired"; verdict "neither functional
   as-served").
2. **E-06 assumed, not re-confirmed** → REFUTED (and inverted). P1 inspected the
   real checkpoint bytes (5 `action_*` present, non-zero values) + the public pin on
   HF; E-06 is refuted against the real checkpoint, transparently as an
   evidence-driven rubric inversion (§7.1).
3. **Blast-radius breach** → REFUTED for all contract-forbidden paths (`api/**`,
   `deploy/**`, `tools/checkpoint_prep/**`, `schemas/`, `Makefile`, `.env.example`,
   `README`, `docs/walkthrough.md`, `docs/images/**`, `webui/**` all unmodified;
   `loader.py` read-only). `git status` = `M misc/logo.png`, `?? docs/archive/phase-4/`,
   `?? docs/session_1/`. Nothing committed/staged.
4. **Action `(c)` fallback omitted** → REFUTED (retained as the R-02 fallback, "after
   a code fix").
5. **VRAM asserted without a trace** → REFUTED (all footprints trace to `nvidia-smi`
   receipts; unmeasured claims — the wired plane-merge footprint, "no leak" — are
   labeled as projections/single-cycle).

Additional skeptical checks (code constants, `merge_state_dicts` collision ordering,
CPU baseline re-run **523 passed**, number reconciliation, no dangling citations) —
all refuted.

## Non-blocking blemish flagged
`misc/logo.png` is modified in the working tree (pre-existing at session start,
unstaged, outside both `allowed_files` and `forbidden_files`, non-production, not an
AM-S1 artifact). It does **not** falsify the done condition (nothing is committed;
INV-1 forbids only *committing* a media binary), but it must **not** be swept into an
AM-S1 commit. **Action:** leave it untouched (it is not this session's change) and
scope any future commit to `docs/**` only. Recorded for owner awareness.

## Classification
No failure to arbitrate — the verifier PASSED. The one blemish is an
ENVIRONMENT/housekeeping note (pre-existing working-tree noise), not a BUG/SPEC_GAP.
