// @vitest-environment node
// Node env: undici Headers does not enforce the browser "forbidden header" list,
// so we can construct + assert stripping of hop-by-hop headers (host, connection, …).
import { describe, expect, it } from "vitest";

import {
  buildUpstreamUrl,
  filterForwardHeaders,
  filterResponseHeaders,
} from "@/lib/proxy";

describe("buildUpstreamUrl", () => {
  it("joins base + segments + search, trimming a trailing slash on the base", () => {
    expect(buildUpstreamUrl("http://api:8000/", ["v1", "reason"], "?x=1")).toBe(
      "http://api:8000/v1/reason?x=1",
    );
    expect(buildUpstreamUrl("http://api:8000", ["v1", "health", "ready"], "")).toBe(
      "http://api:8000/v1/health/ready",
    );
  });
});

describe("filterForwardHeaders", () => {
  it("strips hop-by-hop + host and injects X-API-Key when a key is given", () => {
    const incoming = new Headers({
      host: "webui:3000",
      connection: "keep-alive",
      "content-length": "42",
      "content-type": "application/json",
      "x-request-id": "abc",
    });
    const out = filterForwardHeaders(incoming, "secret");
    expect(out.get("host")).toBeNull();
    expect(out.get("connection")).toBeNull();
    expect(out.get("content-length")).toBeNull();
    expect(out.get("content-type")).toBe("application/json");
    expect(out.get("x-request-id")).toBe("abc");
    // The API enforces X-API-Key (api/app/auth.py), not Authorization: Bearer (X-1).
    expect(out.get("x-api-key")).toBe("secret");
    expect(out.get("authorization")).toBeNull();
  });

  it("omits the API key header when no key is configured", () => {
    const out = filterForwardHeaders(new Headers({ "content-type": "text/plain" }));
    expect(out.get("x-api-key")).toBeNull();
    expect(out.get("content-type")).toBe("text/plain");
  });

  it("overwrites a client-supplied X-API-Key with the server key (no spoofing)", () => {
    const out = filterForwardHeaders(new Headers({ "x-api-key": "attacker" }), "server");
    expect(out.get("x-api-key")).toBe("server");
  });
});

describe("filterResponseHeaders", () => {
  it("strips hop-by-hop and forces no buffering so SSE survives", () => {
    const upstream = new Headers({
      "content-type": "text/event-stream",
      "transfer-encoding": "chunked",
      "content-length": "10",
    });
    const out = filterResponseHeaders(upstream);
    expect(out.get("content-type")).toBe("text/event-stream");
    expect(out.get("transfer-encoding")).toBeNull();
    expect(out.get("content-length")).toBeNull();
    expect(out.get("x-accel-buffering")).toBe("no");
  });

  it("strips content-encoding (the body is already decoded by the fetch client)", () => {
    // undici auto-decompresses res.body but RETAINS content-encoding; forwarding it
    // would mislabel a plaintext body and corrupt it in the browser.
    const upstream = new Headers({
      "content-type": "application/json",
      "content-encoding": "gzip",
    });
    const out = filterResponseHeaders(upstream);
    expect(out.get("content-encoding")).toBeNull();
    expect(out.get("content-type")).toBe("application/json");
  });
});
