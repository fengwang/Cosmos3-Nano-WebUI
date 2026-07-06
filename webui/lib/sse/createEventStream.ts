// SSE client Action (impure shell): connects via fetch, parses with the pure feedSse,
// reconnects with Last-Event-ID + capped backoff, detects heartbeat stalls, and falls
// back to polling when retries are exhausted (RK-09). All side-effecting dependencies
// (fetch, sleep, timers) are injectable so the reconnect/fallback logic is unit-testable.
import { feedSse, initialSseState } from "@/lib/sse/parseSse";
import type { SseEvent } from "@/lib/sse/parseSse";

export interface EventStreamOptions {
  url: string;
  method?: string;
  body?: BodyInit | null;
  headers?: Record<string, string>;
  onEvent: (event: SseEvent) => void;
  onError?: (error: unknown) => void;
  signal?: AbortSignal;
  maxRetries?: number;
  baseDelayMs?: number;
  capDelayMs?: number;
  /** If set, a connection with no traffic within this window is treated as stalled. */
  heartbeatTimeoutMs?: number;
  /**
   * Invoked once when reconnect attempts are exhausted (e.g. start polling the job).
   * Receives the last seen event id so the caller can resume from the right cursor.
   */
  pollFallback?: (lastId?: string) => void | Promise<void>;
  // Injectable side effects (default to the platform implementations).
  fetchImpl?: typeof fetch;
  sleep?: (ms: number) => Promise<void>;
  setTimer?: (cb: () => void, ms: number) => unknown;
  clearTimer?: (handle: unknown) => void;
}

/** Exponential backoff capped at `capMs` (pure). */
export function backoffDelay(attempt: number, baseMs: number, capMs: number): number {
  return Math.min(capMs, baseMs * 2 ** attempt);
}

const defaultSleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

function readWithLiveness(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  timeoutMs: number | undefined,
  setTimer: (cb: () => void, ms: number) => unknown,
  clearTimer: (handle: unknown) => void,
): Promise<ReadableStreamReadResult<Uint8Array>> {
  if (!timeoutMs) return reader.read();
  return new Promise((resolve, reject) => {
    const handle = setTimer(() => reject(new Error("sse stall: no traffic within window")), timeoutMs);
    reader.read().then(
      (result) => {
        clearTimer(handle);
        resolve(result);
      },
      (error) => {
        clearTimer(handle);
        reject(error);
      },
    );
  });
}

/**
 * Consume an SSE endpoint until it ends, the signal aborts, or retries are exhausted.
 * Resolves when the stream completes normally, on abort, or after pollFallback runs.
 */
export async function createEventStream(opts: EventStreamOptions): Promise<void> {
  const {
    url,
    method = "GET",
    body,
    headers = {},
    onEvent,
    onError,
    signal,
    maxRetries = 5,
    baseDelayMs = 500,
    capDelayMs = 10_000,
    heartbeatTimeoutMs,
    pollFallback,
    fetchImpl = fetch,
    sleep = defaultSleep,
    setTimer = (cb, ms) => setTimeout(cb, ms),
    clearTimer = (handle) => clearTimeout(handle as ReturnType<typeof setTimeout>),
  } = opts;

  let lastId: string | undefined;
  let attempt = 0;
  const decoder = new TextDecoder();

  while (true) {
    if (signal?.aborted) return;
    let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
    let state = initialSseState();
    try {
      const requestHeaders: Record<string, string> = { ...headers };
      if (lastId !== undefined) requestHeaders["Last-Event-ID"] = lastId;

      const init: RequestInit & { duplex?: "half" } = {
        method,
        headers: requestHeaders,
        signal,
        cache: "no-store",
      };
      if (body != null && method.toUpperCase() !== "GET") {
        init.body = body;
        init.duplex = "half";
      }

      const res = await fetchImpl(url, init);
      if (!res.ok || !res.body) throw new Error(`sse connect failed: ${res.status}`);
      attempt = 0; // a successful connection resets backoff
      reader = res.body.getReader();

      while (true) {
        const result = await readWithLiveness(reader, heartbeatTimeoutMs, setTimer, clearTimer);
        if (result.done) return; // stream ended normally
        const fed = feedSse(state, decoder.decode(result.value, { stream: true }));
        state = fed.state;
        for (const event of fed.events) {
          if (event.id !== undefined) lastId = event.id;
          onEvent(event);
        }
      }
    } catch (error) {
      await reader?.cancel().catch(() => {});
      if (signal?.aborted) return;
      onError?.(error);
      attempt++;
      if (attempt > maxRetries) {
        if (pollFallback) await pollFallback(lastId);
        return;
      }
      await sleep(backoffDelay(attempt, baseDelayMs, capDelayMs));
    }
  }
}
