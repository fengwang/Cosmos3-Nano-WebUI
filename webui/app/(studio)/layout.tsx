import type { ReactNode } from "react";

import { StudioProvider } from "./StudioProvider";

/** The (studio) route group shares one StudioProvider (draft + active-job state) across its routes. */
export default function StudioLayout({ children }: { children: ReactNode }) {
  return <StudioProvider>{children}</StudioProvider>;
}
