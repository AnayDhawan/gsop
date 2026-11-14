import { describe, expect, it } from "vitest";
import { generateStaticParams } from "./page";
import { lookupFile, sitesFile } from "@/lib/data";

describe("per-site pages", () => {
  it("builds one page for every slug in sites.json", () => {
    const slugs = new Set(sitesFile().sites.map((s) => s.slug));
    const params = generateStaticParams().map((p) => p.slug);
    expect(new Set(params)).toEqual(slugs);
    expect(params.length).toBe(slugs.size);
  });

  it("gives every site a lookup entry, so no page is built without scores or a reason", () => {
    const lookup = lookupFile().sites;
    for (const s of sitesFile().sites) expect(Object.keys(lookup[s.id] ?? {}).length, s.id).toBeGreaterThan(0);
  });

  it("marks every row unreviewed with no sources", () => {
    for (const s of sitesFile().sites) {
      expect(s.status, s.id).toBe("draft");
      expect(s.sources_ok, s.id).toBe(false);
    }
  });
});
