import { describe, expect, it } from "vitest";
import { shortHash, sourceName, statusLabel } from "./format";

describe("format", () => {
  it("turns stored status codes into plain words", () => {
    expect(statusLabel("not_testable")).toBe("Not testable");
    expect(statusLabel("fail")).toBe("Failed");
    expect(statusLabel("something_new")).toBe("something new");
  });
  it("shortens a hash and a v1 path", () => {
    expect(shortHash("0123456789abcdef")).toBe("0123456789ab");
    expect(sourceName("gsop_v1/results/moon/validation.json")).toBe("v1: results/moon/validation.json");
  });
});
