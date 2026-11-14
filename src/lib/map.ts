// Pure helpers for the Honest Map (issue C2). No file access here, so the client component can import it.
export type Bounds = { west: number; south: number; east: number; north: number };
export type ItemKind = "site" | "candidate" | "control" | "region" | "tile";

export type MapItem = {
  kind: ItemKind;
  id: string;
  label: string;
  lat: number;
  lon: number;
  latText: string; // from claims.csv
  lonText: string;
  details: [string, string][]; // label and value, values already formatted from claims.csv
  href?: string;
  failed?: boolean; // control that scored above the pre-registered maximum
  flagged?: boolean;
  bbox?: Bounds;
};

export type MapTarget = {
  target: string;
  name: string;
  body: "Moon" | "Mars";
  confidence: string;
  image: string;
  bounds: Bounds;
  width: number;
  height: number;
  limits: string[];
  items: MapItem[];
};

export type Toggles = Record<ItemKind, boolean>;
export const DEFAULT_TOGGLES: Toggles = { site: true, candidate: false, control: true, region: true, tile: false };

export const KIND_ORDER: ItemKind[] = ["control", "site", "candidate", "region", "tile"];
export const KIND_LABEL: Record<ItemKind, string> = {
  site: "Reference site",
  candidate: "Candidate",
  control: "Negative control",
  region: "Region",
  tile: "Top tile",
};

/** Position of a point inside an equirectangular image, as percentages from the top left. */
export function project(lat: number, lon: number, b: Bounds): { x: number; y: number } {
  return { x: ((lon - b.west) / (b.east - b.west)) * 100, y: ((b.north - lat) / (b.north - b.south)) * 100 };
}

export function visibleItems(items: MapItem[], t: Toggles): MapItem[] {
  return items.filter((i) => t[i.kind]).sort((a, b) => KIND_ORDER.indexOf(a.kind) - KIND_ORDER.indexOf(b.kind));
}

export function itemKey(i: MapItem): string {
  return `${i.kind}:${i.id}`;
}
