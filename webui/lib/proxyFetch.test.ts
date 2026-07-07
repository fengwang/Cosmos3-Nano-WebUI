// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { forward } from "@/lib/proxyFetch";

const ORIG = process.env.COSMOS3_API_KEY;
const ORIG_BASE = process.env.API_INTERNAL_URL;

beforeEach(() => {
  process.env.API_INTERNAL_URL = "http://api:8000";
  delete process.env.COSMOS3_API_KEY;
});
afterEach(() => {
  if (ORIG === undefined) delete process.env.COSMOS3_API_KEY;
  else process.env.COSMOS3_API_KEY = ORIG;
  if (ORIG_BASE === undefined) delete process.env.API_INTERNAL_URL;
  else process.env.API_INTERNAL_URL = ORIG_BASE;
});

describe("forward (BFF proxy Action)", () => {
  it("masks an unreachable upstream as 502 without leaking the internal address", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("ECONNREFUSED http://api:8000"));
    const res = await forward(
      new Request("http://webui/api/v1/health/ready"),
      ["v1", "health", "ready"],
      fetchImpl as unknown as typeof fetch,
    );
    expect(res.status).toBe(502);
    const body = await res.text();
    expect(body).toBe(JSON.stringify({ error: "api_unreachable" }));
    expect(body).not.toContain("api:8000"); // no internal address leak
  });

  it("injects COSMOS3_API_KEY server-side and never returns it to the caller", async () => {
    process.env.COSMOS3_API_KEY = "s3cret";
    let captured: RequestInit | undefined;
    const fetchImpl = vi.fn((_url: string, init?: RequestInit) => {
      captured = init;
      return Promise.resolve(new Response("{}", { status: 200 }));
    });
    const res = await forward(
      new Request("http://webui/api/v1/jobs"),
      ["v1", "jobs"],
      fetchImpl as unknown as typeof fetch,
    );
    const sent = new Headers(captured?.headers);
    expect(sent.get("x-api-key")).toBe("s3cret");
    expect(JSON.stringify([...res.headers])).not.toContain("s3cret");
    expect(await res.text()).not.toContain("s3cret");
  });

  it("sends no body or duplex on GET", async () => {
    let captured: (RequestInit & { duplex?: string }) | undefined;
    const fetchImpl = vi.fn((_url: string, init?: RequestInit) => {
      captured = init;
      return Promise.resolve(new Response("ok", { status: 200 }));
    });
    await forward(
      new Request("http://webui/api/v1/jobs"),
      ["v1", "jobs"],
      fetchImpl as unknown as typeof fetch,
    );
    expect(captured?.body).toBeUndefined();
    expect(captured?.duplex).toBeUndefined();
  });

  it("strips content-encoding from a forwarded response", async () => {
    const fetchImpl = vi.fn(() =>
      Promise.resolve(
        new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "content-type": "application/json", "content-encoding": "gzip" },
        }),
      ),
    );
    const res = await forward(
      new Request("http://webui/api/v1/jobs"),
      ["v1", "jobs"],
      fetchImpl as unknown as typeof fetch,
    );
    expect(res.headers.get("content-encoding")).toBeNull();
    expect(res.headers.get("x-accel-buffering")).toBe("no");
  });
});
