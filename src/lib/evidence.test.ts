import { describe, expect, it } from "vitest";
import { claimIds, evidenceFor, groupByDataset } from "./evidence";
import type { Measurement } from "./types";

const m = (o: Partial<Measurement>): Measurement => ({
  dataset: "cop_dem",
  variable: "elevation",
  stat: "mean",
  radius_km: "10",
  units: "m",
  product_id: "COPERNICUS/DEM/GLO30_2024_1",
  version: "2024_1",
  doi_or_url: "https://example.org",
  date_range: "2010 to 2020",
  coord_flag: "ok",
  page_ok: true,
  note: "",
  value: 1100.4,
  display: "1100",
  ...o,
});

describe("evidenceFor", () => {
  it("shows a value through its claim and the product with its version", () => {
    const e = evidenceFor([m({})], () => "1100");
    expect(e.rows[0]).toMatchObject({ value: "1100", radius: "10", units: "m", product: "COPERNICUS/DEM/GLO30_2024_1 2024_1" });
  });

  it("shows a null as not measured, with its note, and never calls the claim", () => {
    const e = evidenceFor([m({ value: null, display: null, note: "no_images" })], () => {
      throw new Error("no claim exists for a null");
    });
    expect(e.rows[0].value).toBe("not measured");
    expect(e.rows[0].note).toBe("no_images");
  });

  it("drops rows the run marked not for pages, and flags approximate coordinates", () => {
    const rows = [m({ radius_km: "2", coord_flag: "approx", page_ok: false }), m({ coord_flag: "approx" })];
    const e = evidenceFor(rows, () => "x");
    expect(e.rows.map((r) => r.radius)).toEqual(["10"]);
    expect(e.approximateOnly).toBe(true);
  });

  it("is flagged as not approximate when every row is ok", () => {
    expect(evidenceFor([m({})], () => "x").approximateOnly).toBe(false);
  });
});

describe("claimIds", () => {
  it("matches the builder: one id per value, duplicates numbered, nulls skipped", () => {
    const a = m({});
    const b = m({});
    const c = m({ variable: "vv", value: null, display: null });
    const ids = claimIds("askja-caldera-moon", [a, b, c]);
    expect(ids.get(a)).toBe("v2.evidence.askja-caldera-moon.r10.cop_dem.elevation.mean");
    expect(ids.get(b)).toBe("v2.evidence.askja-caldera-moon.r10.cop_dem.elevation.mean#1");
    expect(ids.has(c)).toBe(false);
  });
});

describe("groupByDataset", () => {
  it("groups rows by dataset in a stable order", () => {
    const rows = evidenceFor([m({ dataset: "s2" }), m({ dataset: "cop_dem" }), m({ dataset: "s2", variable: "ndvi" })], () => "x").rows;
    expect(groupByDataset(rows).map(([d, r]) => [d, r.length])).toEqual([["cop_dem", 1], ["s2", 2]]);
  });
});
