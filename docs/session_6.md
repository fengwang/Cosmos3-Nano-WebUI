# Session 6 (AM-S6) - README "See it in action" + docs/walkthrough.md

Contract: `docs/session_6_contract.yaml`
Risk: low
Routing: single agent + deterministic checks + one review, **plus a mandatory adversarial no-over-claim / no-lost-caveat honesty pass**

## Objective

Teach each mode by example, honestly. Add a lean **README "See it in action"**
section (per-mode: example input → what to expect, in prose) that links a separate
**`docs/walkthrough.md`** holding the per-mode step-by-step with example input →
expected output and **image placeholders** (`![...](docs/images/…)`) the owner fills
after following the examples. Update the README's per-mode verification status to
reflect exactly what passed the owner gate in `AM-S2`..`AM-S5`, and reconcile the
BF16-base license discrepancy in `docs/model_setup.md`.

## Why This Session Exists

The examples and screenshots depend on the modes actually running and passing the
owner's quality gate — so this session runs **last** (`docs/project_contract.md`
§two-pass item 8, R-13). Promoting modes to "verified" in user-facing docs is the
exact over-claim hazard the phase-3/4 docs reviews caught, so despite being
docs-only it carries a mandatory honesty pass (routing §5, R-06). Two artifacts
keep the README lean (phase-4 ADHD posture) while giving the heavy visual
walkthrough its own file.

## In Scope

1. **README "See it in action".** A concise section: for each verified mode
   (Studio, Reasoning, Action) a one-line example input and what to expect,
   linking to `docs/walkthrough.md`. Lean; no inlined screenshots (FR-9).
2. **`docs/walkthrough.md`.** Per-mode step-by-step the owner can follow "one by
   one": the exact prompt/input, the command/UI action, the expected output
   (written against the real, owner-approved `AM-S2`..`AM-S5` runs), and an
   `![...](docs/images/<mode>-<example>.png)` placeholder under `docs/images/` for
   each step (`EV-AM-WALKTHROUGH-STRUCTURE`). No image binary is committed (INV-1);
   the owner adds images later.
3. **Honest per-mode status.** Update the README Features/Status per-mode
   verification to the final matrix from `AM-S5`'s handoff — only modes/formats
   with a recorded run + owner PASS are "GPU-verified"; anything that did not pass
   (e.g. an NVFP4-format limitation) is stated honestly, not hidden or over-claimed
   (`EV-AM-README-VERIFIED-SUBSET`, INV-6/INV-7). Reflect zero-BF16 default onboarding.
4. **License reconciliation.** Resolve the BF16-base license discrepancy (E-14)
   against the HF repo's own license page and state it once, consistently, in
   `docs/model_setup.md` (and the README table if present). Moot for the default
   path if BF16 is gone, but the docs must not carry a contradiction (R-09).
5. **Link + honesty verification.** Every internal link/anchor resolves
   (`EV-AM-DOCS-LINKS-RESOLVE`); the adversarial pass finds no surviving over-claim
   or lost caveat (the phase-4 `LX-S2` pattern).

## Out of Scope

- Any code, config, `deploy/**`, or WebUI change (docs only). If a doc example
  reveals a real product bug, file it — do not fix it here.
- Adding image binaries (placeholders only, INV-1).
- Changing any verified behavior or the per-mode results — this session **reports**
  the `AM-S2`..`AM-S5` outcomes, it does not create them.
- Editing `docs/archive/**`.

## Deliverables

- A README "See it in action" section linking `docs/walkthrough.md`.
- `docs/walkthrough.md` with a per-mode example (input → expected output) and
  `docs/images/…` placeholders; no committed images.
- README per-mode verification status updated to the final matrix; zero-BF16
  onboarding reflected; the BF16 license reconciled in `docs/model_setup.md`.
- The honesty pass result recorded; `docs/evidence_map.md` /
  `docs/risk_register.md` closed out (R-06/R-09/R-13).

## Checks

```bash
# Deterministic doc checks (host):
rg -n "GPU-verified" README.md                               # subset of owner-passed modes (INV-6)
rg -n "docs/images/" docs/walkthrough.md                     # every image is a placeholder under docs/images/
git status --porcelain docs/images                           # no committed image binary
# Relative-link + anchor resolver over README.md, docs/walkthrough.md, docs/model_setup.md → all resolve.
```

## Exit Criteria

- `GATE-AM-S6-DOCS` passes: the README has a "See it in action" section linking
  `docs/walkthrough.md`; the walkthrough has per-mode example input → expected
  output + `docs/images/…` placeholders with no committed binary; the README
  verified set is a subset of what passed the owner gate (INV-6); the BF16-license
  discrepancy is reconciled; every internal link resolves; the adversarial honesty
  pass finds no surviving over-claim or lost caveat.

## Handoff

The phase is complete: all three modes GPU-verified (owner PASS) and default-on in
every stack/format where they passed, off quantized-only checkpoints (no BF16 in
the default path), `t2i` non-regressed on both formats, and the README +
`docs/walkthrough.md` teaching each mode honestly with owner-fillable image
placeholders. Record any residual owner-decided limitation (e.g. an NVFP4-format
gap) and archive the phase-5 (`AM`) pack per the project's archival convention.
