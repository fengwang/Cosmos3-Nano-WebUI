import Link from "next/link";

import { Card } from "@/design-system";

export default function Home() {
  return (
    <Card title="Cosmos3-Nano Serving">
      <p>Neumorphic WebUI foundation (Session 8). The generation/reasoning studio arrives in Session 9.</p>
      <p>
        <Link href="/gallery">Open the component gallery →</Link>
      </p>
      <p>
        API readiness is proxied same-origin at <code>/api/health</code> (INV-1) — the
        browser never reaches the api directly.
      </p>
    </Card>
  );
}
