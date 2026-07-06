"use client";

import { useQuery } from "@tanstack/react-query";

import { useHistory } from "@/app/(studio)/useHistory";
import { StatusBadge } from "@/components/StatusBadge";
import { Card } from "@/design-system";
import { API_PREFIX } from "@/lib/api/client";
import type { Job } from "@/lib/studio/types";

import styles from "./history.module.css";

/** One history row: re-hydrates live status from GET /v1/jobs/{id}; degrades to "unavailable" on 404. */
function HistoryRow({ id, mode, summary }: { id: string; mode: string; summary: string }) {
  const { data, isError, isLoading } = useQuery({
    queryKey: ["job", id],
    retry: false,
    queryFn: async (): Promise<Job | null> => {
      const res = await fetch(`${API_PREFIX}/v1/jobs/${encodeURIComponent(id)}`, { cache: "no-store" });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error(`status ${res.status}`);
      return (await res.json()) as Job;
    },
  });

  const status = data?.status ?? (isLoading ? "loading" : data === null || isError ? "unavailable" : "loading");

  return (
    <li className={styles.row}>
      <a
        href={`/studio?job=${encodeURIComponent(id)}&mode=${encodeURIComponent(mode)}`}
        className={styles.link}
        data-testid="history-open"
      >
        <span className={styles.mode}>{mode}</span>
        <span className={styles.summary}>{summary || id}</span>
      </a>
      <StatusBadge status={status} />
    </li>
  );
}

/** History/gallery of past jobs (client localStorage), each re-hydrated against the api. */
export function HistoryList() {
  const { entries } = useHistory();
  if (entries.length === 0) {
    return (
      <Card title="History">
        <p>No jobs yet. Generate something in the Studio and it will appear here.</p>
      </Card>
    );
  }
  return (
    <Card title="History">
      <ul className={styles.list} data-testid="history-list">
        {entries.map((entry) => (
          <HistoryRow key={entry.id} id={entry.id} mode={entry.mode} summary={entry.summary} />
        ))}
      </ul>
    </Card>
  );
}
