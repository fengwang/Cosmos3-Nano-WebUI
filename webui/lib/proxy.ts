// Pure Calculations for the BFF proxy — no I/O (ACD: Calculations). The impure
// fetch/stream shell lives in lib/proxyFetch.ts so this module stays pure/testable.

/** Default internal upstream when API_INTERNAL_URL is unset (matches docker-compose). */
export const DEFAULT_API_BASE = "http://api:8000";

// Hop-by-hop + connection-specific headers that must not be forwarded across the proxy.
const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "content-length",
  "host",
]);

/** Build the upstream URL for `/api/<segments>?<search>` → `<base>/<segments>?<search>`. */
export function buildUpstreamUrl(base: string, segments: string[], search: string): string {
  const trimmedBase = base.replace(/\/+$/, "");
  const path = segments.map(encodeURIComponent).join("/");
  return `${trimmedBase}/${path}${search}`;
}

/**
 * Headers to send upstream: drop hop-by-hop + host headers. Returns a new Headers —
 * the caller's input is untouched. There is no application-layer auth, so the proxy
 * injects no API key; any client-supplied header is forwarded like any other and
 * ignored by the API.
 */
export function filterForwardHeaders(incoming: Headers): Headers {
  const out = new Headers();
  incoming.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) out.set(key, value);
  });
  return out;
}

// Response-only: the fetch client (undici) auto-decompresses the body but retains
// `content-encoding`; forwarding it would mislabel the now-plaintext body. Strip it
// on the response (NOT on the request — a compressed request body must keep its label).
const RESPONSE_STRIP = new Set([...HOP_BY_HOP, "content-encoding"]);

/**
 * Headers to return to the browser: drop hop-by-hop + content-encoding and force
 * `X-Accel-Buffering: no` so SSE streams are not buffered. Returns a new Headers.
 */
export function filterResponseHeaders(upstream: Headers): Headers {
  const out = new Headers();
  upstream.forEach((value, key) => {
    if (!RESPONSE_STRIP.has(key.toLowerCase())) out.set(key, value);
  });
  out.set("x-accel-buffering", "no");
  return out;
}
