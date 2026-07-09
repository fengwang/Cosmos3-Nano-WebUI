"use client";

import { useRef } from "react";
import type { KeyboardEvent } from "react";

import { nextTabIndex } from "@/lib/studio/tabs";

import styles from "./Tabs.module.css";

export interface TabItem {
  id: string;
  label: string;
}

export interface TabsProps {
  tabs: TabItem[];
  active: string;
  onChange: (id: string) => void;
  ariaLabel: string;
}

/**
 * Accessible tablist (roving focus via the pure `nextTabIndex`, `aria-selected`, `aria-controls`).
 * The active tab is signalled by a border-weight + inset delta, not color alone (RK-18). Panels are
 * rendered by the caller with `id={panel-<id>}` + `aria-labelledby={tab-<id>}` + `role="tabpanel"`.
 */
export function Tabs({ tabs, active, onChange, ariaLabel }: TabsProps) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const activeIndex = Math.max(0, tabs.findIndex((t) => t.id === active));

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const next = nextTabIndex(activeIndex, event.key, tabs.length);
    if (next !== activeIndex) {
      event.preventDefault();
      onChange(tabs[next].id);
      refs.current[next]?.focus();
    }
  }

  return (
    <div role="tablist" aria-label={ariaLabel} className={styles.tablist} onKeyDown={onKeyDown}>
      {tabs.map((tab, i) => {
        const selected = tab.id === active;
        return (
          <button
            key={tab.id}
            ref={(el) => {
              refs.current[i] = el;
            }}
            type="button"
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={selected}
            aria-controls={`panel-${tab.id}`}
            tabIndex={selected ? 0 : -1}
            data-selected={selected ? "true" : undefined}
            className={styles.tab}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
