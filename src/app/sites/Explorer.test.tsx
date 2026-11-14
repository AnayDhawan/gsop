import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import Explorer from "./Explorer";
import type { ExplorerRow } from "@/lib/explorer";

vi.mock("next/link", () => ({ default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a> }));

const V = "shackleton_rim__base";
const J = "jezero__base";
const rows: ExplorerRow[] = [
  { id: "askja-moon", slug: "askja", name: "Askja caldera", body: "Moon", list: "known", country: "Iceland", v1_used: true, cells: { [V]: { status: "scored", score: "20.0", percentile: "92.0", flagged: false } }, pct: { [V]: 92 } },
  { id: "lonar-moon", slug: "lonar", name: "Lonar crater", body: "Moon", list: "known", country: "India", v1_used: null, cells: { [V]: { status: "gated_out", reason: "vegetated" } }, pct: {} },
  { id: "dallol-mars", slug: "dallol", name: "Dallol", body: "Mars", list: "candidate", country: "Ethiopia", v1_used: false, cells: { [J]: { status: "scored", score: "30.0", percentile: "50.0", flagged: true } }, pct: { [J]: 50 } },
];
const views = { Moon: [V], Mars: [J] };

describe("Explorer", () => {
  it("lists Moon sites first and links each to its page", () => {
    render(<Explorer rows={rows} views={views} />);
    const link = screen.getByRole("link", { name: "Askja caldera" });
    expect(link).toHaveAttribute("href", "/sites/askja");
    expect(screen.queryByText("Dallol")).not.toBeInTheDocument();
  });

  it("switches body and shows the stored numbers", () => {
    render(<Explorer rows={rows} views={views} />);
    fireEvent.click(screen.getByLabelText("Mars"));
    const row = screen.getByRole("link", { name: "Dallol" }).closest("tr")!;
    expect(within(row).getByText("50.0")).toBeInTheDocument();
    expect(within(row).getByText("Flagged")).toBeInTheDocument();
  });

  it("shows why a site has no score and filters it", () => {
    render(<Explorer rows={rows} views={views} />);
    expect(screen.getByText("vegetated")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Result"), { target: { value: "scored" } });
    expect(screen.queryByText("Lonar crater")).not.toBeInTheDocument();
  });

  it("says so when nothing matches", () => {
    render(<Explorer rows={rows} views={views} />);
    fireEvent.change(screen.getByLabelText("Search name or country"), { target: { value: "zzz" } });
    expect(screen.getByText("No sites match these filters.")).toBeInTheDocument();
  });
});
