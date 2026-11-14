// Turns the flat blocks that scripts/gsop_data/v2.py writes into a tree a page can render. Pure, so it is tested.
export type Block = { type: "h2" | "h3" | "h4" | "li" | "p"; level: number; text: string };
export type Node = { kind: "heading"; depth: 2 | 3 | 4; text: string } | { kind: "p"; text: string } | { kind: "list"; items: { text: string; children: Node[] }[] };

export function toTree(blocks: Block[], skipLeadingParagraph = false): Node[] {
  const out: Node[] = [];
  let i = skipLeadingParagraph && blocks[0]?.type === "p" ? 1 : 0;

  function list(level: number): Node {
    const items: { text: string; children: Node[] }[] = [];
    while (i < blocks.length && blocks[i].type === "li" && blocks[i].level >= level) {
      if (blocks[i].level === level) {
        const item = { text: blocks[i].text, children: [] as Node[] };
        i++;
        if (i < blocks.length && blocks[i].type === "li" && blocks[i].level > level) item.children.push(list(level + 1));
        items.push(item);
      } else {
        // A bullet that jumps a level with no parent: treat it as a sibling at this level.
        items.push({ text: blocks[i].text, children: [] });
        i++;
      }
    }
    return { kind: "list", items };
  }

  while (i < blocks.length) {
    const b = blocks[i];
    if (b.type === "li") out.push(list(b.level));
    else if (b.type === "p") {
      out.push({ kind: "p", text: b.text });
      i++;
    } else {
      out.push({ kind: "heading", depth: Number(b.type[1]) as 2 | 3 | 4, text: b.text });
      i++;
    }
  }
  return out;
}

/** Splits text on `code` spans, so the renderer can set them in a mono face. */
export function inlineParts(text: string): { code: boolean; text: string }[] {
  return text
    .split(/(`[^`]+`)/g)
    .filter((s) => s !== "")
    .map((s) => (s.startsWith("`") && s.endsWith("`") && s.length > 1 ? { code: true, text: s.slice(1, -1) } : { code: false, text: s }));
}
