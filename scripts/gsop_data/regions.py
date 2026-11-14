"""B10: regions from v1's flagged tiles. Clustering and geometry only; no score is computed.

Flagged tile = top 5% in at least 90% of Monte Carlo runs (v1's `robust` flag, stored in mc_summary.parquet).
Clusters join tiles that touch (8 neighbours) on the v1 grid, wrapping at the date line.
"""
import csv
import io
from collections import deque

import numpy as np

from .fmt import NOT_IN_V1, make_meta, num, sha256_file, write_json
from .grid import Grid, haversine_km
from .naming import NEAR_KM, PLACES_FILE, REGIONS_FILE, Namer

# Decision parameter set by this build, not read from v1. Registered as a fact whose source is this file.
MIN_TILES = 100
TOP_REGIONS = 10  # decided for B12: top 10 regions per target, ranked by median Monte Carlo score
REGION_TARGETS = [("moon", "connecting_ridge_c1"), ("moon", "shackleton_rim"), ("mars", "jezero")]

CAVEAT = (
    "Flagged by v1 on Earth terrain only. Not reviewed. Not checked against independent data. "
    "v1 failed its negative controls, so a flag here is a reason to look, not a finding."
)
CAVEAT_MARS = " Mars is a low-confidence secondary result with four families only."
REGIONS_LIMITS = [
    "Regions are groups of neighbouring tiles that v1 flagged on Earth terrain. They are candidates not in our reference list and none has been reviewed.",
    "A region is not a site. It says where v1's terrain score is high, not that the place is a good analog for lunar or Martian work.",
    "The Moon score is effectively terrain only. Gravity, air, dust and radiation are not scored.",
    "Regions within the drop distance of any reference site are left out, so the list is not a full map of high scores.",
    "Small groups are left out. The minimum size is a choice made in this build, not a v1 setting.",
    "Place names are labels from Natural Earth, which is generalised. The name is the desert, plateau or range the centre lies in or is near, otherwise the nearest populated place. It is not a claim about the ground.",
    "Only the highest-scoring regions are listed. Many more groups of flagged tiles exist.",
    "Regions appear only where v1 had terrain data and the tile passed the gates.",
    "India counts use the Natural Earth outline from v1, which is not an official map.",
]


def clusters(tile_ids, ncols):
    s = set(int(t) for t in tile_ids)
    seen = set()
    out = []
    for t in sorted(s):
        if t in seen:
            continue
        q = deque([t])
        seen.add(t)
        c = []
        while q:
            u = q.popleft()
            c.append(u)
            iy, ix = divmod(u, ncols)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    v = (iy + dy) * ncols + ((ix + dx) % ncols)
                    if v in s and v not in seen:
                        seen.add(v)
                        q.append(v)
        out.append(sorted(c))
    return out


def india_polys(geo):
    g = geo["features"][0]["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return [np.array(p[0], dtype=float) for p in polys]  # exterior rings; v1's file has no holes


def in_polys(lon, lat, polys):
    """Even-odd point-in-polygon test, vectorised over points, over the exterior rings."""
    inside = np.zeros(len(lon), dtype=bool)
    for ring in polys:
        x, y = ring[:, 0], ring[:, 1]
        res = np.zeros(len(lon), dtype=bool)
        for i in range(len(ring) - 1):
            x1, y1, x2, y2 = x[i], y[i], x[i + 1], y[i + 1]
            cond = (y1 > lat) != (y2 > lat)
            with np.errstate(divide="ignore", invalid="ignore"):
                xint = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            res ^= cond & (lon < xint)
        inside |= res
    return inside


def build(ctx):
    v1 = ctx.v1
    grid = Grid(v1.json("data/processed/grid.json"))
    run = v1.yaml("config/run.yaml")
    drop_km = float(run["discovery"]["min_distance_km"])
    cell_km2 = (grid.cell / 1000.0) ** 2
    polys = india_polys(v1.json("site_data/india_boundary_naturalearth_ind_10m.geojson"))
    # self-check of the India test against v1's own flags on its top-500 file
    chk = list(csv.DictReader(io.StringIO(v1.text("site_data/candidates_moon_shackleton_rim__base.csv"))))
    lon_c = np.array([float(r["lon"]) for r in chk])
    lat_c = np.array([float(r["lat"]) for r in chk])
    want = np.array([r["in_india_box"] == "True" for r in chk])
    got = in_polys(lon_c, lat_c, polys)
    mism = int((want != got).sum())
    assert mism <= 2, f"India point-in-polygon disagrees with v1 on {mism} tiles"
    s_lat = np.array([s["lat"] for s in ctx.ref_sites])
    s_lon = np.array([s["lon"] for s in ctx.ref_sites])
    s_id = [s["id"] for s in ctx.ref_sites]
    namer = Namer(ctx.repo)
    sources = [v1.src("config/run.yaml"), v1.src("data/processed/grid.json"), v1.src("site_data/india_boundary_naturalearth_ind_10m.geojson")]
    found = []
    stats = {}
    for body, target in REGION_TARGETS:
        view = f"{target}__base"
        d = f"results/{body}/{view}"
        mc = v1.table(d + "/mc_summary.parquet").to_pandas()
        summ = v1.json(d + "/summary.json")
        src_mc = v1.src(d + "/mc_summary.parquet")
        sources += [src_mc, v1.src(d + "/summary.json")]
        fl = mc[mc.robust]
        info = fl.set_index("tile_id")
        cl = clusters(fl.tile_id.values, grid.ncols)
        big = [c for c in cl if len(c) >= MIN_TILES]
        kept = []
        for c in big:
            sub = info.loc[c]
            dist = np.vstack([haversine_km(la, lo, s_lat, s_lon) for la, lo in zip(sub.lat.values, sub.lon.values)])
            col = dist.min(axis=0)
            j = int(col.argmin())
            km = float(col[j])
            if km <= drop_km:
                continue
            ix, iy = grid.ixiy(np.array(c))
            rel = ((ix - ix[0] + grid.ncols // 2) % grid.ncols) - grid.ncols // 2
            cx = ix[0] + rel.mean()
            cy = iy.mean()
            clon, clat = grid.lonlat(np.array([int(round(cy)) * grid.ncols + int(round(cx)) % grid.ncols]))
            clon, clat = float(clon[0]), float(clat[0])
            dl = ((sub.lon.values - clon + 180) % 360) - 180
            west, east = clon + float(dl.min()), clon + float(dl.max())
            wrap = lambda x: ((x + 180) % 360) - 180
            kept.append(
                {
                    "target": target,
                    "profile": "base",
                    "body": body,
                    "confidence": summ["confidence"],
                    "n_tiles": len(c),
                    "area_km2": num(len(c) * cell_km2, 0),
                    "centroid_lat": num(clat, 4),
                    "centroid_lon": num(clon, 4),
                    "bbox": {"south": num(sub.lat.min(), 4), "north": num(sub.lat.max(), 4), "west": num(wrap(west), 4), "east": num(wrap(east), 4)},
                    "median_score": num(np.median(sub.score_base.values), 4),
                    "median_mc_median": num(np.median(sub.mc_median.values), 4),
                    "km_to_nearest_reference_site": num(km, 1),
                    "nearest_reference_site": s_id[j],
                    "n_tiles_in_india": int(in_polys(sub.lon.values, sub.lat.values, polys).sum()),
                    "status": "Unreviewed",
                    "caveat": CAVEAT + (CAVEAT_MARS if body == "mars" else ""),
                    "source_file": src_mc["source_file"],
                    "sha256": src_mc["sha256"],
                    "_key": (-len(c), c[0]),
                }
            )
        kept.sort(key=lambda r: (-r["median_mc_median"], r["_key"]))
        top = kept[:TOP_REGIONS]
        for r in top:
            r["place"] = namer.name(r["centroid_lat"], r["centroid_lon"])
        stats[view] = {
            "n_flagged_tiles": len(fl),
            "n_clusters": len(cl),
            "n_clusters_min_size": len(big),
            "n_dropped_near_site": len(big) - len(kept),
            "n_regions_before_top": len(kept),
            "n_regions": len(top),
        }
        found += top
    width = max(2, len(str(len(found))))
    for i, r in enumerate(found, start=1):
        r["id"] = f"Region {i:0{width}d}"
        del r["_key"]
    me = "scripts/gsop_data/regions.py"
    me_sha = sha256_file(ctx.repo + "/" + me)
    nm = "scripts/gsop_data/naming.py"
    ne_regions = {"source_file": REGIONS_FILE, "sha256": sha256_file(namer.regions_path)}
    ne_places = {"source_file": PLACES_FILE, "sha256": sha256_file(namer.places_path)}
    sources += [ne_regions, ne_places]
    facts = [
        {"claim": "regions.min_tiles", "number": str(MIN_TILES), "source_file": me, "sha256": me_sha},
        {"claim": "regions.top_n", "number": str(TOP_REGIONS), "source_file": me, "sha256": me_sha},
        {"claim": "regions.near_km", "number": str(NEAR_KM), "source_file": nm, "sha256": sha256_file(ctx.repo + "/" + nm)},
        {"claim": "regions.drop_distance_km", "number": str(int(drop_km)), "source_file": sources[0]["source_file"], "sha256": sources[0]["sha256"]},
    ]
    limits = REGIONS_LIMITS + [
        f"Regions with fewer than {MIN_TILES} tiles are left out.",
        f"Each target lists its top {TOP_REGIONS} regions by median score.",
        f"A physical region counts as near when its outline is within {NEAR_KM} km of the centre.",
        f"Regions within {int(drop_km)} km of any reference site are left out.",
    ]
    uniq, seen = [], set()
    for s in sources:
        if s["source_file"] not in seen:
            seen.add(s["source_file"])
            uniq.append(s)
    meta = make_meta(
        "public/data/regions.json",
        "Groups of neighbouring tiles that v1 flagged on terrain. Candidates not in our reference list, unreviewed.",
        limits,
        uniq,
        facts=facts,
        cluster_rule="tiles carrying v1's stability flag, joined by neighbour adjacency on the v1 grid, wrapping at the date line",
        flag_source="robust column of mc_summary.parquet, base profile of each target",
        min_tiles=MIN_TILES,
        top_regions_per_target=TOP_REGIONS,
        rank_rule="median Monte Carlo score of the region's tiles, highest first",
        place_rule="desert, plateau or range containing the centre; else the nearest such region within the near distance; else the nearest populated place",
        drop_distance_km=int(drop_km),
        by_view=stats,
        tile_area_km2=num(cell_km2, 0),
    )
    write_json(ctx.path("public/data/regions.json"), {"meta": meta, "regions": found})
    ctx.regions = found
    ctx.log(f"regions: {len(found)} " + str({k: v["n_regions"] for k, v in stats.items()}))
