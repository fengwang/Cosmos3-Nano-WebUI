import { describe, expect, it } from "vitest";

import { feedSse, initialSseState } from "@/lib/sse/parseSse";
import type { SseEvent } from "@/lib/sse/parseSse";

function collect(chunks: string[]) {
  let state = initialSseState();
  const events: SseEvent[] = [];
  let heartbeats = 0;
  for (const chunk of chunks) {
    const result = feedSse(state, chunk);
    state = result.state;
    events.push(...result.events);
    heartbeats += result.heartbeats;
  }
  return { events, heartbeats, state };
}

describe("feedSse", () => {
  it("parses a single data event (default type 'message')", () => {
    const { events } = collect(["data: hello\n\n"]);
    expect(events).toHaveLength(1);
    expect(events[0]).toMatchObject({ event: "message", data: "hello" });
  });

  it("joins multi-line data with newlines", () => {
    const { events } = collect(["data: a\ndata: b\n\n"]);
    expect(events[0].data).toBe("a\nb");
  });

  it("captures the event type and id (for resumption)", () => {
    const { events } = collect(["id: 42\nevent: token\ndata: x\n\n"]);
    expect(events[0]).toMatchObject({ event: "token", data: "x", id: "42" });
  });

  it("treats a comment line as a heartbeat, emitting no event", () => {
    const { events, heartbeats } = collect([": keep-alive\n"]);
    expect(events).toHaveLength(0);
    expect(heartbeats).toBe(1);
  });

  it("reassembles a line split across chunks", () => {
    const { events } = collect(["data: hel", "lo\n\n"]);
    expect(events).toHaveLength(1);
    expect(events[0].data).toBe("hello");
  });

  it("handles CRLF line endings", () => {
    const { events } = collect(["event: ping\r\ndata: 1\r\n\r\n"]);
    expect(events[0]).toMatchObject({ event: "ping", data: "1" });
  });
});
