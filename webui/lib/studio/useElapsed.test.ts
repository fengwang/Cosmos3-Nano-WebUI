import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useElapsed } from "@/lib/studio/useElapsed";

describe("useElapsed", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("ticks while non-terminal and stops once terminal", () => {
    const { result, rerender } = renderHook(({ key, terminal }) => useElapsed(key, terminal), {
      initialProps: { key: "job1", terminal: false },
    });
    expect(result.current).toBe(0);
    act(() => vi.advanceTimersByTime(1000));
    expect(result.current).toBeGreaterThan(0);
    const atStop = result.current;
    rerender({ key: "job1", terminal: true });
    act(() => vi.advanceTimersByTime(2000));
    expect(result.current).toBe(atStop); // no further ticks after terminal
  });

  it("resets to 0 when the job key changes", () => {
    const { result, rerender } = renderHook(({ key, terminal }) => useElapsed(key, terminal), {
      initialProps: { key: "job1", terminal: false },
    });
    act(() => vi.advanceTimersByTime(1000));
    expect(result.current).toBeGreaterThan(0);
    rerender({ key: "job2", terminal: false });
    expect(result.current).toBe(0);
  });

  it("does not tick when there is no job key", () => {
    const { result } = renderHook(() => useElapsed(undefined, false));
    act(() => vi.advanceTimersByTime(2000));
    expect(result.current).toBe(0);
  });
});
