// Pure helpers for the site explorer (issue C5). No file access here, so the client component can import it.
import { viewName } from "./names";

export type Cell = { status: string; score?: string; percentile?: string; flagged?: boolean; reason?: string };

export type ExplorerRow = {
  id: string;
  slug: string;
  name: string;
  body: "Moon" | "Mars";
  list: "known" | "candidate";
  country: string | null;
  v1_used: boolean | null;
  cells: Record<string, Cell>; // by view, strings come from claims.csv
  pct: Record<string, number>; // by view, used only to sort
};

export type Filters = {
  body: "Moon" | "Mars";
  view: string;
  list: "all" | "known" | "candidate";
  v1: "all" | "yes" | "no" | "unknown";
  result: "all" | "scored" | "unscored";
  flaggedOnly: boolean;
  q: string;
  sort: "name" | "pct_desc" | "pct_asc";
};

export const DEFAULT_VIEW: Record<"Moon" | "Mars", string> = { Moon: "shackleton_rim__base", Mars: "jezero__base" };

export function defaultFilters(): Filters {
  return { body: "Moon", view: DEFAULT_VIEW.Moon, list: "all", v1: "all", result: "all", flaggedOnly: false, q: "", sort: "name" };
}

export function viewOptions(views: string[]): { value: string; label: string }[] {
  return views.map((v) => ({ value: v, label: viewName(v) }));
}

const norm = (s: string) => s.normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();

export function filterRows(rows: ExplorerRow[], f: Filters): ExplorerRow[] {
  const q = norm(f.q.trim());
  const out = rows.filter((r) => {
    if (r.body !== f.body) return false;
    if (f.list !== "all" && r.list !== f.list) return false;
    if (f.v1 !== "all") {
      const v = r.v1_used === true ? "yes" : r.v1_used === false ? "no" : "unknown";
      if (v !== f.v1) return false;
    }
    const cell = r.cells[f.view];
    const scored = cell?.status === "scored";
    if (f.result === "scored" && !scored) return false;
    if (f.result === "unscored" && scored) return false;
    if (f.flaggedOnly && !(scored && cell.flagged)) return false;
    if (q && !norm(`${r.name} ${r.country ?? ""}`).includes(q)) return false;
    return true;
  });
  const byName = (a: ExplorerRow, b: ExplorerRow) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id);
  if (f.sort === "name") return out.sort(byName);
  // Unscored rows go last whichever way the scored rows are ordered.
  return out.sort((a, b) => {
    const pa = a.pct[f.view];
    const pb = b.pct[f.view];
    if (pa === undefined && pb === undefined) return byName(a, b);
    if (pa === undefined) return 1;
    if (pb === undefined) return -1;
    return (f.sort === "pct_desc" ? pb - pa : pa - pb) || byName(a, b);
  });
}
