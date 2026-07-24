# UX-S4 Sharded Review

Date: 2026-07-16
Diff reviewed: working tree vs `HEAD` — `README.md`, `CONTRIBUTING.md`,
`SECURITY.md`, `webui/app/layout.tsx` (+ the `docs/session_4/**` pack).
Three independent, read-only reviewers over the contract's 6 axes (grouped):
correctness+tests, security+architecture, readability+performance. Deduplicated
below.

## Verdict

**One High + two Medium, all fixed** (docs-only; no behavior change). All five
contract `adversarial_cases` refuted; `blast_radius` compliant (only the four
allowed files + `docs/session_4/**`); no residual auth prose (R-09); every
internal link resolves; per-mode claims match `docs/evidence_map.md`. The High
finding was a factual/honesty defect I introduced (a false VRAM causal claim),
caught precisely because the owner chose the full treatment for this low-risk
session.

Deterministic re-check after fixes: doc resolver + both `rg` sweeps **PASS**;
quickstart essentials + posture facts intact; WebUI suite unaffected (fixes were
docs-only; `layout.tsx` unchanged since its green run).

## Findings

### F1 — High (Correctness / Security-honesty) — `README.md`, `SECURITY.md` — FIXED
- Evidence: the guardrails bullet claimed guardrails are disabled
  "**(required for the 720p video default to fit 32 GB)**". The project's own
  evidence contradicts this: E-17 shows FP8 720p/49f fits at peak 14,665 MiB and
  lists the fit requirements as `--enable-layerwise-offload` + `--vae-use-tiling`
  + `shm_size 16gb` — **not** guardrails; `deploy/docker-compose.fp8.yml:18`
  states `--no-guardrails` is used because "`cosmos_guardrail` is not bundled"
  and for the trusted-LAN posture; E-19 notes guardrails-on would **crash**
  (missing model), not OOM.
- Violated clause: INV-4 / the "slim honest callout" acceptance criterion +
  `failure_modes_to_watch` "per-mode/verification claims drifting ahead of
  evidence"; adversarial case "a slimmed security note becomes dishonest".
- Impact: invents a technical justification the evidence refutes — a reader who
  re-enables guardrails expecting an OOM would be misled; undercuts the honesty
  the section exists to provide.
- Fix: reworded both files — guardrails are off because `cosmos_guardrail` is not
  bundled and by trusted-LAN design; output is unfiltered. Dropped the "required
  to fit 32 GB" causal claim.
- Confidence: High (grounded in E-17/E-19 + the shipped compose comment).

### F2 — Medium (Correctness / internal consistency) — `README.md` — FIXED
- Evidence: the 720p bullet read "FP8 headroom is thin (measured peak ≈ 14.7 GB;
  NVFP4 ≈ 18.5 GB), so prefer **NVFP4** for more headroom" — self-contradictory,
  since a *lower* FP8 peak (14.7 < 18.5) means *more* free headroom at the shipped
  49-frame default. The real rationale (E-08/R-05): FP8's 49-frame fit depends on
  fragile layer-wise offload and sits near the 32 GB ceiling at higher frame
  counts (189-frame example peaked 31,957 MiB), whereas NVFP4 fits without offload.
- Violated clause: `docs-integrity` "720p VRAM advisory is honest"; strong
  single-reviewer evidence (a factual contradiction vs E-17/E-18/R-05).
- Impact: a reader comparing the two peaks concludes FP8 is safer and distrusts
  the recommendation.
- Fix: state that the 49-frame default fits comfortably (peaks ≈14.7/≈18.5 GB) and
  attribute "prefer NVFP4" to FP8's offload dependency + tightening at higher
  frame counts — no number change (numbers already matched E-17/E-18).
- Confidence: High.

### F3 — Medium (Readability / cross-doc tone consistency) — `SECURITY.md:3`, `CONTRIBUTING.md:3` — FIXED
- Evidence: after the README was retoned to "local self-hosted preview", the two
  sibling docs a reader reaches from the README's "Project" section still opened,
  in their first sentence, with "**beta / research preview**" — the exact framing
  the phase relaxed. Flagged by 2 of 3 reviewers (security+architecture as a Nit;
  readability as Medium).
- Violated clause: PRD Owner Decision 2 ("The README and `SECURITY.md` keep a
  slimmed but honest note … tone relaxed"); the confirmed Q2 tone decision.
- Impact: the product describes itself two different ways depending on which door
  the reader enters; undercuts the credibility the retone was meant to build.
- Fix: replaced the opening self-descriptor in both with "local self-hosted
  preview" (both files already in the edit set + blast radius); the honest
  "not hardened for untrusted / internet-facing use" statement is retained.
  Incidental non-framing "beta" mentions (`SECURITY.md:29` "beta project …
  without a formal SLA"; `CONTRIBUTING.md` "beta limitations") left as-is — they
  are accurate maintenance-posture descriptions, not the alarmist self-label
  (reviewer-rated Low/optional).
- Confidence: High.

## Informational (not findings)

- **Coverage gap (Tests axis, not a diff defect):** the two `rg` sweeps + the
  link resolver do **not** catch a dropped quickstart step or a per-mode
  over-claim; those rely on human/adversarial review (covered here + by the
  verifier). Recorded as an eval seed for a future doc-lint
  (`docs/eval_corpus/ux-s4-docs-friendliness.md`).
- **Blast radius / leaks:** `git diff --name-only HEAD` = exactly the four allowed
  files; no `/data/models` absolute path, host, or token introduced (NFR-1/INV-1).
- **`layout.tsx`:** copy-only (metadata `description` + one comment); no render/
  behavior change; WebUI `build/lint/typecheck/test` green (42 files / 214 tests).
