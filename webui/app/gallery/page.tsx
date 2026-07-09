"use client";

import { useState } from "react";

import {
  Card,
  Input,
  NavRail,
  PillButton,
  ProgressRing,
  Sheet,
  Surface,
} from "@/design-system";

import styles from "./gallery.module.css";

export default function GalleryPage() {
  const [sheetOpen, setSheetOpen] = useState(false);

  return (
    <div className={styles.page}>
      <h1>Component gallery</h1>
      <p>
        Every core component in its states. This page is the automated a11y / contrast /
        keyboard test surface and the reference for the S9 studio and S10 viewer.
      </p>

      <section aria-labelledby="h-surface">
        <h2 id="h-surface">Surface (primitive)</h2>
        <div className={styles.row}>
          <Surface variant="raised" className={styles.demo}>
            raised
          </Surface>
          <Surface variant="inset" className={styles.demo}>
            inset
          </Surface>
          <Surface variant="flat" className={styles.demo}>
            flat
          </Surface>
        </div>
      </section>

      <section aria-labelledby="h-card">
        <h2 id="h-card">Card</h2>
        <div className={styles.row}>
          <Card title="Occupancy">
            <p>A titled card is a labelled region with a heading.</p>
          </Card>
          <Card>
            <p>An untitled card is a plain raised surface.</p>
          </Card>
        </div>
      </section>

      <section aria-labelledby="h-pill">
        <h2 id="h-pill">PillButton</h2>
        <div className={styles.row}>
          <PillButton>Neutral</PillButton>
          <PillButton tone="accent">Accent</PillButton>
          <PillButton tone="danger">Danger</PillButton>
          <PillButton selected>Selected</PillButton>
          <PillButton disabled>Disabled</PillButton>
        </div>
      </section>

      <section aria-labelledby="h-input">
        <h2 id="h-input">Input</h2>
        <div className={styles.row}>
          <Input label="Prompt" placeholder="A robotic arm wiping a plate…" />
          <Input label="Seed" defaultValue="123" />
          <Input label="Frames" error="Must be between 16 and 400." defaultValue="9000" />
        </div>
      </section>

      <section aria-labelledby="h-ring">
        <h2 id="h-ring">ProgressRing</h2>
        <div className={styles.row}>
          <ProgressRing value={85} label="Occupancy" />
          <ProgressRing value={60} label="Lease contract" />
          <ProgressRing value={30} label="Financial" />
        </div>
      </section>

      <section aria-labelledby="h-nav">
        <h2 id="h-nav">NavRail</h2>
        <Surface variant="raised" className={styles.navDemo}>
          <NavRail
            ariaLabel="Demo navigation"
            currentPath="/run"
            items={[
              { href: "/compose", label: "Compose" },
              { href: "/inspect", label: "Inspect" },
              { href: "/run", label: "Run" },
              { href: "/review", label: "Review" },
            ]}
          />
        </Surface>
      </section>

      <section aria-labelledby="h-sheet">
        <h2 id="h-sheet">Sheet</h2>
        <PillButton onClick={() => setSheetOpen(true)}>Open sheet</PillButton>
        <Sheet open={sheetOpen} onClose={() => setSheetOpen(false)} title="Settings">
          <p>A modal sheet: focus moves in, Tab is trapped, Escape closes.</p>
          <Input label="Display name" defaultValue="Studio" />
          <div className={styles.row}>
            <PillButton tone="accent" onClick={() => setSheetOpen(false)}>
              Save
            </PillButton>
            <PillButton onClick={() => setSheetOpen(false)}>Cancel</PillButton>
          </div>
        </Sheet>
      </section>
    </div>
  );
}
