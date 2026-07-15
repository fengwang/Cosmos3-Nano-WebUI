# UX-S3 Sharded Review

Date: 2026-07-15
Diff reviewed: `7bf5388..HEAD` (session commits). Three independent, read-only
reviewers over the contract's 6 axes (grouped): correctness+tests,
security+architecture, readability+performance. Deduplicated below.

## Verdict

**No Critical/High findings.** All four contract `adversarial_cases` refuted;
`blast_radius` compliant; INV-7 (same-origin BFF) and "no public API interaction
change" held; the 3 new specs verified to actually run (not silently skipped).
Two minor test-quality findings + one doc inaccuracy — all fixed (test/doc only,
no behavior change).

## Findings

### F1 — Low (Tests) — `webui/app/page.test.tsx` — FIXED
- Evidence: the home test asserted `redirect("/studio")` was called but not the
  absence of rendered output; a regression that both redirected *and* returned a
  dead link would still pass.
- Violated clause: spec `webui-declutter.md` scenario "The home route contains
  no dead gallery link".
- Fix: also assert `Home()` returns `undefined` (renders no JSX) — a returned
  markup regression now makes it defined and fails.
- Confidence: Med (behavior correct today; this closed a coverage gap).

### F2 — Nit (Tests) — `webui/components/MediaPreview.dimensions.test.ts` — FIXED
- Evidence: the fixed-px guard `/[^-]height:\s*\d+px/` requires a char before
  `height`, so a `height:` as the file's first characters would be missed
  (cannot occur in practice — CSS props are always inside a rule block).
- Fix: use a lookbehind boundary `/(?<![-\w])height:\s*\d+px/` (and width) so it
  matches a standalone property at any position while still ignoring
  `max-height`/`line-height`.
- Confidence: High the gap exists; Low it could ever trigger.

### F3 — Low (Docs/accuracy) — `docs/session_3/brainstorming.md` — FIXED
- Evidence: Decision Axis 3 listed `ProgressRing` among components "the gallery
  was the sole consumer of", but `ProgressRing` is still used by
  `components/studio/RunPanel.tsx` and `components/action-viewer/ActionWorkspace.tsx`.
- Impact: none on code (nothing was pruned); a false claim in a rationale doc.
- Fix: reword to not over-claim which components became unused; the point stands
  (leaving `@/design-system` untouched avoids the "delete a shared component"
  adversarial case).

## Informational (not findings; out of scope / out of blast radius)

- `webui/app/layout.tsx:12,37` still says "Session 8"/"S9" in the page
  `metadata.description` and a comment. Arguably stale, but `layout.tsx` is
  **outside** the UX-S3 `blast_radius.allowed_files` and was not touched; editing
  it would breach the contract. Flagged for a future session (UX-S4 docs/metadata).
- A pre-existing horizontal overflow of the app-shell (`header.app-header` /
  `main.app-main` in `app/globals.css` + `app/layout.tsx`) at ≤~651px viewport
  width exists independently of this session (those files are untouched by the
  diff). The UX-S3 media enlargement itself is responsive (studio container 347px
  at 375px; media `max-width:100%`). See `webui_smoke.md`.
