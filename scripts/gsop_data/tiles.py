"""B7: top tiles per view, read from v1's stored Monte Carlo summary. No score is computed here."""
import csv
import io

import numpy as np

from .fmt import NOT_IN_V1, make_meta, num, write_json
from .grid import haversine_km

TOP_N = 100
VIEWS = (
    [("moon", t, p) for t in ("connecting_ridge_c1", "shackleton_rim") for p in ("base", "landing_mobility", "power_night")]
    + [("mars", "jezero", p) for p in ("base", "ice_resources", "landing_mobility", "power_night")]
)
FAMILY = {"moon": "illumination", "mars": "sunlight"}

TILES_LIMITS = [
    "Each score compares one Earth tile with one lunar or Martian target. It is not a measure of how well that place would work as a base or landing site.",
    "The Moon score is effectively terrain only. The lighting family adds nothing to the Moon ranking.",
    "Mars is a low-confidence secondary result with four families only: sunlight, slope, relief and air density.",
    "Scores say nothing about gravity, air pressure, dust, radiation or regolith. See the ledger.",
    "Only tiles that passed the land-cover and data gates have a score.",
    "Tiles listed here are candidates not in our reference list. They are unreviewed.",
    "v1 failed its negative controls, and the ranking is not checked against independent data.",
    "Slope, roughness and relief family scores per tile are not in v1 outputs, so only the lighting family is shown.",
]


def india_flags(v1, body, target, profile):
    p = f"site_data/candidates_{body}_{target}__{profile}.csv"
    rows = csv.DictReader(io.StringIO(v1.text(p)))
    return {int(r["tile_id"]): r["in_india_box"] == "True" for r in rows}, v1.src(p)


def build(ctx):
    v1 = ctx.v1
    sites = ctx.sites
    s_lat = np.array([s["lat"] for s in sites])
    s_lon = np.array([s["lon"] for s in sites])
    s_id = [s["id"] for s in sites]
    views = {}
    sources = []
    for body, target, profile in sorted(VIEWS, key=lambda v: f"{v[1]}__{v[2]}"):
        d = f"results/{body}/{target}__{profile}"
        mc = v1.table(d + "/mc_summary.parquet").to_pandas()
        bs = v1.table(d + "/base_scores.parquet").to_pandas().set_index("tile_id")
        summ = v1.json(d + "/summary.json")
        mc = mc.sort_values(["robust", "mc_median", "tile_id"], ascending=[False, False, True], kind="mergesort").head(TOP_N)
        india, india_src = india_flags(v1, body, target, profile)
        if len(s_lat):
            dist = np.vstack([haversine_km(la, lo, s_lat, s_lon) for la, lo in zip(mc.lat.values, mc.lon.values)])
            nearest = dist.argmin(axis=1)
        tiles = []
        for i, r in enumerate(mc.itertuples(index=False)):
            t = {
                "tile_id": int(r.tile_id),
                "lat": num(r.lat, 4),
                "lon": num(r.lon, 4),
                "score": num(r.score_base, 4),
                "mc_median": num(r.mc_median, 4),
                "mc_p05": num(r.mc_p05, 4),
                "mc_p95": num(r.mc_p95, 4),
                "freq_top5": num(r.freq_top5, 4),
                "top5_in_90pct_runs": bool(r.robust),
                "illum_match": num(bs.loc[int(r.tile_id), "illum_match"], 4),
                "in_india": india.get(int(r.tile_id), NOT_IN_V1),
            }
            if len(s_lat):
                t["nearest_reference_site"] = s_id[int(nearest[i])]
                t["km_to_nearest_reference_site"] = num(dist[i, nearest[i]], 1)
            tiles.append(t)
        srcs = [v1.src(d + "/mc_summary.parquet"), v1.src(d + "/base_scores.parquet"), v1.src(d + "/summary.json"), india_src]
        sources += srcs
        views[f"{target}__{profile}"] = {
            "target": target,
            "profile": profile,
            "body": body,
            "confidence": summ["confidence"],
            "illum_match_family": FAMILY[body],
            "n_gated_tiles": int(summ["gates"]["n_passed"]),
            "n_top5_in_90pct_runs": int(summ["n_robust"]),
            "source_file": srcs[0]["source_file"],
            "sha256": srcs[0]["sha256"],
            "tiles": tiles,
        }
    seen, uniq = set(), []
    for s in sources:
        if s["source_file"] not in seen:
            seen.add(s["source_file"])
            uniq.append(s)
    meta = make_meta(
        "public/data/tiles_top.json",
        "Top tiles per view from v1's stored Monte Carlo summary. Candidates not in our reference list, unreviewed.",
        TILES_LIMITS,
        uniq,
        order="tiles with the top-5%-in-90%-of-runs flag first, then by Monte Carlo median score, then by tile id",
        in_india_note="inside the Natural Earth India outline used by v1; not an official map",
        tile_size_note="each tile is one cell of the v1 equal-area grid",
    )
    write_json(ctx.path("public/data/tiles_top.json"), {"meta": meta, "views": views})
    ctx.log(f"tiles_top: {len(views)} views x {TOP_N}")
