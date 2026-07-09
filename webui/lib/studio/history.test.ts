import { describe, expect, it } from "vitest";

import { addEntry, decodeHistory, encodeHistory } from "@/lib/studio/history";
import type { HistoryEntry } from "@/lib/studio/types";

const entry = (id: string): HistoryEntry => ({ id, mode: "t2v", summary: "a robot", createdAt: "2026-06-22T00:00:00Z" });

describe("history codec", () => {
  it("round-trips entries", () => {
    const entries = [entry("a"), entry("b")];
    expect(decodeHistory(encodeHistory(entries))).toEqual(entries);
  });

  it("tolerates null, malformed, and non-array input", () => {
    expect(decodeHistory(null)).toEqual([]);
    expect(decodeHistory("not json")).toEqual([]);
    expect(decodeHistory("{}")).toEqual([]);
  });

  it("drops entries missing required fields", () => {
    expect(decodeHistory(JSON.stringify([{ id: "x" }, entry("ok")]))).toEqual([entry("ok")]);
  });
});

describe("addEntry", () => {
  it("prepends newest-first and dedupes by id", () => {
    const after = addEntry([entry("a")], entry("b"));
    expect(after.map((e) => e.id)).toEqual(["b", "a"]);
    expect(addEntry(after, entry("a")).map((e) => e.id)).toEqual(["a", "b"]);
  });

  it("caps the list length", () => {
    let list: HistoryEntry[] = [];
    for (let i = 0; i < 60; i++) list = addEntry(list, entry(`j${i}`), 50);
    expect(list.length).toBe(50);
  });
});
