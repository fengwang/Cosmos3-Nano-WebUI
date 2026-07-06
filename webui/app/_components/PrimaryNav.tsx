"use client";

import { usePathname } from "next/navigation";

import { NavRail } from "@/design-system/components/NavRail";
import type { NavItem } from "@/design-system/components/NavRail";

// S9 studio IA: the four work areas live in one /studio workspace; Reasoning + History are siblings.
const ITEMS: NavItem[] = [
  { href: "/studio", label: "Studio" },
  { href: "/chat", label: "Reasoning" },
  { href: "/action", label: "Action" },
  { href: "/history", label: "History" },
  { href: "/gallery", label: "Gallery" },
];

/** Reads the active route (the Action) and renders the pure NavRail. Nested routes mark their section. */
export function PrimaryNav() {
  const pathname = usePathname() ?? "/";
  const current = ITEMS.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`))?.href ?? pathname;
  return <NavRail items={ITEMS} currentPath={current} />;
}
