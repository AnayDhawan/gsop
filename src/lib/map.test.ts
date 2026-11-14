import { describe, expect, it } from "vitest";
import { DEFAULT_TOGGLES, project, visibleItems, type MapItem } from "./map";

const b = { west: -180, south: -50, east: 180, north: 80 };

describe("project", () => {
  it("puts the corners at the corners", () => {
    expect(project(80, -180, b)).toEqual({ x: 0, y: 0 });
    expect(project(-50, 180, b)).toEqual({ x: 100, y: 100 });
  });
  it("puts the prime meridian in the middle and north above south", () => {
    expect(project(15, 0, b).x).toBe(50);
    expect(project(60, 0, b).y).toBeLessThan(project(-20, 0, b).y);
  });
});

const item = (kind: MapItem["kind"], id: string): MapItem => ({ kind, id, label: id, lat: 0, lon: 0, latText: "0", lonText: "0", details: [] });

describe("visibleItems", () => {
  const items = [item("tile", "t"), item("site", "s"), item("control", "c"), item("candidate", "k"), item("region", "r")];
  it("hides candidates and tiles by default and lists controls first", () => {
    expect(visibleItems(items, DEFAULT_TOGGLES).map((i) => i.id)).toEqual(["c", "s", "r"]);
  });
  it("shows what is switched on", () => {
    expect(visibleItems(items, { ...DEFAULT_TOGGLES, tile: true, control: false }).map((i) => i.id)).toEqual(["s", "r", "t"]);
  });
});
