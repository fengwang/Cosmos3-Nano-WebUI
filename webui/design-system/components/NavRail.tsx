import type { ReactNode } from "react";

import styles from "./NavRail.module.css";

export interface NavItem {
  href: string;
  label: string;
  icon?: ReactNode;
}

export interface NavRailProps {
  items: NavItem[];
  /** The active route. Pure prop — the Action of reading the path lives in a wrapper. */
  currentPath: string;
  ariaLabel?: string;
}

/**
 * Vertical navigation rail. Pure (no router hook) so it tests without mocks. The
 * current item is marked with aria-current + a border/inset/weight delta — never
 * color alone. Every item carries a visible text label as its accessible name.
 */
export function NavRail({ items, currentPath, ariaLabel = "Primary" }: NavRailProps) {
  return (
    <nav aria-label={ariaLabel} className={styles.rail}>
      <ul className={styles.list}>
        {items.map((item) => {
          const current = item.href === currentPath;
          return (
            <li key={item.href}>
              <a
                href={item.href}
                className={styles.item}
                aria-current={current ? "page" : undefined}
                data-current={current ? "true" : undefined}
              >
                {item.icon ? (
                  <span className={styles.icon} aria-hidden="true">
                    {item.icon}
                  </span>
                ) : null}
                <span className={styles.label}>{item.label}</span>
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
