import { describe, expect, it } from "vitest";
import { defaultFilters, filterRows, type ExplorerRow } from "./explorer";

const V = "shackleton_rim__base";
const row = (o: Partial<ExplorerRow> & { id: string; name: string }): ExplorerRow => ({
  slug: o.id,
  body: "Moon",
  list: "known",
  country: "Iceland",
  v1_used: false,
  cells: { [V]: { status: "scored", score: "20.0", percentile: "80.0", flagged: false } },
  pct: { [V]: 80 },
  ...o,
});

const rows: ExplorerRow[] = [
  row({ id: "a", name: "Askja caldera", pct: { [V]: 92 } }),
  row({ id: "b", name: "Mount Erebus", country: "Antarctica", v1_used: true, pct: { [V]: 60 }, cells: { [V]: { status: "scored", score: "10.0", percentile: "60.0", flagged: true } } }),
  row({ id: "c", name: "Lonar crater", country: "India", v1_used: null, list: "candidate", cells: { [V]: { status: "gated_out", reason: "vegetated" } }, pct: {} }),
  row({ id: "d", name: "Jezero analog", body: "Mars" }),
];

describe("filterRows", () => {
  it("keeps one body", () => {
    expect(filterRows(rows, defaultFilters()).map((r) => r.id)).toEqual(["a", "c", "b"]);
    expect(filterRows(rows, { ...defaultFilters(), body: "Mars" }).map((r) => r.id)).toEqual(["d"]);
  });
  it("filters by entry type", () => {
    expect(filterRows(rows, { ...defaultFilters(), list: "candidate" }).map((r) => r.id)).toEqual(["c"]);
  });
  it("filters by v1 used, keeping unknown separate", () => {
    expect(filterRows(rows, { ...defaultFilters(), v1: "yes" }).map((r) => r.id)).toEqual(["b"]);
    expect(filterRows(rows, { ...defaultFilters(), v1: "unknown" }).map((r) => r.id)).toEqual(["c"]);
    expect(filterRows(rows, { ...defaultFilters(), v1: "no" }).map((r) => r.id)).toEqual(["a"]);
  });
  it("filters by scored result and by flag", () => {
    expect(filterRows(rows, { ...defaultFilters(), result: "unscored" }).map((r) => r.id)).toEqual(["c"]);
    expect(filterRows(rows, { ...defaultFilters(), flaggedOnly: true }).map((r) => r.id)).toEqual(["b"]);
  });
  it("searches name and country, ignoring case and accents", () => {
    expect(filterRows(rows, { ...defaultFilters(), q: "ASKJA" }).map((r) => r.id)).toEqual(["a"]);
    expect(filterRows(rows, { ...defaultFilters(), q: "antarct" }).map((r) => r.id)).toEqual(["b"]);
    expect(filterRows(rows, { ...defaultFilters(), q: "zzz" })).toEqual([]);
  });
  it("sorts by percentile with unscored rows last", () => {
    expect(filterRows(rows, { ...defaultFilters(), sort: "pct_desc" }).map((r) => r.id)).toEqual(["a", "b", "c"]);
    expect(filterRows(rows, { ...defaultFilters(), sort: "pct_asc" }).map((r) => r.id)).toEqual(["b", "a", "c"]);
  });
});
