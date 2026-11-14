import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import MeasuredEvidence from "./MeasuredEvidence";
import type { Evidence } from "@/lib/evidence";

vi.mock("next/image", () => ({ default: ({ alt }: { alt: string }) => <span role="img" aria-label={alt} /> }));

const ev = (over: Partial<Evidence> = {}): Evidence => ({
  approximateOnly: false,
  rows: [
    { dataset: "cop_dem", variable: "elevation", stat: "mean", radius: "10", value: "1100", units: "m", product: "COP 2024_1", note: "" },
    { dataset: "s1", variable: "vv", stat: "median", radius: "10", value: "not measured", units: "dB", product: "S1", note: "no_images" },
  ],
  ...over,
});
const radius = (r: string) => `<${r}>`;

describe("MeasuredEvidence", () => {
  it("renders nothing when the evidence file is absent, so the page is unchanged", () => {
    const { container } = render(<MeasuredEvidence evidence={null} chip={null} radiusClaim={radius} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows value, radius, product and version, and says not measured for a null", () => {
    render(<MeasuredEvidence evidence={ev()} chip={null} radiusClaim={radius} />);
    expect(screen.getByText("1100 m")).toBeInTheDocument();
    expect(screen.getAllByText("<10>")).toHaveLength(2);
    expect(screen.getByText("COP 2024_1")).toBeInTheDocument();
    expect(screen.getByText("not measured")).toBeInTheDocument();
    expect(screen.getByText("no images")).toBeInTheDocument();
  });

  it("flags approximate coordinates", () => {
    render(<MeasuredEvidence evidence={ev({ approximateOnly: true })} chip={null} radiusClaim={radius} />);
    expect(screen.getByText(/coordinates for this site are approximate/)).toBeInTheDocument();
  });

  it("shows the imagery chip with its Copernicus credit", () => {
    render(<MeasuredEvidence evidence={ev()} chip={{ src: "/img/sites/a.jpg", credit: "Contains modified Copernicus Sentinel data" }} radiusClaim={radius} />);
    expect(screen.getByRole("img")).toBeInTheDocument();
    expect(screen.getByText("Contains modified Copernicus Sentinel data")).toBeInTheDocument();
  });

  it("says not measured when the file exists but the site has no rows", () => {
    render(<MeasuredEvidence evidence={{ approximateOnly: false, rows: [] }} chip={null} radiusClaim={radius} />);
    expect(screen.getByText("not measured")).toBeInTheDocument();
  });
});
