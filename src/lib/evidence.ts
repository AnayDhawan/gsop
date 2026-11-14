// Pure helpers for the optional measured-evidence section (issue C8).
import type { Measurement } from "./types";

export type EvidenceRow = {
  dataset: string;
  variable: string;
  stat: string;
  radius: string; // shown as stored
  value: string; // display string from claims.csv, or "not measured"
  units: string;
  product: string; // product and version
  note: string;
};

export type Evidence = { rows: EvidenceRow[]; approximateOnly: boolean };

/**
 * Rows a page may show for one site. Rows marked page_ok = false are never shown (the run sets that for the smaller
 * radius at approximate coordinates). A null value reads "not measured" with its note. `claimFor` resolves the number.
 */
export function evidenceFor(rows: Measurement[], claimFor: (m: Measurement) => string): Evidence {
  const shown = rows.filter((m) => m.page_ok);
  return {
    approximateOnly: rows.some((m) => m.coord_flag === "approx"),
    rows: shown.map((m) => ({
      dataset: m.dataset,
      variable: m.variable,
      stat: m.stat,
      radius: m.radius_km,
      value: m.display === null ? "not measured" : claimFor(m),
      units: m.units,
      product: [m.product_id, m.version].filter(Boolean).join(" "),
      note: m.note,
    })),
  };
}

export function groupByDataset(rows: EvidenceRow[]): [string, EvidenceRow[]][] {
  const g = new Map<string, EvidenceRow[]>();
  for (const r of rows) g.set(r.dataset, [...(g.get(r.dataset) ?? []), r]);
  return [...g.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}

/** Claim id for each measurement with a value, in file order. Mirrors scripts/gsop_data/claims.py, duplicates get #n. */
export function claimIds(siteId: string, rows: Measurement[]): Map<Measurement, string> {
  const out = new Map<Measurement, string>();
  const seen = new Map<string, number>();
  for (const m of rows) {
    if (m.display === null) continue;
    const k = `v2.evidence.${siteId}.r${m.radius_km}.${m.dataset}.${m.variable}.${m.stat}`;
    const n = seen.get(k) ?? 0;
    seen.set(k, n + 1);
    out.set(m, n === 0 ? k : `${k}#${n}`);
  }
  return out;
}
