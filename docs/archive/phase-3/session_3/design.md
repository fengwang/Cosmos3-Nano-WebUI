# UX-S3 Design — WebUI Declutter

Date: 2026-07-15
Authority: `docs/session_3_contract.yaml`, `docs/project_contract.md`, PRD FR-7/FR-8.

## Context

- Next.js App Router, `output: "standalone"` (server bundle, not static export).
  No `middleware.ts`.
- `/` → `app/page.tsx` (stale stub, links to `/gallery`), **outside** the
  `(studio)` route group.
- `/studio` → `app/(studio)/studio/page.tsx`, wrapped by
  `app/(studio)/layout.tsx` which provides `StudioProvider` (draft + active-job
  state) to everything in the group.
- Media rendered by `components/MediaPreview.tsx` (`<video|img class=.media>` /
  `<audio class=.audio>`), consumed by `ReviewPanel.tsx` (incl. the compare
  path) and `InspectPanel.tsx`. `.media { max-width:100%; max-height:60vh }`.
- Studio column: `.studio { display:flex; flex-direction:column; max-width:60rem }`.
- No committed e2e/a11y tests; `tests/e2e` does not exist. No vitest test or
  snapshot references any in-scope surface.

## Goals

- G1 Remove the Component Gallery entirely (route, nav item, home link) with no
  dead route and no dead link (FR-7, `EV-UX-GALLERY-GONE`).
- G2 Land users on the Studio from `/` (FR-7).
- G3 Enlarge the media viewport (both bounds) while staying responsive and
  keeping the compare-grid intact (FR-8, `EV-UX-MEDIA-ENLARGED`).

## Non-Goals

- Any server/API/proxy change; any Studio structural redesign; any
  design-system pruning; any change to Reasoning/Action/History; populating the
  e2e/a11y suite.

## Decisions

### D1 — `/` redirects to `/studio` (server `redirect()`)

`app/page.tsx` becomes a server component whose body is `redirect("/studio")`
(from `next/navigation`). **Why over rendering Studio at `/`:** the Studio needs
the `(studio)` group's `StudioProvider`; to render it at `/` we would hoist the
provider to the root layout (wrapping unrelated routes) or duplicate the studio
tree — both are scope creep and both trigger the route-group interaction the
contract flags. A redirect renders no Studio content at `/`, so no provider is
needed. **Why over `next.config` redirects:** page-level `redirect()` is
covered by the vitest suite (mock `next/navigation`) and keeps the change in
one in-radius file. `redirect()` throws a framework control-flow signal, so the
function has no reachable return — the component renders nothing itself.

### D2 — Nav item removed from the single source (`PrimaryNav.ITEMS`)

`PrimaryNav` derives the rail from the `ITEMS` array and computes the active
item with `pathname === href || pathname.startsWith(href + "/")`. Removing the
Gallery entry from `ITEMS` is sufficient; the active-item logic is unaffected
(the removed entry never matched anything else). Rail becomes
`Studio / Reasoning / Action / History`.

### D3 — Gallery deletion is a pure removal

`app/gallery/**` is imported by nothing, so `rm` of the directory is complete.
The design-system components it consumed stay exported (no design-system
overhaul; unused barrel exports do not fail lint/typecheck). This avoids the
"deleted a shared component the Studio still uses" adversarial case by not
touching `@/design-system` at all.

### D4 — Media enlargement via caps only (80rem / 80vh)

`.studio max-width: 60rem → 80rem` (~1280px ≈ native 720p width) and `.media
max-height: 60vh → 80vh`. Both remain **caps**, and `.media` keeps
`max-width: 100%`, so on any viewport narrower than the cap the media shrinks to
fit its column instead of overflowing. No fixed pixel dimension is introduced.
`.compareGrid` (`1fr 1fr`) is left untouched: inside the wider column each of
the two compared media is capped at 100% of its half-column and 80vh tall, so
the grid still renders side-by-side and each item stays responsive.

### D5 — Tests are content/behavior assertions, not visual snapshots

- Nav: render `PrimaryNav` and assert no `Gallery` link and that the four
  expected items render.
- Home: mock `next/navigation.redirect` and assert `Home()` calls it with
  `"/studio"`.
- Media dimensions: read the two CSS-module files from disk and assert the
  raised bounds (`80vh`, `80rem`), the absence of the old bounds
  (`60vh`/`60rem`), that `.media` retains `max-width: 100%`, and that no fixed
  `height:`/`width:` pixel rule was introduced on `.media`. CSS-module values
  are not observable in jsdom, so a file-content assertion is the deterministic
  regression guard; the Playwright computed-style check (task 5) confirms the
  real-browser effect.

## Risks / Trade-offs

- **[Redirect vs. route-group layout]** → D1 renders nothing at `/`, so the
  `(studio)` layout/provider never mounts at `/`; the hazard is structurally
  avoided.
- **[Removing `gallery.module.css` leaves a dangling import]** → only
  `app/gallery/page.tsx` imports it, and it is deleted in the same step;
  `tsc`/`eslint`/`build` would fail loudly on any stray import. Guarded by the
  full check suite + `rg` sweep.
- **[Enlarged media overflows narrow viewports / breaks compare-grid]** → caps
  + `max-width:100%`, compare-grid untouched; asserted by the CSS-content test
  and the Playwright resize check.
- **[URL change surprises deep links to `/`]** → `/` was a stub with no
  bookmarkable state; a 307 to `/studio` is the intended behavior, not a
  regression.

## Migration Plan

Per-task on `phase3-session-3`: (T2) remove gallery + nav item; (T3) redirect
`/`; (T4) enlarge media. Each task is red→green→commit. Rollback is a
`git revert` of the task commit; there is no data/state migration. No push.

## Open Questions

None. The two design decisions (redirect; 80rem/80vh) were resolved in the
interview and confirmed by the owner.
