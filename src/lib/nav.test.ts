import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { NAV, isActive } from "./nav";

describe("nav", () => {
  it("lists each route once", () => {
    const hrefs = NAV.map((n) => n.href);
    expect(new Set(hrefs).size).toBe(hrefs.length);
  });

  it("has a page file for every route", () => {
    for (const n of NAV) {
      expect(fs.existsSync(path.join(process.cwd(), "src/app", n.href, "page.tsx")), n.href).toBe(true);
    }
  });

  it("marks a route and its children as active", () => {
    expect(isActive("/sites", "/sites")).toBe(true);
    expect(isActive("/sites/askja-caldera", "/sites")).toBe(true);
    expect(isActive("/siteseeing", "/sites")).toBe(false);
    expect(isActive("/", "/map")).toBe(false);
  });
});
