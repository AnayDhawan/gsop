import { describe, expect, it } from "vitest";
import { inlineParts, toTree, type Block } from "./mdblocks";

const b = (type: Block["type"], text: string, level = 0): Block => ({ type, text, level });

describe("toTree", () => {
  it("nests bullets by level and keeps headings and paragraphs in order", () => {
    const tree = toTree([b("h2", "A"), b("li", "one"), b("li", "one.a", 1), b("li", "one.b", 1), b("li", "two"), b("h3", "B"), b("p", "text")]);
    expect(tree.map((n) => n.kind)).toEqual(["heading", "list", "heading", "p"]);
    const list = tree[1];
    if (list.kind !== "list") throw new Error("expected a list");
    expect(list.items.map((i) => i.text)).toEqual(["one", "two"]);
    const children = list.items[0].children[0];
    if (children.kind !== "list") throw new Error("expected a nested list");
    expect(children.items.map((i) => i.text)).toEqual(["one.a", "one.b"]);
  });

  it("can skip an opening paragraph", () => {
    expect(toTree([b("p", "intro"), b("h2", "A")], true).map((n) => n.kind)).toEqual(["heading"]);
    expect(toTree([b("h2", "A")], true).map((n) => n.kind)).toEqual(["heading"]);
  });

  it("nests a bullet that skips a level under the one before it, and loses nothing", () => {
    const tree = toTree([b("li", "top"), b("li", "deep", 2), b("li", "next")]);
    const list = tree[0];
    if (list.kind !== "list") throw new Error("expected a list");
    expect(list.items.map((i) => i.text)).toEqual(["top", "next"]);
    const child = list.items[0].children[0];
    if (child.kind !== "list") throw new Error("expected a nested list");
    expect(child.items.map((i) => i.text)).toEqual(["deep"]);
  });
});

describe("inlineParts", () => {
  it("separates code spans", () => {
    expect(inlineParts("see `x_y` now")).toEqual([
      { code: false, text: "see " },
      { code: true, text: "x_y" },
      { code: false, text: " now" },
    ]);
  });
  it("leaves plain text alone", () => {
    expect(inlineParts("plain")).toEqual([{ code: false, text: "plain" }]);
  });
});
