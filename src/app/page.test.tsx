import fs from "node:fs";
import path from "node:path";
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import Home from "./page";
import { e32Sentence } from "@/lib/data";

vi.mock("next/link", () => ({ default: ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) => <a href={href} className={className}>{children}</a> }));

describe("landing page", () => {
  const decisions = fs.readFileSync(path.join(process.cwd(), "docs/DECISIONS_SITE.md"), "utf-8");
  const locked = (label: string) => decisions.match(new RegExp(`^${label}: \\*\\*(.+?)\\*\\*`, "m"))![1];

  it("uses the headline and support line locked in docs/DECISIONS_SITE.md", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(locked("Headline"));
    expect(screen.getByText(locked("Support line"))).toBeInTheDocument();
  });

  it("puts the failures before any result and prints the E32 sentence verbatim", () => {
    render(<Home />);
    const failed = screen.getByRole("heading", { name: "What failed" });
    const india = screen.getByRole("heading", { name: "India focus" });
    expect(failed.compareDocumentPosition(india) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByText(e32Sentence())).toBeInTheDocument();
    expect(screen.getByText(/has not been checked against independent data/)).toBeInTheDocument();
  });

  it("links to the ledger, the map and the sites", () => {
    render(<Home />);
    for (const href of ["/ledger", "/map", "/sites"]) expect(document.querySelector(`a[href="${href}"]`), href).not.toBeNull();
  });

  it("uses none of the banned words", () => {
    const { container } = render(<Home />);
    expect(container.textContent).not.toMatch(/\b(validated|discovered|undiscovered|new sites)\b/i);
  });
});
