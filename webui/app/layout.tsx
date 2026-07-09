import type { ReactNode } from "react";

import { themesCss } from "@/design-system/tokens/tokens";

import { PrimaryNav } from "./_components/PrimaryNav";
import { ThemeToggle } from "./_components/ThemeToggle";
import { Providers } from "./providers";
import "./globals.css";

export const metadata = {
  title: "Cosmos3-Nano Serving",
  description: "Neumorphic WebUI foundation + design system (Session 8).",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" data-theme="light">
      <head>
        {/* Token layer injected from the single source of truth (no .css/.ts drift). */}
        <style id="ds-tokens" dangerouslySetInnerHTML={{ __html: themesCss() }} />
      </head>
      <body>
        <Providers>
          <a className="skip-link" href="#main-content">
            Skip to main content
          </a>
          <div className="app-shell">
            <header className="app-header">
              <strong>Cosmos3-Nano Serving</strong>
              <ThemeToggle />
            </header>
            <PrimaryNav />
            <main id="main-content" className="app-main" tabIndex={-1}>
              {children}
            </main>
          </div>
          {/* Polite live region for async job/stream status (used from S9). */}
          <div aria-live="polite" className="sr-only" id="live-region" />
        </Providers>
      </body>
    </html>
  );
}
