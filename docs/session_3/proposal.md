# UX-S3 Proposal — WebUI Declutter

Date: 2026-07-15
Source: `docs/session_3/brainstorming.md` (owner-approved validated design).

## Motivation

Reshape the WebUI first-run for a task-first media tool: remove the developer
Component Gallery (a design-system showcase surfaced as a primary nav item),
land users directly on the Generation Studio instead of a stale stub, and make
the generated media the visual centerpiece — all without a structural redesign
of the Studio (PRD §1, §3.6; FR-7, FR-8; E-10, E-11).

## Specific Changes Agreed

1. **Delete** `webui/app/gallery/` (`page.tsx`, `gallery.module.css`) — the
   route and its styles.
2. `webui/app/_components/PrimaryNav.tsx`: remove the
   `{ href: "/gallery", label: "Gallery" }` entry so the rail is
   `Studio / Reasoning / Action / History`.
3. `webui/app/page.tsx`: replace the stale stub (whose only content links to
   the gallery) with a server component that `redirect("/studio")` — removing
   the dead home link in the same edit.
4. `webui/components/MediaPreview.module.css`: `.media` `max-height`
   `60vh → 80vh` (keep `max-width: 100%`).
5. `webui/app/(studio)/studio/page.module.css`: `.studio` `max-width`
   `60rem → 80rem`.
6. Co-located tests for every behavior change (nav has no Gallery; `/`
   redirects to `/studio`; both media bounds raised; responsiveness preserved).

## Landing Decision (R-07) — Recorded

`/` **redirects** to `/studio` via `redirect("/studio")` in the root
`app/page.tsx` server component. Chosen over rendering the Studio at `/`
because the Studio requires the `(studio)` route group's `StudioProvider`;
redirecting means `/` renders no Studio content and needs no provider,
structurally avoiding the route-group interaction the contract flags as a
failure mode. `next.config` is `output: "standalone"` (not static export), so a
runtime redirect is valid.

## Capabilities

### Modified capabilities

- **`webui-declutter`** — the Component Gallery route/showcase is REMOVED; the
  primary navigation no longer offers Gallery; the home route `/` redirects to
  the Studio (previously a stale stub linking to the gallery). Spec:
  `specs/webui-declutter.md`. Refs FR-7.
- **`media-viewport`** — the generated-media viewport is enlarged (studio
  container `max-width` `60rem → 80rem`; `MediaPreview` `max-height`
  `60vh → 80vh`) while staying responsive and keeping the Review compare-grid
  intact. Spec: `specs/media-viewport.md`. Refs FR-8.

## Impact

- **Code**: delete `webui/app/gallery/**`; edit `webui/app/page.tsx`,
  `webui/app/_components/PrimaryNav.tsx`,
  `webui/components/MediaPreview.module.css`,
  `webui/app/(studio)/studio/page.module.css`. `studio.module.css` is in the
  blast radius but is **not** expected to change (compare-grid left intact).
- **APIs**: none. This is a presentation-only session — no request/response
  shape, no proxy/BFF behavior, no server code (INV-7, contract invariant "no
  public API interaction changes").
- **Dependencies**: none added.
- **Routing**: `/gallery` ceases to exist; `/` becomes a redirect to `/studio`.
  No other route changes; Reasoning/Action/History untouched.
- **Tests**: new co-located `PrimaryNav`, home-redirect, and media-dimension
  tests; no existing test/snapshot references these surfaces, so nothing breaks.
- **Evidence/docs**: `docs/session_3/**`, `docs/evidence_map.md`,
  `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/handoff.md`.

## Non-Goals (from contract)

- Auth (UX-S1), generation defaults (UX-S2), README/docs (UX-S4).
- A structural redesign of the Studio, a marketing/landing page beyond the
  redirect, or a design-system overhaul (including pruning now-unused exports).
- Removing/rewriting the Reasoning / Action / History routes.
- Populating the scaffolded (empty) e2e/a11y suite.
