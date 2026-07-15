import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

// CSS-module values are not observable in jsdom (css:false), so assert the source
// of truth directly. Paths are relative to the vitest root (webui/).
const read = (p: string) => readFileSync(resolve(process.cwd(), p), "utf8");
const media = read("components/MediaPreview.module.css");
const studioPage = read("app/(studio)/studio/page.module.css");

describe("enlarged media viewport", () => {
  it("raises the media max-height from 60vh to 80vh", () => {
    expect(media).toMatch(/max-height:\s*80vh/);
    expect(media).not.toMatch(/max-height:\s*60vh/);
  });

  it("raises the studio container max-width from 60rem to 80rem", () => {
    expect(studioPage).toMatch(/max-width:\s*80rem/);
    expect(studioPage).not.toMatch(/max-width:\s*60rem/);
  });

  it("stays responsive: media keeps max-width:100% and no fixed px size", () => {
    expect(media).toMatch(/max-width:\s*100%/);
    // Reject a fixed px height/width on .media (a standalone property at any
    // position) while ignoring max-height / line-height / max-width.
    expect(media).not.toMatch(/(?<![-\w])height:\s*\d+px/);
    expect(media).not.toMatch(/(?<![-\w])width:\s*\d+px/);
  });
});
