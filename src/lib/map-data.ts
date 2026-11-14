// Server side: build the Honest Map data. Every number printed is a string from claims.csv.
import { OVERLAY_TARGETS, claim, controlsFile, lookupFile, overlay, regionsFile, sitesFile, tilesFile } from "./data";
import { statusLabel } from "./format";
import type { MapItem, MapTarget } from "./map";
import { targetName } from "./names";
import type { Region } from "./types";

const regionKey = (r: Region) => r.id.replace(" ", "_");

function placeLabel(r: Region): string {
  const p = r.place;
  const km = claim(`regions.${regionKey(r)}.place_distance_km`);
  if (p.relation === "inside") return `inside ${p.name}`;
  if (p.relation === "near") return `near ${p.name}, about ${km} km`;
  return `nearest populated place: ${p.name}, about ${km} km`;
}

export function mapData(): { targets: MapTarget[]; controlMax: string } {
  const sites = sitesFile().sites;
  const lookup = lookupFile().sites;
  const tiles = tilesFile().views;
  const controls = controlsFile().controls;
  const regions = regionsFile().regions;
  const siteName = new Map(sites.map((s) => [s.id, s.name]));
  const targets: MapTarget[] = OVERLAY_TARGETS.map((t) => {
    const o = overlay(t);
    const body = o.body === "moon" ? "Moon" : "Mars";
    const view = `${t}__base`;
    const items: MapItem[] = [];

    for (const c of controls) {
      const r = c.runs[o.body];
      if (!r) continue;
      const scored = r.status === "scored";
      const failed = scored; // the only scored controls are the ones that scored far above the maximum
      items.push({
        kind: "control",
        id: c.id,
        label: c.label,
        lat: c.lat,
        lon: c.lon,
        latText: claim(`controls.${c.id}.lat`),
        lonText: claim(`controls.${c.id}.lon`),
        failed,
        details: [
          ["Result", scored ? `Percentile ${claim(`controls.${c.id}.${o.body}.rank_pct`)}` : `${statusLabel(r.status)}: ${r.reason ?? "no reason stored"}`],
          ["Pre-registered maximum", `Percentile ${claim(`metrics.${o.body}.criterion.negative_control_rank_pct_max`)}`],
          ["Verdict", scored ? "Failed. A place that should score low scored high." : "No score, so it passes nothing."],
          ["Coordinates", c.coordinates_confirmed ? "Confirmed from a primary source" : "Not confirmed from a primary source"],
        ],
      });
    }

    for (const s of sites.filter((x) => x.body === body)) {
      const e = lookup[s.id]?.[view];
      const scored = e?.status === "scored";
      items.push({
        kind: s.list === "known" ? "site" : "candidate",
        id: s.id,
        label: s.name,
        lat: s.lat,
        lon: s.lon,
        latText: claim(`sites.${s.id}.lat`),
        lonText: claim(`sites.${s.id}.lon`),
        href: `/sites/${s.slug}`,
        flagged: scored ? e.top5_in_90pct_runs : undefined,
        details: [
          ["Entry type", s.list === "known" ? "Reference site" : "Candidate, not in our reference list"],
          ["Country", s.country ?? "not provided"],
          ["Percentile", scored ? claim(`lookup.${s.id}.${view}.percentile`) : e ? `${statusLabel(e.status)}: ${e.reason}` : "not in v1 outputs"],
          ["Score", scored ? claim(`lookup.${s.id}.${view}.score`) : "not in v1 outputs"],
          ["v1 used this site", s.v1_used === true ? "Yes" : s.v1_used === false ? "No" : "Unknown"],
        ],
      });
    }

    for (const r of regions.filter((x) => x.target === t)) {
      const k = regionKey(r);
      items.push({
        kind: "region",
        id: r.id,
        label: r.id,
        lat: r.centroid_lat,
        lon: r.centroid_lon,
        latText: claim(`regions.${k}.centroid_lat`),
        lonText: claim(`regions.${k}.centroid_lon`),
        bbox: r.bbox,
        details: [
          ["Place", placeLabel(r)],
          ["Status", r.status],
          ["Tiles", claim(`regions.${k}.n_tiles`)],
          ["Area (km2)", claim(`regions.${k}.area_km2`)],
          ["Median score", claim(`regions.${k}.median_score`)],
          ["Tiles inside the India outline", claim(`regions.${k}.n_tiles_in_india`)],
          ["Caveat", r.caveat],
        ],
      });
    }

    for (const x of tiles[view].tiles) {
      const k = `tiles.${view}.${x.tile_id}`;
      items.push({
        kind: "tile",
        id: String(x.tile_id),
        label: `Tile ${x.tile_id}`,
        lat: x.lat,
        lon: x.lon,
        latText: claim(`${k}.lat`),
        lonText: claim(`${k}.lon`),
        flagged: x.top5_in_90pct_runs,
        details: [
          ["Score", claim(`${k}.score`)],
          ["Monte Carlo range", `${claim(`${k}.mc_p05`)} to ${claim(`${k}.mc_p95`)} (median ${claim(`${k}.mc_median`)})`],
          ["Flagged in the top group", x.top5_in_90pct_runs ? "Yes" : "No"],
          ["Nearest reference site", x.nearest_reference_site ? `${siteName.get(x.nearest_reference_site) ?? x.nearest_reference_site}, about ${claim(`${k}.km_to_nearest_reference_site`)} km` : "not in v1 outputs"],
          ["Status", "Candidate not in our reference list, unreviewed"],
        ],
      });
    }

    return {
      target: t,
      name: targetName(t),
      body,
      confidence: o.confidence,
      image: `/data/overlays/${o.image}`,
      bounds: o.bounds,
      width: o.width,
      height: o.height,
      limits: o.meta.limits,
      items,
    };
  });
  return { targets, controlMax: claim("metrics.moon.criterion.negative_control_rank_pct_max") };
}
