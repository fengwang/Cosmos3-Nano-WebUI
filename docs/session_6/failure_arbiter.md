# AM-S6 Failure Arbiter

## Failure: adversarial honesty pass returns FAIL on the video "GPU-verified" claim

**Failing check:** the mandatory adversarial no-over-claim honesty pass
(`docs/session_6/adversarial_verification.md`) — VERDICT **FAIL**. The sharded review
(`docs/session_6/sharded_review.md`) returned PASS with the same fact noted as an informational Low
(F-2). The two disagree precisely on whether an owner's verbal attestation satisfies INV-6 limb (i).

**Claim under attack:** README (line ~116, ~208), `docs/walkthrough.md` (video block), `docs/model_setup.md`
(§6), and the `docs/evidence_map.md` AM-S6 audit mark `t2v` / `i2v` / `t2v_audio` **"GPU-verified" on both
FP8 and NVFP4**, on the strength of an owner quality attestation gathered *during* AM-S6 (Feng, 2026-07-26).

**Evidence:**
- INV-6: *"a mode is documented 'GPU-verified' only after (i) a recorded end-to-end run on the RTX 5090
  **and** (ii) the owner's recorded manual quality PASS — per format, per mode. Neither alone suffices."*
- The recorded evidence base (`docs/session_{2,3,4,5}/evidence/*`) has end-to-end run artifacts only for
  **t2i, reasoning, action**. There is **no recorded run** for `t2v`/`i2v`/`t2v_audio` — the pre-AM-S6
  `model_setup.md` said `i2v`/`t2v_audio` "remain unrun" and t2v was a "best-effort smoke" only.
- `docs/session_6/design.md` D2 concedes it: the owner "supplied (ii) verbally and attests (i) on their
  hardware" — a recollection, not a recorded run.
- Contract `out_of_scope`: AM-S6 *"reports the AM-S2..AM-S5 outcomes, it does not create them."* Promoting
  video from smoke-only to verified via an attestation collected in AM-S6 is arguably *creating* a result.

## Classification: **AMBIGUITY** (bordering SPEC_GAP)

The contract permits two readings of INV-6 limb (i) for an owner-run mode:
- **Reading A (adversarial verifier):** "a recorded end-to-end run" means recorded *evidence* of the run
  (the P-file standard used for t2i/reasoning/action). The owner's verbal "I ran it" is testimony, not that
  evidence → video is **not** yet GPU-verified → the README set is a *superset* of the recorded set → INV-6
  breached, R-13 breached (walkthrough asserts an owner-approved run that has no record), out_of_scope breached.
- **Reading B (sharded review):** the owner is the quality-gate authority (PRD Decision 6); an owner
  attestation "I ran X on my 5090 and it's high quality," once recorded and dated, is simultaneously the
  record of the run (i) and the quality verdict (ii) → INV-6 satisfied.

**Why not the other categories.** Not BUG (no code; the docs faithfully transcribe the owner's statement).
Not TEST_BUG (the honesty pass fired correctly; that is its job). Not ENVIRONMENT.

## Allowed vs forbidden next action

- **Forbidden:** silently keeping the "GPU-verified" video claim on Reading B (the honesty pass — which the
  gate requires to be clean — explicitly rejected it); **and** silently downgrading it against the owner's
  explicit "mark it GPU-verified" instruction. Neither unilateral move is legitimate.
- **Allowed / required:** STOP and get an explicit owner decision, because the conflict is between the
  owner's explicit instruction and the owner's own honesty invariant (INV-6) — only the owner can reconcile
  it. Then apply that decision consistently across README / walkthrough / model_setup / evidence_map and
  re-run the honesty pass.

## Options put to the owner (see the session message)
1. **[rec] Record a run line for the video modes** — the owner confirms the specifics of the runs they did
   (formats + what they saw: a valid ~720p clip; audio present for t2v_audio), which I capture as the
   INV-6 limb-(i) recorded run alongside the quality PASS. Keeps "GPU-verified", honestly satisfies INV-6.
2. **Honest partial status** — video = "owner quality-approved; full GPU-verified pending a recorded run";
   t2i/reasoning/action stay GPU-verified. Restores an honest video caveat. Most conservative.
3. **Explicit owner INV-6 exception** — the owner formally rules that a verbal owner attestation suffices
   for the video modes, recorded as an explicit owner decision (the INV-4-exception pattern). Keeps
   "GPU-verified" on the record as an owner override of INV-6's two-limb rule.
