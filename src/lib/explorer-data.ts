// Server side: build the explorer rows from sites.json, site_lookup.json and claims.csv.
import { claim, lookupFile, sitesFile } from "./data";
import type { Cell, ExplorerRow } from "./explorer";

export function explorerData(): { rows: ExplorerRow[]; views: { Moon: string[]; Mars: string[] } } {
  const lookup = lookupFile();
  const summary = lookup.summary_by_view;
  const order = (a: string, b: string) => Number(b.endsWith("__base")) - Number(a.endsWith("__base")) || a.localeCompare(b);
  const views = {
    Moon: Object.keys(summary).filter((v) => summary[v].body === "moon").sort(order),
    Mars: Object.keys(summary).filter((v) => summary[v].body === "mars").sort(order),
  };
  const rows: ExplorerRow[] = sitesFile().sites.map((s) => {
    const cells: Record<string, Cell> = {};
    const pct: Record<string, number> = {};
    for (const [view, e] of Object.entries(lookup.sites[s.id] ?? {})) {
      if (e.status === "scored") {
        cells[view] = {
          status: "scored",
          score: claim(`lookup.${s.id}.${view}.score`),
          percentile: claim(`lookup.${s.id}.${view}.percentile`),
          flagged: e.top5_in_90pct_runs,
        };
        pct[view] = e.percentile;
      } else {
        cells[view] = { status: e.status, reason: e.reason };
      }
    }
    return { id: s.id, slug: s.slug, name: s.name, body: s.body, list: s.list, country: s.country, v1_used: s.v1_used, cells, pct };
  });
  return { rows, views };
}
