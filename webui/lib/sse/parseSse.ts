// Pure incremental SSE parser (ACD: Calculation). `feedSse(state, chunk)` returns the
// next state + any complete events + heartbeat (comment) count. The caller threads the
// state across chunks; no I/O, no timers — fully deterministic and unit-testable.

export interface SseEvent {
  event: string;
  data: string;
  id?: string;
}

export interface SseState {
  /** Bytes after the last newline — an incomplete line carried to the next chunk. */
  partial: string;
  data: string[];
  event?: string;
  id?: string;
}

export interface SseFeed {
  state: SseState;
  events: SseEvent[];
  heartbeats: number;
}

export const initialSseState = (): SseState => ({ partial: "", data: [] });

export function feedSse(prev: SseState, chunk: string): SseFeed {
  const text = (prev.partial + chunk).replace(/\r\n?/g, "\n");
  const lines = text.split("\n");
  const partial = lines.pop() ?? ""; // trailing fragment (no terminating newline yet)

  let data = [...prev.data];
  let event = prev.event;
  let id = prev.id; // last-event-id persists across events (SSE spec)
  const events: SseEvent[] = [];
  let heartbeats = 0;

  for (const line of lines) {
    if (line === "") {
      if (data.length > 0 || event !== undefined) {
        events.push({ event: event ?? "message", data: data.join("\n"), id });
      }
      data = [];
      event = undefined;
      continue;
    }
    if (line.startsWith(":")) {
      heartbeats++;
      continue;
    }
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    switch (field) {
      case "data":
        data.push(value);
        break;
      case "event":
        event = value;
        break;
      case "id":
        id = value;
        break;
      default:
        break; // retry/unknown fields ignored
    }
  }

  return { state: { partial, data, event, id }, events, heartbeats };
}
