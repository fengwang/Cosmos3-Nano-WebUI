# UX-S3 Tasks — WebUI Declutter

Derived from `specs/webui-declutter.md`, `specs/media-viewport.md`, and
`design.md`. Ordered by dependency. Each task is red→green→commit.

## 1. Refining pack

- [x] 1.1 Write brainstorming, proposal, design, specs, tasks, plan.
- [x] 1.2 Write the execution contract (`execution_contract.md`).

## 2. Remove Gallery route + nav item (FR-7, `webui-declutter`)

- [x] 2.1 Add `webui/app/_components/PrimaryNav.test.tsx` asserting the rail
      renders Studio/Reasoning/Action/History and **no** Gallery link (fails
      now — the item is present).
- [x] 2.2 Remove the `{ href: "/gallery", label: "Gallery" }` entry from
      `PrimaryNav.ITEMS`; test green.
- [x] 2.3 Delete `webui/app/gallery/` (`page.tsx`, `gallery.module.css`).
- [x] 2.4 `pnpm typecheck && pnpm lint && pnpm test`; `rg -i gallery` clean bar
      the HistoryList comment; commit.

## 3. Land / on the Studio (FR-7, `webui-declutter`)

- [x] 3.1 Add `webui/app/page.test.tsx` mocking `next/navigation` and asserting
      `Home()` calls `redirect("/studio")` and renders no `/gallery` link
      (fails now — Home renders a Card with the gallery link).
- [x] 3.2 Replace `webui/app/page.tsx` with a server component that
      `redirect("/studio")`; test green.
- [x] 3.3 `pnpm typecheck && pnpm lint && pnpm test`; commit.

## 4. Enlarge media viewport (FR-8, `media-viewport`)

- [x] 4.1 Add `webui/components/MediaPreview.dimensions.test.ts` asserting
      `.media max-height: 80vh` (not `60vh`), `.studio max-width: 80rem` (not
      `60rem`), `.media` retains `max-width: 100%`, and no fixed px height/width
      on `.media` (fails now — values are `60vh`/`60rem`).
- [x] 4.2 Edit `MediaPreview.module.css` (`60vh → 80vh`) and
      `(studio)/studio/page.module.css` (`60rem → 80rem`); test green.
- [x] 4.3 `pnpm typecheck && pnpm lint && pnpm test`; commit.

## 5. Full deterministic checks + supporting evidence

- [x] 5.1 `rg -i "gallery|/gallery" webui/app webui/components` → only the
      HistoryList comment.
- [x] 5.2 From `webui/`: `pnpm build && pnpm lint && pnpm typecheck && pnpm test`
      all green; confirm `/gallery` is gone from the build route list and `/`
      is a redirect.
- [x] 5.3 Playwright DOM / computed-style check (non-blocking): `/` → `/studio`,
      nav has no Gallery, `.media` computed `max-height` = 80vh at desktop and
      no horizontal overflow at 375px. Save evidence.

## 6. Review + fixes

- [x] 6.1 Run the 6-axis read-only review (correctness, security, tests,
      architecture, performance, readability); dedupe; save
      `sharded_review.md`.
- [x] 6.2 Fix only High/Critical findings; re-run targeted checks.

## 7. Adversarial verify + close

- [x] 7.1 Fresh-context adversarial verifier vs `GATE-UX-S3-WEBUI` (contract +
      diff + evidence only); save `adversarial_verification.md`.
- [x] 7.2 Verify done condition; update `docs/handoff.md`, `evidence_map.md`,
      `risk_register.md`, `eval_seed_cases.md`, eval corpus.
- [x] 7.3 Final commit; state remaining risks + next-session warnings.
