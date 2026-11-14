// Build-time loader for the committed data files. Import this from server components only (it reads the disk).
// Every number a page prints comes from claim(): a missing claim stops the build instead of printing a typed value.
import fs from "node:fs";
import path from "node:path";
import type { Control, LedgerEntry, LookupEntry, Measurement, Meta, Metric, Overlay, Region, Site, SummaryGroup, V2File, View } from "./types";

const ROOT = process.cwd();
const cache = new Map<string, unknown>();

function readText(rel: string): string {
  // Build-time read of committed files. The pages are prerendered, so nothing here runs at request time.
  return fs.readFileSync(path.join(/* turbopackIgnore: true */ ROOT, rel), "utf-8");
}

function readJson<T>(rel: string): T {
  if (!cache.has(rel)) cache.set(rel, JSON.parse(readText(rel)));
  return cache.get(rel) as T;
}

export const sitesFile = () => readJson<{ meta: Meta; sites: Site[] }>("public/data/sites.json");
export const lookupFile = () =>
  readJson<{ meta: Meta; sites: Record<string, Record<string, LookupEntry>>; summary_by_view: Record<string, { body: string; v1_used_true: SummaryGroup; v1_used_false: SummaryGroup; v1_used_unknown: SummaryGroup }> }>(
    "public/data/site_lookup.json",
  );
export const tilesFile = () => readJson<{ meta: Meta; views: Record<string, View> }>("public/data/tiles_top.json");
export const regionsFile = () => readJson<{ meta: Meta; regions: Region[] }>("public/data/regions.json");
export const metricsFile = () => readJson<{ meta: Meta; metrics: Metric[] }>("public/data/metrics.json");
export const ledgerFile = () => readJson<{ meta: Meta; entries: LedgerEntry[] }>("public/data/ledger.json");
export const controlsFile = () => readJson<{ meta: Meta; controls: Control[] }>("public/data/controls.json");
export const v2File = () => readJson<V2File>("public/data/v2.json");

function exists(rel: string): boolean {
  return fs.existsSync(path.join(/* turbopackIgnore: true */ ROOT, rel));
}

/** Site measurements from the optional v2 evidence run. Null when the file is absent, and the page then shows nothing. */
export function measurementsFile(): { meta: Meta; by_site: Record<string, Measurement[]> } | null {
  return exists("public/data/site_measurements.json") ? readJson("public/data/site_measurements.json") : null;
}

/** The imagery chip for a site, when the evidence run produced one. */
export function chipFor(slug: string): { src: string; credit: string | null } | null {
  if (!exists(`public/img/sites/${slug}.jpg`)) return null;
  let credit: string | null = null;
  if (exists("public/img/sites/credits.json")) {
    const c = readJson<{ credit?: string }>("public/img/sites/credits.json");
    credit = c.credit ?? null;
  }
  return { src: `/img/sites/${slug}.jpg`, credit };
}

export const overlay = (target: string) => readJson<Overlay>(`public/data/overlays/${target}.json`);
export const OVERLAY_TARGETS = ["connecting_ridge_c1", "shackleton_rim", "jezero"] as const;

// ---- claims.csv

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') {
        cell += '"';
        i++;
      } else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") {
      row.push(cell);
      cell = "";
    } else if (c === "\n") {
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    } else cell += c;
  }
  if (cell || row.length) {
    row.push(cell);
    rows.push(row);
  }
  return rows;
}

function claimsMap(): Map<string, string> {
  if (!cache.has("claims")) {
    const m = new Map<string, string>();
    for (const r of parseCsv(readText("public/data/claims.csv")).slice(1)) m.set(r[0], r[1]);
    cache.set("claims", m);
  }
  return cache.get("claims") as Map<string, string>;
}

/** The display string for a claim id. Throws when the id has no row, so the build fails. */
export function claim(id: string): string {
  const v = claimsMap().get(id);
  if (v === undefined) throw new Error(`no claims.csv row for ${id}`);
  return v;
}

export function hasClaim(id: string): boolean {
  return claimsMap().has(id);
}

// ---- text that other files own

/** The E32 sentence, read from the ledger header. The check script keeps it equal to docs/E32.txt. */
export function e32Sentence(): string {
  const s = ledgerFile().meta.uncertainty_sentence;
  if (!s) throw new Error("ledger.json has no uncertainty_sentence");
  return s;
}

/** Headline and support line, read from docs/DECISIONS_SITE.md so the page cannot drift from the locked text. */
export function headline(): { headline: string; support: string } {
  const t = readText("docs/DECISIONS_SITE.md");
  const h = t.match(/^Headline: \*\*(.+?)\*\*/m);
  const s = t.match(/^Support line: \*\*(.+?)\*\*/m);
  if (!h || !s) throw new Error("docs/DECISIONS_SITE.md: headline lines not found");
  return { headline: h[1], support: s[1] };
}
