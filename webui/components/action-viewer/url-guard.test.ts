import { describe, expect, it } from "vitest";

import { isRemoteUrl } from "./url-guard";

describe("isRemoteUrl (INV-1 asset guard)", () => {
  it("flags remote/scheme URLs", () => {
    for (const u of ["https://evil/x.urdf", "http://x/y", "file:///etc/passwd", "ws://x", "ftp://x/y"]) {
      expect(isRemoteUrl(u), u).toBe(true);
    }
  });
  it("accepts same-origin local paths", () => {
    for (const u of ["/urdf/agibotworld.urdf", "./x.urdf", "urdf/x.urdf", "/_next/static/x.js"]) {
      expect(isRemoteUrl(u), u).toBe(false);
    }
  });
});
