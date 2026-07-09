// @vitest-environment node
import { describe, expect, it, vi } from "vitest";

import { backoffDelay, createEventStream } from "@/lib/sse/createEventStream";

const enc = new TextEncoder();

/**
 * A pull-based ReadableStream that emits one item per read, erroring (or closing)
 * only after earlier chunks have been delivered. (A synchronous enqueue-then-error
 * in start() would reset the queue and drop the buffered chunk — unlike a real drop.)
 */
function streamOf(...items: (string | Error)[]): ReadableStream<Uint8Array> {
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i >= items.length) {
        controller.close();
        return;
      }
      const item = items[i++];
      if (item instanceof Error) {
        controller.error(item);
        return;
      }
      controller.enqueue(enc.encode(item));
    },
  });
}

const okRes = (body: ReadableStream<Uint8Array>) =>
  ({ ok: true, status: 200, body }) as unknown as Response;

describe("backoffDelay", () => {
  it("grows exponentially but is capped", () => {
    expect(backoffDelay(1, 500, 10_000)).toBe(1000);
    expect(backoffDelay(2, 500, 10_000)).toBe(2000);
    expect(backoffDelay(10, 500, 10_000)).toBe(10_000);
  });
});

describe("createEventStream", () => {
  it("reconnects with Last-Event-ID after a mid-stream drop", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(okRes(streamOf("id: 7\ndata: a\n\n", new Error("drop"))))
      .mockResolvedValueOnce(okRes(streamOf("data: b\n\n")));
    const events: string[] = [];

    await createEventStream({
      url: "/api/v1/jobs/x/events",
      onEvent: (e) => events.push(e.data),
      fetchImpl: fetchImpl as unknown as typeof fetch,
      sleep: () => Promise.resolve(),
      maxRetries: 3,
    });

    expect(fetchImpl).toHaveBeenCalledTimes(2);
    const secondInit = fetchImpl.mock.calls[1][1] as RequestInit;
    expect((secondInit.headers as Record<string, string>)["Last-Event-ID"]).toBe("7");
    expect(events).toEqual(["a", "b"]);
  });

  it("falls back to polling after exhausting retries", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("down"));
    const pollFallback = vi.fn();

    await createEventStream({
      url: "/x",
      onEvent: () => {},
      fetchImpl: fetchImpl as unknown as typeof fetch,
      sleep: () => Promise.resolve(),
      maxRetries: 2,
      pollFallback,
    });

    expect(fetchImpl).toHaveBeenCalledTimes(3); // initial + 2 retries
    expect(pollFallback).toHaveBeenCalledTimes(1);
  });

  it("reconnects when no traffic arrives within the heartbeat window", async () => {
    const hanging = new ReadableStream<Uint8Array>({ start() {} }); // never emits
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(okRes(hanging))
      .mockResolvedValueOnce(okRes(streamOf("data: ok\n\n")));
    const events: string[] = [];
    let firstTimer = true;

    await createEventStream({
      url: "/x",
      onEvent: (e) => events.push(e.data),
      fetchImpl: fetchImpl as unknown as typeof fetch,
      sleep: () => Promise.resolve(),
      maxRetries: 2,
      heartbeatTimeoutMs: 30_000,
      // Fire the liveness timeout only on the first (hanging) connection.
      setTimer: (cb) => {
        if (firstTimer) {
          firstTimer = false;
          cb();
        }
        return 0;
      },
      clearTimer: () => {},
    });

    expect(fetchImpl).toHaveBeenCalledTimes(2);
    expect(events).toEqual(["ok"]);
  });
});
