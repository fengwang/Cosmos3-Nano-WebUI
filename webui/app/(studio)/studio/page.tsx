"use client";

import { useEffect } from "react";

import { useStudio } from "@/app/(studio)/StudioProvider";
import type { Stage } from "@/app/(studio)/StudioProvider";
import { ComposePanel } from "@/components/studio/ComposePanel";
import { InspectPanel } from "@/components/studio/InspectPanel";
import { ReviewPanel } from "@/components/studio/ReviewPanel";
import { RunPanel } from "@/components/studio/RunPanel";
import { Tabs } from "@/components/Tabs";

import styles from "./page.module.css";

const TABS = [
  { id: "compose", label: "Compose" },
  { id: "inspect", label: "Inspect" },
  { id: "run", label: "Run" },
  { id: "review", label: "Review" },
];

export default function StudioPage() {
  const { stage, setStage, openJob } = useStudio();

  // Deep-link re-open from History: /studio?job=<id>&mode=<mode> → load into Review.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const job = params.get("job");
    if (job) openJob(job, params.get("mode") ?? "t2v");
  }, [openJob]);

  return (
    <section aria-label="Generation studio" className={styles.studio}>
      <h1>Generation Studio</h1>
      <Tabs tabs={TABS} active={stage} onChange={(id) => setStage(id as Stage)} ariaLabel="Studio stages" />
      <div className={styles.panel}>
        <div id="panel-compose" role="tabpanel" aria-labelledby="tab-compose" hidden={stage !== "compose"} tabIndex={0}>
          <ComposePanel />
        </div>
        <div id="panel-inspect" role="tabpanel" aria-labelledby="tab-inspect" hidden={stage !== "inspect"} tabIndex={0}>
          <InspectPanel />
        </div>
        <div id="panel-run" role="tabpanel" aria-labelledby="tab-run" hidden={stage !== "run"} tabIndex={0}>
          <RunPanel />
        </div>
        <div id="panel-review" role="tabpanel" aria-labelledby="tab-review" hidden={stage !== "review"} tabIndex={0}>
          <ReviewPanel />
        </div>
      </div>
    </section>
  );
}
