// History persistence codec (ACD: pure encode/decode/merge; history). localStorage I/O is the Action
// (the useHistory hook); this stays pure + tolerant of corrupt/foreign data so a bad blob can't crash the
// list. No api "list jobs" endpoint exists (filed to S7) — the studio is the source of truth for which
// jobs it submitted; live status is re-hydrated via GET /v1/jobs/{id}.

import type { HistoryEntry } from "@/lib/studio/types";

export const HISTORY_KEY = "cosmos3.studio.history.v1";
const CAP = 50;

function coerce(value: unknown): HistoryEntry | null {
  if (!value || typeof value !== "object") return null;
  const e = value as Record<string, unknown>;
  if (typeof e.id !== "string" || typeof e.mode !== "string" || typeof e.createdAt !== "string") return null;
  return { id: e.id, mode: e.mode, createdAt: e.createdAt, summary: typeof e.summary === "string" ? e.summary : "" };
}

/** Tolerant decode: null / malformed / non-array → []. */
export function decodeHistory(raw: string | null): HistoryEntry[] {
  if (!raw) return [];
  try {
    const value: unknown = JSON.parse(raw);
    if (!Array.isArray(value)) return [];
    return value.map(coerce).filter((e): e is HistoryEntry => e !== null);
  } catch {
    return [];
  }
}

export function encodeHistory(entries: HistoryEntry[]): string {
  return JSON.stringify(entries.slice(0, CAP));
}

/** Prepend an entry, dedupe by id (newest wins), cap the list. Pure. */
export function addEntry(entries: HistoryEntry[], entry: HistoryEntry, cap = CAP): HistoryEntry[] {
  return [entry, ...entries.filter((e) => e.id !== entry.id)].slice(0, cap);
}
