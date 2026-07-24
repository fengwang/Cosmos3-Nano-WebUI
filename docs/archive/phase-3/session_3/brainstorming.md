# UX-S3 Brainstorming — WebUI Declutter

Date: 2026-07-15
Risk: low · Routing: single_agent (single agent + deterministic checks + one review)

The design exploration was front-loaded into the interview-me phase; this
document records the approaches considered per decision axis, their trade-offs,
and the owner-validated outcome (explicit "yes", 2026-07-15).

## Context Explored

- The `/gallery` route (`webui/app/gallery/page.tsx` + `gallery.module.css`) is
  a self-contained design-system showcase. It imports `Card, Input, NavRail,
  PillButton, ProgressRing, Sheet, Surface` from `@/design-system` but is
  imported by nothing (verified: `rg gallery app components lib`). Removing it
  cannot break another consumer (E-10).
- The home page `webui/app/page.tsx` is a stale stub whose sole actionable
  content is a `<Link href="/gallery">` (E-10). Removing the gallery leaves it
  with a dead link, so the landing must be reworked in the same session.
- The primary nav (`webui/app/_components/PrimaryNav.tsx:14`) lists
  `Studio / Reasoning / Action / History / Gallery`; the Gallery item must go.
- The generated-media viewport is capped at `max-height: 60vh`
  (`webui/components/MediaPreview.module.css`) inside a `max-width: 60rem`
  studio column (`webui/app/(studio)/studio/page.module.css`) (E-11). Since
  UX-S2 the default artifact is a 1280×720 video, which at a 60rem (~960px)
  column is downscaled.
- Routing facts that constrain the landing decision: `next.config.mjs` uses
  `output: "standalone"` (a real server, **not** static export — runtime
  redirects are valid); there is **no** `middleware.ts`; `/` lives at
  `app/page.tsx` **outside** the `(studio)` route group, so it does not receive
  the group's `StudioProvider`. There is a precedent for `next/navigation`
  control functions (`app/sse-probe/page.tsx` uses `notFound()`).
- No committed test or snapshot targets the gallery, the home page, the nav
  items, or the media dimensions (verified: `rg` over `*.test.*`, no `*.snap`).
  So removal/enlargement has **no** test fallout (E-10/E-11).

## Decision Axis 1 — How `/` lands on the Studio

| Approach | Summary | Trade-off |
|---|---|---|
| **A. `redirect("/studio")` in `app/page.tsx`** (chosen) | Root page is a server component that calls `redirect()` from `next/navigation`. | `/` never renders Studio content, so it needs no `StudioProvider` → sidesteps the route-group interaction the contract flags. Cleanly unit-testable (mock `redirect`). URL becomes `/studio`. |
| B. `next.config` `redirects()` | Config-level `{ source: "/", destination: "/studio", permanent: false }`. | Also avoids the provider issue, but hides routing in config, is not covered by the vitest suite, and splits the change across a forbidden-by-default file. |
| C. Render the Studio at `/` | Move/duplicate the studio page under `/`, or hoist `StudioProvider` to the root layout. | Keeps `/` as the URL, but hoisting the provider wraps **every** route (chat/action/history) in studio state — scope creep — and is exactly the `(studio)`-layout-group interaction the contract lists as a failure mode. |

**Chosen: A.** Lowest blast radius, testable, and it structurally avoids the
route-group hazard. Owner-selected.

## Decision Axis 2 — How large to enlarge the media viewport

Both bounds stay **caps** (`max-height` in `vh`, `max-width` in `rem`) with the
media keeping `max-width: 100%`, so narrow viewports always shrink the media
rather than overflow — this defuses the "fixed pixel value overflows narrow
viewports" adversarial case regardless of magnitude.

| Approach | container / media | Trade-off |
|---|---|---|
| Conservative | 72rem / 72vh | A 1280px video is still capped to ~1152px (still downscaled). |
| **Moderate** (chosen) | **80rem / 80vh** | 80rem ≈ 1280px = native 720p width, so a default video is shown near 1:1; 80vh leaves room for native controls + caption on a laptop. |
| Bold | 90rem / 88vh | Fills a wide monitor, but on a 13–14" laptop the media may need scrolling to see controls + caption together. |

**Chosen: Moderate (80rem / 80vh).** Owner-selected.

## Decision Axis 3 — Scope of gallery removal

- Delete the route directory, the nav item, and the home link only.
- The `@/design-system` components the gallery demonstrated are **left
  exported**. A few may now have fewer consumers (e.g. `Sheet`), but most are
  still used by the Studio and other routes (`ProgressRing` by `RunPanel` /
  `ActionWorkspace`, `NavRail` by `PrimaryNav`, `Card`/`PillButton`/`Surface`
  widely). Pruning the design system is explicitly out of scope ("no
  design-system overhaul"), and unused barrel exports do not fail `eslint`/`tsc`.
  Touching `@/design-system` at all would risk the "delete a shared component the
  Studio still uses" adversarial case, so it is left untouched.
- The compare-grid (`webui/components/studio/studio.module.css .compareGrid`,
  `grid-template-columns: 1fr 1fr`) is **left untouched** — enlarging the
  media caps does not require touching it, and leaving it is the safest way to
  keep it "intact".

## Validated Design (owner-approved)

1. Delete `webui/app/gallery/` (`page.tsx`, `gallery.module.css`).
2. Remove the `{ href: "/gallery", label: "Gallery" }` item from `PrimaryNav`
   → rail is `Studio / Reasoning / Action / History`.
3. Replace `webui/app/page.tsx` with a server component that
   `redirect("/studio")` (removes the dead home link in the same edit).
4. `MediaPreview.module.css` `.media { max-height: 60vh → 80vh }`;
   `(studio)/studio/page.module.css` `.studio { max-width: 60rem → 80rem }`.
   Keep `max-width: 100%` on `.media`; do not touch `.compareGrid`.

## Process Decisions

- **Commits:** per-task commits on `phase3-session-3` (prior-session pattern);
  **no push** — the owner integrates.
- **Verification:** the deterministic checks (`rg` sweep + `pnpm
  build/lint/typecheck/test`) are the blocking gate. A Playwright DOM /
  computed-style check is captured as **non-blocking supporting evidence** for
  `EV-UX-GALLERY-GONE` / `EV-UX-MEDIA-ENLARGED` (mirrors UX-S2).
