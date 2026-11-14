"""B8: look up v1's stored score at each reference site. Descriptive lookup, not a test.

Site to tile rule is v1's own: the best-scoring tile that passed the gates within the site match radius.
Percentile is v1's own: 100 * (tiles with a lower score) / (tiles that passed the gates in that view).
"""
import numpy as np

from .fmt import NOT_IN_V1, make_meta, num, write_json
from .grid import Grid, haversine_km
from .tiles import VIEWS

# Gate codes in gates__*.parquet. Read by matching tile counts to rejected_by_reason in each summary.json.
CODE = {0: "passed", 1: "open water or ice", 2: "vegetated", 3: "built or cropland", 5: "missing data"}
LAND_COVER_FAIL = (1, 2, 3)

LOOKUP_LIMITS = [
    "This is a lookup of scores v1 already stored. It is descriptive and is not a test of the method.",
    "A site is matched to the best-scoring tile that passed the gates within the match radius. A different radius would give different numbers.",
    "Tiles are large compared with most sites, so a score describes the surrounding area, not the site itself.",
    "Scores exist only for tiles that passed the land-cover and data gates. A gated-out or unscored site has no score, which says nothing about how good an analog it is.",
    "Percentile is the share of scored tiles in that view with a lower score.",
    "The Moon score is effectively terrain only. Mars is a low-confidence secondary result.",
    "v1 failed its negative controls, so a high percentile here does not show that a site is a good analog.",
    "The ranking is not checked against independent data. Gravity, air, dust and radiation are not scored.",
    "Sites are compared with views of their own body only.",
]


def run_for_view(body, target, profile):
    return f"results/{body}/{target}__{profile}"


def build(ctx):
    v1 = ctx.v1
    grid = Grid(v1.json("data/processed/grid.json"))
    run_yaml = v1.yaml("config/run.yaml")
    radius = float(run_yaml["site_match_radius_km"])
    reach_y = int(np.ceil(radius * 1000 / grid.cell)) + 1
    sites = ctx.sites
    ncell = grid.nrows * grid.ncols
    gate_arrays = {}
    for body, profile in sorted({(b, p) for b, _, p in VIEWS}):
        g = v1.table(f"results/{body}/gates__{profile}.parquet").to_pandas()
        arr = np.full(ncell, -1, dtype=np.int8)
        arr[g.tile_id.values] = g.code.values.astype(np.int8)
        gate_arrays[(body, profile)] = arr
    # per-site candidate tiles within radius (independent of view)
    near = []
    for s in sites:
        ix0, iy0 = grid.cell_of(s["lon"], s["lat"])
        tiles = []
        # East-west ground distance per cell shrinks by cos(latitude) on this equal-area grid, so the window widens with latitude.
        reach_x = int(np.ceil(radius * 1000 / (grid.cell * max(np.cos(np.radians(s["lat"])), 0.02)))) + 1
        for dy in range(-reach_y, reach_y + 1):
            for dx in range(-reach_x, reach_x + 1):
                iy, ix = iy0 + dy, ix0 + dx
                if 0 <= iy < grid.nrows:
                    tiles.append(iy * grid.ncols + (ix % grid.ncols))
        tiles = np.array(sorted(set(tiles)), dtype=np.int64)
        lon, lat = grid.lonlat(tiles)
        km = haversine_km(s["lat"], s["lon"], lat, lon)
        keep = km <= radius
        near.append((tiles[keep], km[keep]))
    entries = {s["id"]: {} for s in sites}
    sources = [v1.src("config/run.yaml"), v1.src("data/processed/grid.json")]
    view_sources = {}
    summaries = {}
    for body, target, profile in sorted(VIEWS, key=lambda v: f"{v[1]}__{v[2]}"):
        view = f"{target}__{profile}"
        d = run_for_view(body, target, profile)
        bs = v1.table(d + "/base_scores.parquet", columns=["tile_id", "score"])
        tid = bs.column("tile_id").to_numpy()
        sc = bs.column("score").to_numpy()
        order = np.argsort(tid)
        tid_s, sc_s = tid[order], sc[order]
        sorted_scores = np.sort(sc)
        n = len(sc)
        flagged = set(v1.table(d + "/mc_summary.parquet", columns=["tile_id", "robust"]).to_pandas().query("robust").tile_id.tolist())
        gates = gate_arrays[(body, profile)]
        view_sources[view] = [v1.src(d + "/base_scores.parquet"), v1.src(d + "/mc_summary.parquet"), v1.src(f"results/{body}/gates__{profile}.parquet")]
        sources += view_sources[view]
        pcts = {"true": [], "false": [], "unknown": []}
        groups = {"true": 0, "false": 0, "unknown": 0}
        for s, (tiles, km) in zip(sites, near):
            if s["body"].lower() != body:
                continue
            groups[s["v1_used"]] += 1
            codes = gates[tiles] if len(tiles) else np.array([], dtype=np.int8)
            land = codes >= 0
            e = {"source_file": view_sources[view][0]["source_file"], "sha256": view_sources[view][0]["sha256"]}
            if not land.any():
                e.update(status="no_land_tile", reason="no land tile within the match radius")
            else:
                passed = codes == 0
                if passed.any():
                    t_p, km_p = tiles[passed], km[passed]
                    pos = np.searchsorted(tid_s, t_p)
                    scores = sc_s[pos]
                    best = sorted(range(len(t_p)), key=lambda i: (-float(scores[i]), float(km_p[i]), int(t_p[i])))[0]
                    score = float(scores[best])
                    pct = 100.0 * int(np.searchsorted(sorted_scores, np.float32(score), side="left")) / n
                    e.update(
                        status="scored",
                        tile_id=int(t_p[best]),
                        km_to_tile=num(km_p[best], 1),
                        score=num(score, 4),
                        percentile=num(pct, 4),
                        top5_in_90pct_runs=int(t_p[best]) in flagged,
                    )
                    pcts[s["v1_used"]].append(pct)
                else:
                    c = codes[land]
                    if all(int(x) in LAND_COVER_FAIL for x in c):
                        vals, cnt = np.unique(c, return_counts=True)
                        top = int(vals[np.argmax(cnt)])
                        e.update(status="gated_out", reason=f"every tile in range failed a land-cover gate; most common: {CODE[top]}")
                    else:
                        e.update(status="missing_data", reason="no tile in range passed; some tiles lack data")
            entries[s["id"]][view] = e
        summ = {}
        for k, key in (("true", "v1_used_true"), ("false", "v1_used_false")):
            p = pcts[k]
            summ[key] = {
                "n_group": groups[k],
                "n": len(p),
                "median_percentile": num(float(np.median(p)), 4) if p else NOT_IN_V1,
            }
        summ["v1_used_unknown"] = {"n_group": groups["unknown"], "n": len(pcts["unknown"])}
        summ["body"] = body
        summ["source_file"] = view_sources[view][0]["source_file"]
        summ["sha256"] = view_sources[view][0]["sha256"]
        summaries[view] = summ
    seen, uniq = set(), []
    for s in sources:
        if s["source_file"] not in seen:
            seen.add(s["source_file"])
            uniq.append(s)
    radius_txt = str(int(radius))
    facts = [
        {
            "claim": "lookup.match_radius_km",
            "number": radius_txt,
            "source_file": sources[0]["source_file"],
            "sha256": sources[0]["sha256"],
        }
    ]
    limits = LOOKUP_LIMITS + [f"Match radius: {radius_txt} km, the radius v1 used."]
    meta = make_meta(
        "public/data/site_lookup.json",
        "Descriptive lookup of stored v1 scores at reference sites. This is not a test.",
        limits,
        uniq,
        facts=facts,
        gate_codes=CODE,
        summary_note="n is the number of sites with a percentile; n_group is the number of sites in that group for the view's body. Unknown flags are counted separately.",
    )
    out = {"meta": meta, "sites": entries, "summary_by_view": summaries}
    write_json(ctx.path("public/data/site_lookup.json"), out)
    ctx.lookup = out
    n_scored = sum(1 for s in entries.values() for e in s.values() if e["status"] == "scored")
    n_all = sum(len(s) for s in entries.values())
    ctx.log(f"site_lookup: {n_all} entries, {n_scored} scored")
