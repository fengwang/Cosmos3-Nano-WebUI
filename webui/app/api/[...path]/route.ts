// Same-origin catch-all BFF proxy (INV-1): the browser reaches the api ONLY through
// `/api/*` on the webui origin; all upstream access is server-side. Streams every
// method so SSE survives. The narrower `app/api/health/route.ts` alias wins for
// `/api/health` (Next resolves static segments before this dynamic catch-all).
import { forward } from "@/lib/proxyFetch";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

async function handle(
  req: Request,
  ctx: { params: Promise<{ path?: string[] }> },
): Promise<Response> {
  const { path = [] } = await ctx.params;
  return forward(req, path);
}

export const GET = handle;
export const POST = handle;
export const PUT = handle;
export const PATCH = handle;
export const DELETE = handle;
export const OPTIONS = handle;
export const HEAD = handle;
