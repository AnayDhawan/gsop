import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import Page from "./page";
import { e32Sentence } from "@/lib/data";

vi.mock("next/link", () => ({ default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a> }));

describe("methods and limits page", () => {
  it("states the failures and the limits up front", () => {
    const { container } = render(<Page />);
    const text = container.textContent ?? "";
    expect(text).toMatch(/failed its own pre-registered negative-control test/);
    expect(text).toMatch(/has not been checked against independent data/);
    expect(text).toMatch(/effectively terrain only/);
    expect(text).toMatch(/low-confidence secondary result/);
  });

  it("puts limits before the description of how the screening works", () => {
    render(<Page />);
    const limits = screen.getByRole("heading", { name: "Limits" });
    const works = screen.getByRole("heading", { name: "How the screening works" });
    expect(limits.compareDocumentPosition(works) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("prints the E32 sentence verbatim", () => {
    render(<Page />);
    expect(screen.getByText(e32Sentence())).toBeInTheDocument();
  });

  it("shows the v2 status and the thermal limits, and says what is not available yet", () => {
    render(<Page />);
    expect(screen.getByText("v2 run not completed")).toBeInTheDocument();
    expect(screen.getByText(/Reference thermal layers: where each one cannot match Earth/)).toBeInTheDocument();
    expect(screen.getByText(/Site evidence limits: not available yet/)).toBeInTheDocument();
    expect(screen.getByText(/Data resource table: not available yet/)).toBeInTheDocument();
  });

  it("uses sentence case in section headings", () => {
    render(<Page />);
    for (const h of screen.getAllByRole("heading", { level: 2 })) {
      const words = (h.textContent ?? "").split(" ");
      for (const w of words.slice(1)) expect(w, `heading "${h.textContent}"`).not.toMatch(/^[A-Z][a-z]+$/);
    }
  });

  it("has no banned words and no dashes used as punctuation", () => {
    const { container } = render(<Page />);
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/\b(validated|discovered|undiscovered|new sites)\b/i);
    expect(text).not.toMatch(/—/);
  });

  it("renders the limits document as nested lists with code spans", () => {
    const { container } = render(<Page />);
    const doc = within(container.querySelector("details")!.parentElement!).getAllByRole("list")[0];
    expect(doc).toBeInTheDocument();
    expect(container.querySelectorAll("details code").length).toBeGreaterThan(5);
  });
});
