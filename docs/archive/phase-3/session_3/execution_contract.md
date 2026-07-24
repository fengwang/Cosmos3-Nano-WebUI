# UX-S3 Execution Contract

Date: 2026-07-15
Authority: `docs/session_3_contract.yaml` (UX-S3), `docs/project_contract.md`.
Design: `docs/session_3/design.md` (owner-approved: redirect `/`→`/studio`;
moderate media enlargement 80rem / 80vh; add regression tests + widen vitest
include).

## Planned File Changes

| File | Change |
|---|---|
| `webui/app/gallery/page.tsx` | **delete** |
| `webui/app/gallery/gallery.module.css` | **delete** |
| `webui/app/_components/PrimaryNav.tsx` | remove the `{ href:"/gallery", label:"Gallery" }` item |
| `webui/app/page.tsx` | replace stale stub with `redirect("/studio")` server component |
| `webui/components/MediaPreview.module.css` | `.media max-height 60vh → 80vh` (keep `max-width:100%`) |
| `webui/app/(studio)/studio/page.module.css` | `.studio max-width 60rem → 80rem` |
| `webui/components/studio/studio.module.css` | **no change expected** (compare-grid left intact; in radius as a safety allowance) |
| `webui/vitest.config.ts` | **(UX-S3-A1)** broaden `include` to `app/**` + `components/**` so co-located specs run |
| `webui/app/_components/PrimaryNav.test.tsx` | **new** — nav omits Gallery |
| `webui/app/page.test.tsx` | **new** — `/` redirects to `/studio` |
| `webui/components/MediaPreview.dimensions.test.ts` | **new** — enlarged bounds + responsiveness |
| `docs/session_3/**`, `docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`, `docs/eval_corpus/`, `docs/handoff.md` | updated |

## Allowed Blast Radius

From `session_3_contract.yaml.blast_radius.allowed_files`: `webui/app/gallery/**`,
`webui/app/page.tsx`, `webui/app/_components/PrimaryNav.tsx`,
`webui/components/MediaPreview.module.css`,
`webui/app/(studio)/studio/page.module.css`,
`webui/components/studio/studio.module.css`, `docs/session_3/**`,
`docs/evidence_map.md`, `docs/risk_register.md`, `docs/eval_seed_cases.md`,
`docs/handoff.md`.

**Recorded expansion — UX-S3-A1 (owner-approved 2026-07-15):** the contract's
`routing` requires spec-derived verification but its `deterministic_checks`
run `pnpm test`, whose `include` globs do not cover the natural co-location for
this session's files. To make spec-derived tests actually run (avoiding the
"silent-skip" failure mode), the blast radius is expanded by three new test
files (`app/_components/PrimaryNav.test.tsx`, `app/page.test.tsx`,
`components/MediaPreview.dimensions.test.ts`) and one config edit
(`webui/vitest.config.ts` `include`). This adds tests + test-runner config only;
no product behavior beyond the four planned source edits. The session contract
YAML itself is out of this session's write-radius, so the amendment is recorded
here and in `docs/evidence_map.md` (mirroring the UX-S1-A1 precedent).

Forbidden (stop if hit): `api/**`; any auth (UX-S1) / generation-default (UX-S2)
code; `README.md`, `CONTRIBUTING.md`, `SECURITY.md` (UX-S4); the
Reasoning/Action/History route or component files; `docs/archive/**`; model
weights / generated media.

## First Test To Write

`webui/app/_components/PrimaryNav.test.tsx` — render `PrimaryNav` and assert it
renders Studio/Reasoning/Action/History links and **no** link with name
`/gallery/i` or `href="/gallery"`. Fails against the current nav (Gallery item
present); passes after the item is removed (`EV-UX-GALLERY-GONE`).

## Checks After Each Task

- After each webui task: from `webui/`, `pnpm typecheck && pnpm lint && pnpm test`
  (targeted `pnpm test -- <name>` during the red/green loop).
- After the gallery deletion: `rg -i "gallery|/gallery" webui/app webui/components`
  → only the `HistoryList` "History/gallery" comment.
- Before the session's final commit: full `pnpm build && pnpm lint && pnpm
  typecheck && pnpm test` from `webui/`, and confirm the build route list drops
  `/gallery`.
- Classify any failure (BUG / SPEC_GAP / AMBIGUITY / ENVIRONMENT / TEST_BUG)
  before fixing (`failure_arbiter.md`).

## Review Axes (end of session)

correctness · security · tests · architecture · performance · readability
(read-only, deduplicated; per the contract's `review_axes` and the 6-axis
sharded-review prompt).

## Adversarial Verifier Brief

Fresh context; sees only `docs/session_3_contract.yaml`, the diff, and recorded
evidence. Try to falsify that `GATE-UX-S3-WEBUI` is satisfied. Attack:
1. the `/gallery` route still resolves by URL (or a nav item/link dangles) —
   half-removed feature;
2. `/` still renders the old stub / a dead link, or the redirect breaks under
   the `(studio)` route group;
3. media enlarged with a fixed pixel value that overflows a narrow viewport or
   breaks the compare-grid;
4. a design-system component the gallery imported was deleted, breaking the
   Studio;
5. the new tests don't actually run (include-glob silent skip) or assert
   implementation trivia rather than the spec;
6. a public API interaction / BFF posture changed (INV-7) — should be untouched;
7. build/lint/typecheck/test not actually green, or `rg` sweep not clean.

## Concrete Done Condition

`GATE-UX-S3-WEBUI` passes:
- no `/gallery` route, nav item, or home link; `rg -i gallery` over
  `webui/app`+`webui/components` clean bar the HistoryList comment
  (`EV-UX-GALLERY-GONE`);
- `/` redirects to `/studio` (307), verified by a unit test + Playwright;
- `MediaPreview` `max-height` = 80vh and studio container `max-width` = 80rem
  (both raised vs baseline), responsive (`max-width:100%`, no fixed px), the
  compare-grid still 2-up (`EV-UX-MEDIA-ENLARGED`);
- `pnpm build && pnpm lint && pnpm typecheck && pnpm test` green, including the
  three new specs (`EV-UX-CPU-SUITE-GREEN`).

Invariants held: INV-7 (same-origin BFF unchanged; no direct API calls); no
public API interaction change; enlargement responsive on small screens.
