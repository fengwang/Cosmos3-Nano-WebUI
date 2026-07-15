# UX-S3 WebUI Smoke + Deterministic Gate Evidence

Date: 2026-07-15
Scope: `GATE-UX-S3-WEBUI`. Deterministic checks are the **blocking** gate; the
browser smoke is **non-blocking** supporting evidence (owner-confirmed).

## Deterministic gate (blocking) — GREEN

From `webui/`:

| Check | Result |
|---|---|
| `rg -i "gallery\|/gallery" webui/app webui/components` | only `components/history/HistoryList.tsx` "History/gallery" comment |
| `pnpm build` | OK — route list drops `/gallery`; `/` is a 128 B redirect route; `/studio` present |
| `pnpm lint` | OK (exit 0) |
| `pnpm typecheck` | OK (`tsc --noEmit` clean) |
| `pnpm test` | **42 files / 214 passed** (baseline 39/208 + 3 new UX-S3 specs) |

New specs added (run via the broadened vitest `include`, UX-S3-A1):
`app/_components/PrimaryNav.test.tsx`, `app/page.test.tsx`,
`components/MediaPreview.dimensions.test.ts`.

Note: a stale `.next/types/app/gallery/page.ts` made `tsc` fail immediately
after the route deletion — classified **ENVIRONMENT** (stale generated types),
resolved by `pnpm build` regenerating `.next/types`; no product code changed.

## Browser smoke (non-blocking) — Next dev server, port 3111

### Redirect (curl, real HTTP)
- `GET /` → **HTTP 307**, `location: http://localhost:3111/studio`
- `GET /studio` → **HTTP 200**

### DOM / computed style (Playwright, viewport 1440×900)
```
landedPath:            "/studio"          (navigating to / lands on the Studio)
hasGalleryLink:        false
navLinks:              [Studio→/studio, Reasoning→/chat, Action→/action, History→/history]
studioMaxWidth:        1280px             (= 80rem; was 60rem/960px)
enlargedMediaRule:     .MediaPreview_media__… { max-width: 100%; max-height: 80vh; … }
```
Screenshot (not committed; `.playwright-mcp/` is gitignored) showed the Studio
landing with the four-item rail (Studio highlighted, no Gallery) and the UX-S2
"Using recommended default" negative-prompt placeholder intact.

Console: one benign `favicon.ico` 404 in dev; no application error (the Studio
rendered without a backend API).

### Responsiveness (viewport 375×800)
- `section[aria-label="Generation studio"]` clientWidth = **347px** (fits; the
  `80rem` cap does not force width) and the media rule is `max-width: 100%` →
  the UX-S3 enlargement does **not** overflow narrow viewports. Adversarial
  case #3 (fixed-px overflow) refuted; the responsiveness invariant holds.
- Observed (pre-existing, out of scope): the document scrollWidth is 651px at
  375px — a horizontal overflow originating from `header.app-header` /
  `main.app-main` (the app-shell in `app/globals.css` + `app/layout.tsx`).
  **This session's diff touches neither file** (`git diff --name-only
  7bf5388..HEAD` excludes `globals.css`/`layout.tsx`), so the app-shell's
  narrow-viewport behavior is pre-existing and unrelated to UX-S3. Flagged as a
  future-session observation (desktop-oriented shell; nav/layout are outside the
  UX-S3 blast radius and "no structural redesign" is a non-goal).
