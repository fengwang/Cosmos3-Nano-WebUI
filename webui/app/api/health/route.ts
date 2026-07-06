// Health alias preserved for the docker-compose `webui` healthcheck:
// GET /api/health → upstream /v1/health/ready, server-side only (INV-1).
// Implemented over the shared proxy Action — no bespoke fetch, no compat layer.
import { forward } from "@/lib/proxyFetch";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET(req: Request): Promise<Response> {
  return forward(req, ["v1", "health", "ready"]);
}
