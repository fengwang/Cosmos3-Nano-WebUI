# Session 3 (UX-S3) - WebUI Declutter: Remove Gallery, Land on Studio, Enlarge Media

Contract: `docs/session_3_contract.yaml`
Risk: low
Routing: single_agent (single agent + deterministic checks + one review)

## Objective

Declutter the WebUI for a task-first experience: remove the design-system
Component Gallery entirely, land users on the Studio, and enlarge the
generated-media viewport — without a structural redesign of the Studio.

## Why This Session Exists

The `/gallery` route is a design-system showcase surfaced as a primary nav
item (`docs/evidence_map.md` E-10), and the home page is a stale stub whose
only content links to it (`webui/app/page.tsx:10`). For a media tool the
generated-media viewport is also small — capped at `60vh` inside a `60rem`
column (E-11). Removing the gallery, redirecting `/` to the Studio, and
enlarging the media area is low risk: no committed e2e/a11y test targets the
gallery (`tests/e2e` does not exist), so removal has no test fallout.

## In Scope

1. Remove the gallery route directory `webui/app/gallery/` (`page.tsx`,
   `gallery.module.css`).
2. Remove the gallery nav item (`webui/app/_components/PrimaryNav.tsx:14`) so
   the rail is Studio / Reasoning / Action / History.
3. Replace the stale home page: make `/` render or redirect to the Studio
   (`webui/app/page.tsx`), leaving no dead link.
4. Enlarge the generated-media viewport: raise `MediaPreview` `max-height`
   above `60vh` and the studio container `max-width` above `60rem`
   (`webui/components/MediaPreview.module.css`,
   `webui/app/(studio)/studio/page.module.css`), keeping the layout responsive
   on small screens and the Review compare-grid
   (`webui/components/studio/studio.module.css`) intact. Exact values are a
   design detail; the intent is media-as-centerpiece, not a redesign.

## Out of Scope

- Auth (`UX-S1`), generation defaults (`UX-S2`), README (`UX-S4`).
- A structural redesign of the Studio, a new landing/marketing page beyond the
  redirect, or a design-system overhaul.
- Removing or rewriting the Reasoning / Action / History routes.
- Populating the scaffolded (currently empty) e2e/a11y suite.

## Deliverables

- Gallery route, nav item, and home link removed; `/` routes to the Studio.
- An enlarged media viewport (both bounds raised vs the `60vh`/`60rem`
  baseline), responsive, compare-grid intact.
- Clean `rg -i 'gallery'` in `webui/app`/`webui/components` apart from the
  unrelated `HistoryList` "history/gallery" wording.

## Deterministic Checks

```bash
rg -i "gallery|/gallery" webui/app webui/components   # only the HistoryList comment remains
# from webui/
pnpm build && pnpm lint && pnpm typecheck && pnpm test
```

## Exit Criteria

- `GATE-UX-S3-WEBUI` passes.
- No `/gallery` route, nav item, or link; `/` renders/redirects to the Studio
  (`EV-UX-GALLERY-GONE`).
- Media viewport enlarged, responsive, compare-grid intact
  (`EV-UX-MEDIA-ENLARGED`).
- WebUI build/lint/typecheck/test green.

## Handoff

Note the final media-viewport dimensions and the landing behavior for the
README screenshots/description that `UX-S4` will write.
