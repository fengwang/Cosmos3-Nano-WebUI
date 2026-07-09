import { ActionWorkspace } from "@/components/action-viewer/ActionWorkspace";

export const metadata = { title: "Action · Cosmos3-Nano" };

// Top-level route (sibling of /chat, /history) — inherits the root app shell + #live-region, and is
// deliberately OUTSIDE the (studio) group so it does NOT carry the generation StudioProvider. The WebGL
// viewer inside ActionWorkspace is loaded client-only (next/dynamic ssr:false).
export default function ActionPage() {
  return (
    <section aria-label="Action viewer">
      <h1>Action</h1>
      <p>3D / URDF kinematic action viewer — render an embodiment&rsquo;s rollout synced to its trajectory.</p>
      <ActionWorkspace />
    </section>
  );
}
