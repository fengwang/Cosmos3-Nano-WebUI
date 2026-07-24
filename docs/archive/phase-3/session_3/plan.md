# UX-S3 Plan — WebUI Declutter (TDD micro-steps)

Date: 2026-07-15
Inputs: `tasks.md`, `design.md`, `specs/*`. All paths relative to repo root;
commands run from `webui/`. Red→green→commit per task.

## Pre-step P.0 — Enable the new test locations (blast-radius note UX-S3-A1)

`webui/vitest.config.ts` `include` only matches `design-system/**`, `lib/**`,
`components/action-viewer/**`; tests co-located with this session's files
(`app/**`, `components/**`) would be **silently skipped**. Broaden it so the new
specs actually run. Recorded as an in-session blast-radius expansion
(execution_contract.md; evidence_map row).

```ts
// webui/vitest.config.ts — include:
include: [
  "design-system/**/*.test.{ts,tsx}",
  "lib/**/*.test.{ts,tsx}",
  "app/**/*.test.{ts,tsx}",         // UX-S3: run co-located route/nav specs
  "components/**/*.test.{ts,tsx}",  // UX-S3: supersedes action-viewer-only glob
],
```

Verify no unexpected pre-existing tests get swept in: `pnpm test` count rises by
exactly the number of new files (baseline 39 files / 208 tests).

## Task 2 — Remove Gallery route + nav item

### 2.1 (RED) `webui/app/_components/PrimaryNav.test.tsx`

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ usePathname: () => "/studio" }));

import { PrimaryNav } from "./PrimaryNav";

describe("PrimaryNav", () => {
  it("lists Studio/Reasoning/Action/History and omits Gallery", () => {
    render(<PrimaryNav />);
    for (const name of ["Studio", "Reasoning", "Action", "History"]) {
      expect(screen.getByRole("link", { name })).toBeInTheDocument();
    }
    expect(screen.queryByRole("link", { name: /gallery/i })).toBeNull();
  });

  it("renders no link targeting /gallery", () => {
    const { container } = render(<PrimaryNav />);
    expect(container.querySelector('a[href="/gallery"]')).toBeNull();
  });
});
```

Run `pnpm test -- PrimaryNav` → **fails** (Gallery item still present).

### 2.2 (GREEN) Edit `webui/app/_components/PrimaryNav.tsx`

Delete the line `{ href: "/gallery", label: "Gallery" },` from `ITEMS`.
Run `pnpm test -- PrimaryNav` → green.

### 2.3 Delete the route

```bash
git rm webui/app/gallery/page.tsx webui/app/gallery/gallery.module.css
```

### 2.4 Check + commit

```bash
pnpm typecheck && pnpm lint && pnpm test
rg -i "gallery|/gallery" app components   # only HistoryList comment
```
Commit: `feat(ux-s3): remove component gallery route + nav item`.

## Task 3 — Land / on the Studio

### 3.1 (RED) `webui/app/page.test.tsx`

```tsx
import { describe, expect, it, vi } from "vitest";
import { redirect } from "next/navigation";

vi.mock("next/navigation", () => ({ redirect: vi.fn() }));

import Home from "./page";

describe("Home", () => {
  it("redirects to /studio", () => {
    Home();
    expect(redirect).toHaveBeenCalledWith("/studio");
  });
});
```

Run `pnpm test -- page` → **fails** (Home renders a Card, never calls redirect).

### 3.2 (GREEN) Replace `webui/app/page.tsx`

```tsx
import { redirect } from "next/navigation";

// The home route lands users on the Generation Studio (UX-S3). The Studio owns
// its own (studio) route-group provider, so `/` only redirects — it renders no
// Studio content and needs no provider.
export default function Home() {
  redirect("/studio");
}
```

Run `pnpm test -- page` → green.

### 3.3 Check + commit

```bash
pnpm typecheck && pnpm lint && pnpm test
```
Commit: `feat(ux-s3): redirect / to the studio (drop stale home stub)`.

## Task 4 — Enlarge media viewport

### 4.1 (RED) `webui/components/MediaPreview.dimensions.test.ts`

```ts
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const read = (p: string) => readFileSync(resolve(process.cwd(), p), "utf8");
const media = read("components/MediaPreview.module.css");
const studioPage = read("app/(studio)/studio/page.module.css");

describe("enlarged media viewport", () => {
  it("media max-height raised 60vh → 80vh", () => {
    expect(media).toMatch(/max-height:\s*80vh/);
    expect(media).not.toMatch(/max-height:\s*60vh/);
  });

  it("studio container max-width raised 60rem → 80rem", () => {
    expect(studioPage).toMatch(/max-width:\s*80rem/);
    expect(studioPage).not.toMatch(/max-width:\s*60rem/);
  });

  it("stays responsive: max-width:100%, no fixed px size", () => {
    expect(media).toMatch(/max-width:\s*100%/);
    expect(media).not.toMatch(/height:\s*\d+px/);
    expect(media).not.toMatch(/width:\s*\d+px/);
  });
});
```

Run `pnpm test -- dimensions` → **fails** (values are 60vh / 60rem).

### 4.2 (GREEN) Edit the two CSS modules

- `webui/components/MediaPreview.module.css`: `.media { max-height: 60vh; }` →
  `80vh` (keep `max-width: 100%`).
- `webui/app/(studio)/studio/page.module.css`: `.studio { max-width: 60rem; }`
  → `80rem`.
- Do **not** touch `webui/components/studio/studio.module.css` (`.compareGrid`
  stays `1fr 1fr`).

Run `pnpm test -- dimensions` → green.

### 4.3 Check + commit

```bash
pnpm typecheck && pnpm lint && pnpm test
```
Commit: `feat(ux-s3): enlarge media viewport (80rem container / 80vh media)`.

## Task 5 — Full checks + supporting evidence

```bash
rg -i "gallery|/gallery" app components          # only the HistoryList comment
pnpm build && pnpm lint && pnpm typecheck && pnpm test
```
Confirm the build route list no longer contains `/gallery` and `/` is present.
Playwright (non-blocking): `browser_navigate /` → asserts URL `/studio`; nav
snapshot has no Gallery; `getComputedStyle(.media).maxHeight` ≈ 80vh at 1440px;
`browser_resize 375` → media clientWidth ≤ viewport. Save evidence under
`docs/session_3/`.

## Tasks 6–7 — Review, adversarial verify, close

6-axis read-only review → `sharded_review.md`; fix only High/Critical; re-check.
Fresh-context adversarial verifier vs `GATE-UX-S3-WEBUI` →
`adversarial_verification.md`. Verify done; update `handoff.md`,
`evidence_map.md`, `risk_register.md`, `eval_seed_cases.md`, eval corpus. Final
commit; no push.

## Commit Points

1. gallery removed · 2. `/`→studio redirect · 3. media enlarged ·
4. checks/review/verify/docs (may be split: a `test+config` commit for P.0 can
ride with Task 2, and a `docs(ux-s3)` commit closes the session).
