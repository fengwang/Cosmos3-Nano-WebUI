import { afterEach, describe, expect, it, vi } from "vitest";

import { API_PREFIX, apiFetch, apiUrl } from "@/lib/api/client";

describe("apiUrl", () => {
  it("prefixes a known api path with the same-origin BFF base", () => {
    expect(API_PREFIX).toBe("/api");
    // The path argument is type-checked against the generated OpenAPI schema:
    // a typo here would fail `pnpm typecheck`.
    expect(apiUrl("/v1/reason")).toBe("/api/v1/reason");
    expect(apiUrl("/v1/health/ready")).toBe("/api/v1/health/ready");
  });

  it("appends a query string when given", () => {
    expect(apiUrl("/v1/jobs", "?limit=10")).toBe("/api/v1/jobs?limit=10");
  });
});

describe("apiFetch", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("fetches the same-origin proxy URL, forwarding the search string", async () => {
    const calls: string[] = [];
    vi.stubGlobal("fetch", (url: string) => {
      calls.push(url);
      return Promise.resolve(new Response("{}"));
    });
    await apiFetch("/v1/jobs", undefined, "?limit=5");
    expect(calls[0]).toBe("/api/v1/jobs?limit=5");
  });
});
