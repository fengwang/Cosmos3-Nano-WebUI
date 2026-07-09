"use client";

import { useCallback, useEffect, useState } from "react";

import { addEntry, decodeHistory, encodeHistory, HISTORY_KEY } from "@/lib/studio/history";
import type { HistoryEntry } from "@/lib/studio/types";

function readHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  return decodeHistory(window.localStorage.getItem(HISTORY_KEY));
}

/** localStorage-backed job history (the Action shell over the pure history codec). */
export function useHistory(): { entries: HistoryEntry[]; record: (entry: HistoryEntry) => void } {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  // Hydrate after mount (avoids SSR/client mismatch; localStorage is client-only).
  useEffect(() => {
    setEntries(readHistory());
  }, []);

  const record = useCallback((entry: HistoryEntry) => {
    setEntries((prev) => {
      const next = addEntry(prev, entry);
      try {
        window.localStorage.setItem(HISTORY_KEY, encodeHistory(next));
      } catch {
        // localStorage can throw (private mode / quota) — history is best-effort.
      }
      return next;
    });
  }, []);

  return { entries, record };
}
