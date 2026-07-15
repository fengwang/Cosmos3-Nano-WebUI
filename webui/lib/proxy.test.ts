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
  it("strips hop-by-hop + host and injects no api key (UX-S1: auth removed)", () => {
    const incoming = new Headers({
      host: "webui:3000",
      connection: "keep-alive",
      "content-length": "42",
      "content-type": "application/json",
      "x-request-id": "abc",
    });
    const out = filterForwardHeaders(incoming);
    expect(out.get("host")).toBeNull();
    expect(out.get("connection")).toBeNull();
    expect(out.get("content-length")).toBeNull();
    expect(out.get("content-type")).toBe("application/json");
    expect(out.get("x-request-id")).toBe("abc");
    expect(out.get("x-api-key")).toBeNull(); // the proxy injects nothing
    expect(out.get("authorization")).toBeNull();
  });

  it("forwards a client-supplied x-api-key untouched (inert; the API ignores it)", () => {
    // Decision 2A / INV-3: auth is gone, so a leftover header passes through like any other
    // non-hop-by-hop header — the proxy adds no special stripping.
    const out = filterForwardHeaders(new Headers({ "x-api-key": "whatever" }));
    expect(out.get("x-api-key")).toBe("whatever");
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
