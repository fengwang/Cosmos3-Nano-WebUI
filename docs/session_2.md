# Session 2 (LX-S2) - ADHD-Friendly README Rewrite

Contract: `docs/session_2_contract.yaml`
Risk: low
Routing: single_agent + one review, **plus a mandatory adversarial
no-over-claim / no-lost-caveat pass** (honesty hazard, `R-04`)

## Objective

Rewrite `README.md` into an ADHD-friendly on-ramp for a reader who skims: a
punchy but factually-true hook, a copy-paste TL;DR that preserves the runnable
quickstart, a small Mermaid "how it works" map, collapsible `<details>` for
verbose/advanced/troubleshooting content, sparing GFM callouts, and in-page
navigation — while keeping every current fact and relocating (never deleting or
hiding) the honest Status & security caveats to the end. Single file; depth
stays linked to `CONTRIBUTING.md` / `docs/model_setup.md`. Runs last, on the
settled post-`LX-S1` state (idle keep-warm now 30 min).

## Why This Session Exists

The current README is the phase-3 `UX-S4` output: honest and features-first,
but a flat ~188-line document with a top honesty banner, no visual map, no
progressive disclosure, and no in-page navigation (`docs/evidence_map.md`
E-09). For the ADHD reader the three research reports describe — reduced
working memory, executive-function friction at task initiation, high
distractibility — that on-ramp is heavier than it needs to be. The reports
converge on a fix (lead with what/why, chunk, tabulate, navigate, minimize
setup friction; E-10) and diverge on several points this blueprint has already
resolved (E-11..E-16). This session applies the agreed structural moves and the
owner's punchy-hook decision.

It is **low** risk (documentation-only), but routed with a mandatory
adversarial honesty pass: the owner-chosen punchier hook with caveats moved to
the bottom raises the over-claim hazard (`R-04`), and the phase-3 precedent
shows a "low-risk" docs session's review is exactly what caught a real false
claim. Honesty is a hard invariant here (`INV-6`), not a preference.

## Deep-study inputs

- **Consensus adopted (E-10):** lead with what/why; aggressive chunking (short
  sentences, ≤~4-line paragraphs, one idea per paragraph); tables for
  structured comparisons; headings → in-page TOC/anchors; exact copy-paste
  commands in fenced blocks; minimize setup friction.
- **Disagreements resolved (chosen paths):** punchy true hook then TL;DR
  (E-11); **no** Codespaces / cloud path — local RTX 5090 required (E-12);
  `<details>` for verbose content only, never for caveats (E-13); typography
  specs treated as non-normative — GitHub controls README rendering (E-14); no
  bionic reading (E-15); single README kept lean via `<details>` + links, not a
  multi-doc split (E-16).
- **Techniques adopted:** one ≤7-node Mermaid map (E-17); sparing GFM callouts
  (E-18); sparing purposeful emoji, never the sole signal (E-19).

## In Scope

1. **Hook + TL;DR.** Open with a factually-true one/two-line hook (what it
   makes, locally, on your own GPU), immediately followed by a copy-paste
   TL;DR / fastest-path that preserves the runnable quickstart: clone →
   pinned public `hf download` → `make build` → `make up-fp8` → `make health`
   → open the Studio (INV-5). Drop the current top honesty banner (its content
   moves to the bottom section, not away).
2. **Visual map.** Add one small (≤7-node) Mermaid diagram of the real
   WebUI → API → generation-container flow (browser → Next.js BFF → FastAPI →
   orchestrator → vLLM-Omni container), faithful to `deploy/**` +
   `api/orchestrator/**` (INV-8, E-17).
3. **Progressive disclosure.** Move verbose/advanced/troubleshooting content
   into collapsible `<details>`/`<summary>` blocks (blank line after
   `</summary>`), keeping the default view short. Never collapse essential
   setup or the caveats (E-13, `R-09`).
4. **Navigation + chunking.** Add in-page anchors / a short TOC; tighten prose
   into short chunks; keep tables for the features and checkpoint matrices;
   use sparing callouts and sparing, purposeful section emoji.
5. **Honest caveats, relocated and visible.** Keep the **full** Status &
   security content in the README, visible (not inside `<details>`), at the
   end: no application auth; loopback default with LAN as an explicit opt-in;
   root-equivalent Docker socket; guardrails-off; honest per-mode verification
   (only text→image GPU-verified end to end; other modes CPU-tested + `MIG-S8`
   gate). Add the new 30-min idle keep-warm behavior from `LX-S1`.
6. **Link hygiene.** Every internal link/anchor resolves; depth continues to
   link to `CONTRIBUTING.md` and `docs/model_setup.md` (not inlined); no
   cloud/Codespaces call to action anywhere (E-12, `R-06`).

## Out of Scope

- Any code, config, or WebUI change (the timeout is `LX-S1`); any GPU work.
- Splitting the README into new documents, or creating a landing/marketing
  site; adding a Codespaces / DevContainer / remote-dev path.
- Committing any image, GIF, or other binary; the visual map is text (Mermaid).
  A demo image, if any, reuses an existing repository asset (NFR-1).
- Rewriting `CONTRIBUTING.md` / `SECURITY.md` / `docs/model_setup.md` substance
  (link-correctness only, if a link target must be adjusted).
- Editing `docs/archive/**`.

## Deliverables

- A rewritten `README.md`: punchy true hook + copy-paste TL;DR; a ≤7-node
  Mermaid map; collapsible `<details>` for verbose content; sparing callouts;
  in-page navigation; tighter chunks — single file, depth linked out.
- The full Status & security section preserved, visible, and at the end, with
  the five posture facts and the new 30-min idle behavior.
- Every "GPU-verified" claim a subset of the evidence-map verified modes
  (text→image only); every internal link resolving; no cloud CTA.
- A recorded adversarial no-over-claim / no-lost-caveat pass result.

## Deterministic Checks

```bash
# every relative link + in-page anchor in README.md resolves to an existing target
rg -in "codespace|devcontainer|open in cloud|launch in the cloud" README.md   # expect: none
rg -n "make (build|up-fp8|health)" README.md   # expect: present; cross-check each target in Makefile
# structure asserts: a mermaid fence, a <details>/<summary>, a TL;DR block, a visible
# Status & security section in the final third (not inside <details>)
# honesty assert: README "GPU-verified" claims are a subset of the evidence-map verified set (t2i only)
```

## Exit Criteria

- `GATE-LX-S2-README` passes.
- README opens with a factually-true hook + runnable TL;DR
  (`EV-LX-README-RUNNABLE-QUICKSTART`); contains a ≤7-node Mermaid map,
  `<details>` for verbose content, and in-page navigation
  (`EV-LX-README-STRUCTURE`).
- The full Status & security section is present, visible, and at the end, with
  the five posture facts and the 30-min idle behavior
  (`EV-LX-README-HONEST-CAVEATS`).
- Only text→image is claimed GPU-verified (`EV-LX-README-VERIFIED-SUBSET`);
  every internal link resolves and there is no cloud CTA
  (`EV-LX-DOCS-LINKS-RESOLVE`).
- The adversarial honesty pass records no surviving over-claim or lost/hidden
  caveat.

## Handoff

Confirm `docs/evidence_map.md` / `docs/risk_register.md` /
`docs/eval_seed_cases.md` reflect the closed `LX-S1`/`LX-S2` state, including
the honesty-pass result and any residual note (the out-of-scope WebUI SSE
heartbeat, `R-03`/E-08). This closes the phase-4 blueprint's session set.
