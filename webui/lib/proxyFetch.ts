// BFF proxy Action (impure shell): reads server env, fetches the internal api, and
// streams the response straight through. Composes the pure Calculations in lib/proxy.ts.
// Server-only — invoked from route handlers, never shipped to the browser.
import {
  DEFAULT_API_BASE,
  buildUpstreamUrl,
  filterForwardHeaders,
  filterResponseHeaders,
} from "@/lib/proxy";

/** Mask an unreachable upstream — never leak the internal address or a stack trace. */
function maskedGatewayError(): Response {
  return new Response(JSON.stringify({ error: "api_unreachable" }), {
    status: 502,
    headers: { "content-type": "application/json" },
  });
}

/**
 * Forward an incoming browser request to the internal api as `<base>/<segments>`.
 * `fetchImpl` is injectable for tests; production passes the platform fetch.
 */
export async function forward(
  req: Request,
  segments: string[],
  fetchImpl: typeof fetch = fetch,
): Promise<Response> {
  const base = process.env.API_INTERNAL_URL ?? DEFAULT_API_BASE;
  const url = buildUpstreamUrl(base, segments, new URL(req.url).search);
  const headers = filterForwardHeaders(req.headers);
  const method = req.method.toUpperCase();
  const hasBody = method !== "GET" && method !== "HEAD";

  const init: RequestInit & { duplex?: "half" } = {
    method,
    headers,
    redirect: "manual",
    cache: "no-store",
  };
  if (hasBody) {
    init.body = req.body;
    init.duplex = "half"; // required by Node fetch when streaming a request body
  }

  let upstream: Response;
  try {
    upstream = await fetchImpl(url, init);
  } catch {
    return maskedGatewayError();
  }

  const responseHeaders = filterResponseHeaders(upstream.headers);
  if (!upstream.body) {
    return new Response(null, { status: upstream.status, headers: responseHeaders });
  }

  // Pump the upstream body through a stream we own, so we can (a) surface an upstream
  // drop to the client as a stream error — letting the SSE client reconnect (RK-09) —
  // without an unhandled rejection, and (b) release the upstream when the client
  // disconnects (no leaked connection). No buffering, so SSE stays incremental.
  const reader = upstream.body.getReader();
  const stream = new ReadableStream<Uint8Array>({
    async pull(controller) {
      try {
        const { done, value } = await reader.read();
        if (done) {
          controller.close();
          return;
        }
        controller.enqueue(value);
      } catch (error) {
        controller.error(error);
      }
    },
    cancel(reason) {
      void reader.cancel(reason);
    },
  });

  return new Response(stream, { status: upstream.status, headers: responseHeaders });
}
