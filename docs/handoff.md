# Session Handoff

## State Snapshot
- **Session:** UX-S4 — README / Docs Friendliness: features-first README, dev/CI
  owned by CONTRIBUTING, slim honest Status & security callout, all links resolve
  (risk: low). **Final session of the phase.**
- **Branch:** `phase3-session-4`
- **Last commit:** the UX-S3 close commit (`db5d615`) is the branch base; UX-S4
  work is staged in the working tree (see "Changed files") pending the owner's
  commit(s).
- **Changed files (deliverable):** `README.md` (restructured features-first),
  `CONTRIBUTING.md` (now the sole owner of dev/CI; tone aligned), `SECURITY.md`
  (`R-16`→`R-01`, guardrails-off note, tone aligned), `webui/app/layout.tsx`
  (copy-only: stale "Session 8"/"S9" → accurate metadata). Docs: `docs/session_4/**`
  (full refining pack + sharded_review + adversarial_verification),
  `docs/evidence_map.md` (E-24..E-26), `docs/risk_register.md` (R-08/R-09 resolved),
  `docs/eval_seed_cases.md` (UX-S4 result), `docs/eval_corpus/ux-s4-docs-friendliness.md`,
  this handoff.
- **Checks run:** relative-link resolver over README/SECURITY/CONTRIBUTING → 0
  unresolved (incl. in-page anchors); `rg "release_checklist|R-16" README.md
  SECURITY.md` → clean; `rg "COSMOS3_API_KEY|X-API-Key" README.md SECURITY.md` →
  clean; spec-derived asserts (features precede quickstart; all 6 quickstart
  essentials present; no dev block in README, present in CONTRIBUTING; 5 posture
  facts present); from `webui/` `pnpm build && pnpm lint && pnpm typecheck &&
  pnpm test` → green (**42 files / 214 tests**); 3-reviewer 6-axis sharded review
  (1 High + 2 Medium, all fixed); fresh-context adversarial verifier **PASS**.
- **Checks not run:** no API/CPU `pytest` (docs-only; no server/schema change); no
  external URL reachability (badges/CI links — offline, out of scope); no GPU smoke
  (none applies to docs); no PR/push (owner integrates).
- **Current status:** `GATE-UX-S4-DOCS` **PASS**. README is features-first with a
  runnable few-minute quickstart, dev/CI lives in CONTRIBUTING, the slim honest
  Status & security callout is accurate against the evidence, and every internal
  link resolves. Blast-radius compliant (only the four allowed files + docs).

## Narrative Context
UX-S4 reframes the docs for the trusted-LAN appliance posture settled by
UX-S1/S2/S3. The README now leads with what the project does and a runnable
~5-minute quickstart (no auth to configure; 720p + curated-negative-prompt
defaults out of the box), relocates all development/CI detail to `CONTRIBUTING.md`
(it was already a superset — the change is de-duplication, so nothing was lost),
tightens Checkpoint setup to point at `docs/model_setup.md`, and consolidates
every honesty caveat into one slim "Status & security" section (no-auth,
loopback default, root-equivalent Docker socket, guardrails-off, per-mode
verification, 720p FP8/NVFP4 VRAM advisory). The two dangling references were
fixed (README `release_checklist.md` bullet dropped; `SECURITY.md` `R-16`→live
`R-01`), and the one allowed non-doc edit corrected stale "Session 8/S9" copy in
`webui/app/layout.tsx`. The full-treatment review paid for itself: it caught a
**false causal claim** I introduced ("guardrails required for 720p to fit 32 GB"),
which the evidence (E-17/E-19) contradicts — fixed to the honest reason.

## Decision Log
| Decision | Chosen | Rejected | Reason | Contract Ref |
|---|---|---|---|---|
| Verify depth (low-risk session) | Full treatment (refining pack + 6-axis sharded review + adversarial verifier) | Streamlined; minimal | Matches the UX-S3 precedent; caught a real honesty defect (F1) | Interview Q1 |
| README tone / caveat placement | Relaxed; all caveats in one "Status & security" section at the end + light top pointer | Honesty banner up top; keep the beta WARNING | "slim honest callout" + "tone relaxed, honesty retained" (PRD §3.2) | Interview Q2; design D1 |
| Dangling references | Drop README "Release readiness" bullet; repoint `SECURITY.md` `R-16`→live `R-01` | Repoint both to archive; drop both | R-01 is the accurate live risk (carries R-16 forward); a user README needn't link an archived checklist | Interview Q3; design D3 |
| Guardrails-off framing (F1 fix) | Honest reason: `cosmos_guardrail` not bundled + trusted-LAN posture | "required for 720p to fit 32 GB" (my first draft) | E-17: the 32 GB fit is offload+tiling+shm, not guardrails; E-19: guardrails-on crashes (missing model) | Sharded review F1 |
| Sibling-doc tone (F3 fix) | Align SECURITY.md/CONTRIBUTING.md opening to "local self-hosted preview" | Leave "beta / research preview" | 2-reviewer finding; PRD Decision 2 puts SECURITY.md in the retone scope; both already in the edit set | Sharded review F3 |

## Next Priority Queue
1. **Phase complete.** `GATE-UX-S1-AUTH` … `GATE-UX-S4-DOCS` all PASS. The
   remaining phase-level action is the owner's integration (commit/merge of the
   four `phase3-session-*` branches) and the standing `MIG-S8` manual GPU gate for
   the non-t2i modes.
2. **Optional future UX polish (out of every current session's scope):** the
   pre-existing app-shell horizontal overflow at ≤~651px viewport
   (`webui/app/globals.css` `.app-*` + `app/layout.tsx` layout), flagged by UX-S3.
3. **Optional doc-lint (from the UX-S4 eval seed):** a committed check asserting
   the quickstart contains the essential steps and that Features "verified" rows ⊆
   the evidence-map verified modes — the two deterministic sweeps do not catch a
   dropped step or a per-mode over-claim.

## Warnings And Gotchas
- **Environment:** ESLint output run through the `rtk` proxy prints a spurious
  "JSON parse failed: EOF" when there are zero findings (empty output). Confirm
  the true exit code with `rtk proxy pnpm lint; echo $?` — `0` = clean.
- **Known failing tests:** none.
- **Deferred risks:** **R-05** (720p FP8 headroom is thin at higher frame counts;
  49-frame default fits via layer-wise offload; NVFP4 has more headroom) — now
  documented honestly in the README/SECURITY callout. **R-16** (Docker-socket
  privilege hardening) stays deferred/archived; the live **R-01** carries it
  forward and SECURITY.md points there. **Guardrails-off** default is documented,
  not hardened (out of scope, `MIG-S8`).
- **Files future sessions must not casually edit:** `schemas/openapi.json` is
  generated (never hand-edit); `docs/archive/**` is historical; `webui/app/layout.tsx`
  metadata should track the README subtitle if the product blurb changes.

## Handoff to the owner (contract handoff_requirements)
- `docs/risk_register.md`, `docs/evidence_map.md`, and `docs/eval_seed_cases.md`
  now reflect the closed state of `UX-S1`..`UX-S4`: R-08/R-09 resolved (UX-S4),
  E-24..E-26 recorded, `EV-UX-DOCS-LINKS-RESOLVE` PASS logged. R-05 VRAM caveat
  and deferred R-16 are recorded above and in the register.
- The docs describe the shipped reality: `/` → 307 → `/studio`; nav rail is
  Studio/Reasoning/Action/History (no Gallery); media viewport 80rem/80vh; no
  auth; 720p video default on FP8/NVFP4; guardrails-off.

## Eval Seeds
- **High-value catch (sharded review):** a false causal claim ("guardrails
  required for 720p to fit 32 GB") passed my own drafting but was refuted by the
  project's own evidence map. → seed `docs/eval_corpus/ux-s4-docs-friendliness.md`
  §1 (a "why" claim in user docs must trace to an evidence row; cross-check causal
  statements, not just link/token sweeps).
- **Coverage gap (missed by deterministic checks):** the `rg` sweeps + link
  resolver do not catch a dropped quickstart step or a per-mode over-claim. →
  §2 (candidate doc-lint).
- **Environment note:** the `rtk`-proxied ESLint "JSON parse failed: EOF" false
  alarm on a clean lint. → §3 (classify ENVIRONMENT; confirm exit code).
