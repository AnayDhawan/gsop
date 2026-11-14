import { describe, expect, it } from "vitest";
import { bodyOfTarget, viewName } from "./names";

describe("names", () => {
  it("names views", () => {
    expect(viewName("shackleton_rim__base")).toBe("Shackleton rim, Base");
    expect(viewName("connecting_ridge_c1__power_night")).toBe("Connecting Ridge C1, Power and night");
  });
  it("assigns bodies", () => {
    expect(bodyOfTarget("jezero")).toBe("Mars");
    expect(bodyOfTarget("shackleton_rim")).toBe("Moon");
  });
});
