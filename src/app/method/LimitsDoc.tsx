import { inlineParts, toTree, type Block, type Node } from "@/lib/mdblocks";

function Inline({ text }: { text: string }) {
  return (
    <>
      {inlineParts(text).map((p, i) =>
        p.code ? (
          <code key={i} className="gsop-mono text-[0.9em]">
            {p.text}
          </code>
        ) : (
          <span key={i}>{p.text}</span>
        ),
      )}
    </>
  );
}

function Tree({ nodes }: { nodes: Node[] }) {
  return (
    <>
      {nodes.map((n, i) => {
        if (n.kind === "heading") {
          // The page already has its own h2 for the section, so the document's headings start at h3.
          const H = (n.depth === 2 ? "h3" : "h4") as "h3" | "h4";
          return (
            <H key={i} className={n.depth === 2 ? "mt-4 text-lg" : "gsop-label mt-3"}>
              <Inline text={n.text} />
            </H>
          );
        }
        if (n.kind === "p") return <p key={i}><Inline text={n.text} /></p>;
        return (
          <ul key={i} className="list-disc space-y-2 pl-6">
            {n.items.map((it, j) => (
              <li key={j}>
                <Inline text={it.text} />
                {it.children.length > 0 && <div className="mt-2"><Tree nodes={it.children} /></div>}
              </li>
            ))}
          </ul>
        );
      })}
    </>
  );
}

/** A limits document stored in v2.json. Its numbers each have a claims.csv row that cites the document. */
export default function LimitsDoc({ blocks, skipLeadingParagraph = true }: { blocks: Block[]; skipLeadingParagraph?: boolean }) {
  return (
    <div className="space-y-3 text-sm">
      <Tree nodes={toTree(blocks, skipLeadingParagraph)} />
    </div>
  );
}
