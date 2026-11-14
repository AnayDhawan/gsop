// Single list of routes. The header, footer and tests read it, so a route cannot be missing from one of them.
export type NavItem = { href: string; label: string; description: string };

export const NAV: NavItem[] = [
  { href: "/map", label: "Honest Map", description: "Where v1 scores high, with the controls that failed in red" },
  { href: "/sites", label: "Sites", description: "Reference sites and candidates, with the v1 score at each" },
  { href: "/ledger", label: "Failure-First Ledger", description: "What failed and where the analogy breaks down" },
  { href: "/method", label: "Methods and limits", description: "How the screening works, and what it cannot tell you" },
  { href: "/credits", label: "Data credits", description: "Open data behind the scores" },
];

export const REPO_URL = "https://github.com/AnayDhawan/GSOP";

export function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(href + "/");
}
