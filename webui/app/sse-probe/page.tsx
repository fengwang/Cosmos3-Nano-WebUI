"use client";

// Test harness page (development only — 404 in production builds): drives the real SSE
// client through the real BFF proxy so the E2E gate can prove incremental delivery,
// Last-Event-ID reconnect/resume, AND polling fallback end-to-end (RK-09).
// Query: ?job=&count=&drop=&fail=all&poll=1&maxRetries= . Not part of the studio UI (S9).
import { notFound } from "next/navigation";
import { useEffect, useState } from "react";

import { createEventStream } from "@/lib/sse/createEventStream";

interface Row {
  event: string;
  data: string;
  id?: string;
}

export default function SseProbe() {
  if (process.env.NODE_ENV === "production") notFound();

  const [rows, setRows] = useState<Row[]>([]);
  const [status, setStatus] = useState<"streaming" | "done">("streaming");

  useEffect(() => {
    const sp = new URLSearchParams(window.location.search);
    const job = sp.get("job") ?? "probe";
    const poll = sp.get("poll") === "1";
    const maxRetries = sp.get("maxRetries") ? Number(sp.get("maxRetries")) : undefined;

    const query = new URLSearchParams({ count: sp.get("count") ?? "3" });
    if (sp.get("drop")) query.set("drop", sp.get("drop") as string);
    if (sp.get("fail")) query.set("fail", sp.get("fail") as string);

    const controller = new AbortController();
    void createEventStream({
      url: `/api/v1/jobs/${encodeURIComponent(job)}/events?${query.toString()}`,
      signal: controller.signal,
      baseDelayMs: 10,
      capDelayMs: 50,
      maxRetries,
      onEvent: (event) => {
        setRows((prev) => [...prev, { event: event.event, data: event.data, id: event.id }]);
        if (event.event === "done") setStatus("done");
      },
      pollFallback: poll
        ? async () => {
            const res = await fetch(`/api/v1/jobs/${encodeURIComponent(job)}`);
            const data = (await res.json()) as { status?: string };
            setRows((prev) => [...prev, { event: "fallback", data: data.status ?? "unknown" }]);
            setStatus("done");
          }
        : undefined,
    });
    return () => controller.abort();
  }, []);

  return (
    <div>
      <h1>SSE probe</h1>
      <p data-testid="status">{status}</p>
      <ul data-testid="events">
        {rows.map((row, i) => (
          <li key={i} data-event={row.event} data-id={row.id}>
            {row.data}
          </li>
        ))}
      </ul>
    </div>
  );
}
