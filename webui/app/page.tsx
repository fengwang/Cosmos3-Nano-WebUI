import { redirect } from "next/navigation";

// The home route lands users on the Generation Studio (UX-S3). The Studio owns its
// own (studio) route-group provider, so `/` only redirects — it renders no Studio
// content itself and needs no provider.
export default function Home() {
  redirect("/studio");
}
