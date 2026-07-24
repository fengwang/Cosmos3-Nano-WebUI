# AM-S1 Sharded Review

Date: 2026-07-24. Risk: high → sharded review required. Three independent
read-only reviewers (fresh context) over the decision record + evidence + rubric +
contracts. Deduplicated below with disposition. Policy: **fix High/Critical**;
Medium/Low fixed where cheap and they harden the record before adversarial
verification + owner sign-off; Nits optional.

## Reviewers
1. Correctness + evidence-sufficiency → 0 Critical, 2 High, 3 Med, 3 Low, 3 Nit.
2. Contract-compliance + security/safety → **PASS, 0 findings** (blast radius clean;
   no secret/private-path leak; INV-1/INV-4/INV-5/R-02 all hold).
3. Reproducibility + clarity → 3 High, 4 Med, 3 Low, 1 Nit.

No **Critical** findings. No reviewer found a wrong/fabricated verdict, a
feasibility→quality conflation that survives, a blast-radius breach, or a leaked
secret. All Highs concern **how verdicts are justified**, not the verdicts.

## Deduplicated findings (by theme)

### T1 [HIGH] Rubric deviations not flagged (R1-H1, R1-M2, R3-M×2, R3-L)
The pre-registered rubric (design.md) did not anticipate the actual findings, so
several verdicts were reached outside their frozen branches without saying so:
- Packaging: rubric gated "GO" on "**P1 gap confirmed**"; P1 **contradicted** the
  gap → the "GO/DONE" is an evidence-driven *update*, not a rubric branch.
- Action: rubric enumerates (a)/(c)-loads/(c)-blocked-by-D1; the real state
  (surface **present-but-unwired**; (c) fails at a **key collision** before the
  precision check) is a fourth, unlisted state.
- Residency: rubric's two-resident row said "reasoner ~quantized ⇒ E-08 **stale**";
  the real outcome is the reasoner stays **BF16**, so E-08 is **not** stale today.
- E-06: the design gate ("confirmed iff A none / B present") **failed** (A has 5) →
  E-06 refuted; not stated as an explicit gate-failure.
**Disposition: FIX** — add explicit rubric-deviation callouts. Serves the
anti-conflation discipline (the rubric was the safeguard).

### T2 [HIGH] Provenance attribution over-confident (R1-H2)
"ALREADY APPLIED (P6-S5)" is graded High, but rests on a self-asserted sidecar
`note` + touched-files, not a re-run/hash check. The **adapters-are-bundled** fact
is airtight (P1 byte-level, non-zero values); the **tool attribution** is
circumstantial. **Disposition: FIX** — keep "bundled = GO/DONE" High; annotate the
P6-S5 attribution as "per sidecar provenance, not re-verified this session."

### T3 [HIGH] Show the receipts / reproducibility (R3-H transcripts, R3-M collision-verbatim, R3-M VRAM-CSV, R1-L3, R3-L P0)
Evidence files present curated tables, not literal command+raw-output transcripts
(design.md:44 promised "commands + outputs"). **Disposition: FIX** — add a
"commands + raw output (receipts)" block to P1/P3/P5/P7 with exact commands and
trimmed verbatim output (key scan; chat response shape; the real `ValueError`
collision string; raw `nvidia-smi` CSV rows); cite the CPU-suite log path for P0.

### T4 [HIGH] P4/P6 method deviations undocumented (R3-H P4, R3-H P6)
- P4 (reasoning (c) fallback) was **not run** — correctly, because P3 found a chat
  surface (so P4's "no-chat" branch didn't fire), but its absence is silent.
- P6 (action (c) load) was done **CPU-side/torch-free** (the collision precedes any
  GPU work), not the pre-registered GPU instantiation; the `505` precision check was
  therefore **inferred, not executed**.
**Disposition: FIX** — document P4-not-run + why; mark P6 CPU-side and `505` as
inferred.

### T5 [MED/LOW] Wording precision (R1-M1, R1-M3, R1-L1, R1-L2, R3-Nit, R1-N1)
"real values" (sampled only on deployed FP8, not public/NVFP4); "integrity-probed"
(tool has the path / unit-tested, not this checkpoint); "no extra VRAM" (projected
for the wired state, unmeasured); "no leak" (single cycle); completion_tokens=1
interpretation; deployed vs public differ by lm_head. **Disposition: FIX (cheap)** —
scope each phrase. These overlap the High edits.

## Summary
0 Critical · 5 High (T1–T4 + the R3 transcript cluster) · several Med/Low folded in.
Conclusions stand; fixes tighten justification + receipts. Re-check after fixes:
deterministic checks stay green; blast radius unchanged.
