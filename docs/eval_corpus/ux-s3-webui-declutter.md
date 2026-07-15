# Eval Harvest — UX-S3 (WebUI Declutter: Remove Gallery, Land on Studio, Enlarge Media)

Date: 2026-07-15
Session outcome: GATE-UX-S3-WEBUI **PASS**. Deterministic gate green (build/lint/
typecheck + 42 files / 214 tests); `rg` sweep clean; runtime redirect + Playwright
layout evidence recorded; 6-axis sharded review (no High/Critical); adversarial
verifier PASS. Presentation-only; no code fix resulted from review or verification
(three minor test/doc improvements only).

Reusable workflow lessons, each with a proposed promotion target.

## 1. A test-runner allowlist can silently skip a session's own tests (false green)
- **What (SPEC_GAP / near-miss, caught in planning):** `webui/vitest.config.ts`
  `include` is an explicit allowlist (`design-system/**`, `lib/**`,
  `components/action-viewer/**`). The files UX-S3 edits live in `app/**` and
  `components/**` (non-action-viewer), so a co-located `PrimaryNav.test.tsx` /
  `page.test.tsx` / dimensions test would be collected by nobody and pass with
  **zero assertions run** — the same "fails silently" class as the 4-hashtag spec
  scenario trap. The tight blast radius listed only the 6 source files, so making
  the tests run required editing `vitest.config.ts` (out of the listed radius).
- **How caught:** reading the vitest config before writing the first test; confirmed
  by watching the RED test actually get collected only after broadening `include`.
- **Promotion target — update project-contract template / AGENTS.md:** when a
  session's `routing` requires spec-derived tests, its `blast_radius` MUST include a
  test location that the test runner's `include`/discovery actually covers (or the
  runner config, as an explicit allowed edit). "Wrote a test" ≠ "the test runs" —
  verify the collected-file count changes.

## 2. Deleting an App-Router route breaks `tsc` until rebuild (ENVIRONMENT, not a bug)
- **What:** immediately after `git rm webui/app/gallery/`, `pnpm typecheck` failed
  with `TS2307: Cannot find module '.next/types/app/gallery/page.js'`. `tsconfig`
  includes `.next/types/**`, which are **generated** by the previous `pnpm build`
  and still referenced the deleted route.
- **How caught:** the per-task `pnpm typecheck` check; classified ENVIRONMENT via the
  Failure Arbiter (stale generated artifact), fixed by `pnpm build` regenerating
  `.next/types` — no product code touched.
- **Promotion target — add eval seed / update AGENTS.md:** after adding/removing a
  Next.js route, a `tsc` error under `.next/types/**` is expected-until-rebuild;
  re-run `pnpm build` before treating it as a defect. Don't "fix" generated types.

## 3. Keep the deterministic sweep literally clean — even in test code and comments
- **What:** the contract's acceptance criterion is `rg -i gallery … clean apart from
  the HistoryList comment`. A first draft of `PrimaryNav.test.tsx` asserted the
  Gallery item's absence by literally querying `a[href="/gallery"]` and had a comment
  mentioning "gallery" — both would have added matches to the sweep.
- **How caught:** running the sweep after the RED→GREEN loop.
- **Promotion target — update REVIEW.md / test guidance:** to guard the *absence* of
  a removed token without re-tripping a repo-wide token sweep, assert the *positive*
  contract (e.g. the exact ordered nav set) rather than naming the removed token;
  keep the removed token out of test code and comments too.

## 4. Prefer a redirect over rendering, to sidestep framework layout/provider coupling
- **What (design signal that worked):** landing `/` on the Studio via
  `redirect("/studio")` in a root server component means `/` renders no Studio content
  and never needs the `(studio)` route-group `StudioProvider` — structurally avoiding
  the "route-group interaction" the contract flagged as a failure mode. Rendering the
  Studio at `/` would have forced hoisting/duplicating the provider (scope creep).
- **Promotion target — keep (design note):** when a "land on X" requirement meets a
  framework where X depends on a scoped layout/provider, a redirect is usually lower
  blast radius and lower risk than relocating X or hoisting its provider.

## 5. CSS-module values aren't observable in jsdom — assert the source + confirm in a real browser
- **What:** `vitest` runs with `css:false`, so a rendered `.media` has no computed
  `max-height` in jsdom. The regression guard reads the CSS-module files from disk and
  asserts the raised bounds + `max-width:100%` + no fixed px; the *real-browser*
  computed style (`max-width`=1280px; media rule `max-height:80vh`) and the 375px
  no-overflow check came from Playwright (non-blocking).
- **Promotion target — keep (test pattern):** for CSS-only changes, a file-content
  assertion is a valid deterministic guard; pair it with a real-browser computed-style
  check for the "does it actually apply" confirmation rather than pretending jsdom
  measures layout.

## 6. Distinguish "my change broke responsiveness" from a pre-existing layout issue
- **What (adversarial case #3 handled correctly):** at 375px the document overflowed
  (scrollWidth 651px). The instinct is to blame the just-enlarged media, but the studio
  container fit (347px) and the media rule is `max-width:100%`; the overflow came from
  `header.app-header`/`main.app-main` (the app-shell). Proven pre-existing by
  `git diff --name-only 7bf5388..HEAD` excluding `globals.css`/`layout.tsx`.
- **Promotion target — update adversarial-verifier / REVIEW.md guidance:** when a smoke
  surfaces a defect near the change, attribute it with the diff before fixing —
  a symptom adjacent to your change is not proof your change caused it, and a
  pre-existing issue in out-of-radius files is not this session's to fix.

## 7. Process signals that worked (keep)
- Front-loading the two real design decisions (redirect vs render; media magnitude) into
  the interview, with a concrete restate + explicit yes, meant the refining pack and TDD
  loop had no open questions.
- Per-task RED→GREEN→commit kept each behavior change independently verified and revertible.
- Surfacing the blast-radius-vs-tests tension to the owner (rather than silently expanding
  or silently skipping) produced a clean, recorded amendment (UX-S3-A1) instead of a latent
  contract breach.
