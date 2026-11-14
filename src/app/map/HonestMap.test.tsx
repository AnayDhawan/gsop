import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import HonestMap from "./HonestMap";
import type { MapItem, MapTarget } from "@/lib/map";

vi.mock("next/link", () => ({ default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a> }));
vi.mock("next/image", () => ({ default: ({ alt }: { alt: string }) => <span role="img" aria-label={alt} /> }));

const item = (kind: MapItem["kind"], id: string, label: string, extra: Partial<MapItem> = {}): MapItem => ({
  kind,
  id,
  label,
  lat: 10,
  lon: 20,
  latText: "10.00",
  lonText: "20.00",
  details: [["Percentile", "88.0"]],
  ...extra,
});

const base = { bounds: { west: -180, south: -55, east: 180, north: 83 }, width: 3600, height: 1383, confidence: "standard", limits: ["Limit one."], image: "/x.png" };
const targets: MapTarget[] = [
  {
    ...base,
    target: "shackleton_rim",
    name: "Shackleton rim",
    body: "Moon",
    items: [
      item("control", "namib", "Namib sand sea", { failed: true, details: [["Result", "Percentile 90.2"], ["Verdict", "Failed. A place that should score low scored high."]] }),
      item("site", "askja", "Askja caldera", { href: "/sites/askja" }),
      item("candidate", "cand", "Candidate place"),
      item("tile", "7", "Tile 7"),
    ],
  },
  { ...base, target: "jezero", name: "Jezero", body: "Mars", confidence: "low", items: [item("site", "dallol", "Dallol")] },
];

const view = () => render(<HonestMap targets={targets} sentence="The sentence." controlMax="25.0" />);

describe("HonestMap", () => {
  it("shows controls and reference sites by default, and hides candidates and tiles", () => {
    view();
    expect(screen.getByRole("button", { name: "Negative control: Namib sand sea" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reference site: Askja caldera" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Candidate place/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Tile 7/ })).not.toBeInTheDocument();
  });

  it("turns layers on and off", () => {
    view();
    fireEvent.click(screen.getByLabelText(/Candidates/));
    expect(screen.getByRole("button", { name: /Candidate place/ })).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText(/Reference sites/));
    expect(screen.queryByRole("button", { name: /Askja caldera/ })).not.toBeInTheDocument();
  });

  it("shows the failed verdict for a selected control, in red", () => {
    view();
    fireEvent.click(screen.getByRole("button", { name: "Negative control: Namib sand sea" }));
    const verdict = screen.getByText("Failed. A place that should score low scored high.");
    expect(verdict.className).toContain("text-control");
    expect(screen.getByText("Percentile 90.2")).toBeInTheDocument();
  });

  it("switches overlay and lists that body's items only", () => {
    view();
    fireEvent.click(screen.getByLabelText(/Jezero/));
    expect(screen.getByRole("button", { name: "Reference site: Dallol" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Askja/ })).not.toBeInTheDocument();
  });

  it("offers the same items as a table", () => {
    view();
    fireEvent.click(screen.getByRole("button", { name: "Table" }));
    const t = screen.getByRole("table");
    expect(within(t).getByRole("link", { name: "Askja caldera" })).toHaveAttribute("href", "/sites/askja");
    expect(within(t).getByText("Namib sand sea")).toBeInTheDocument();
  });
});
