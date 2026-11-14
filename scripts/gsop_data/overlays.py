"""B6: equirectangular score overlays per target, a shared legend, and sidecar JSON.

Nearest-neighbour lookup from the 6 km EPSG:6933 tile grid. Nothing is interpolated or recomputed.
"""
import io

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer

from .fmt import make_meta, num, write_bytes, write_json
from .grid import Grid

TARGETS = ["connecting_ridge_c1", "shackleton_rim", "jezero"]
BODY = {"connecting_ridge_c1": "moon", "shackleton_rim": "moon", "jezero": "mars"}
STEP_DEG = 0.1
STOPS = [(0.0, "#440154"), (0.25, "#3b528b"), (0.5, "#21908c"), (0.75, "#5dc863"), (1.0, "#fde725")]
SCALE_NAME = "viridis-like, 5 stops, linear"

OVERLAY_LIMITS = [
    "Colours show the base profile only, one score per tile of the v1 equal-area grid.",
    "Transparent means v1 has no score there (water, gated out, or missing data). It does not mean a low score.",
    "Pixels are copied from the nearest tile; nothing is smoothed or interpolated.",
    "The score compares Earth terrain with one lunar or Martian target. It says nothing about gravity, air, dust or radiation.",
    "The ranking is not checked against independent data, and v1 failed its negative controls.",
]


def hex_rgb(h):
    return tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))


def palette():
    pos = np.array([s[0] for s in STOPS])
    cols = np.array([hex_rgb(s[1]) for s in STOPS], dtype=float)
    out = [0, 0, 0]  # index 0 is transparent
    for i in range(1, 256):
        t = (i - 1) / 254.0
        out += [int(round(np.interp(t, pos, cols[:, c]))) for c in range(3)]
    return out


def png_bytes(img, **kw):
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False, compress_level=9, **kw)
    return buf.getvalue()


def build(ctx):
    v1 = ctx.v1
    grid = Grid(v1.json("data/processed/grid.json"))
    run_dir = "results/{body}/{t}__base"
    tables = {}
    lat_min, lat_max = 90.0, -90.0
    for t in TARGETS:
        p = run_dir.format(body=BODY[t], t=t) + "/base_scores.parquet"
        tb = v1.table(p, columns=["tile_id", "score"])
        tid = tb.column("tile_id").to_numpy()
        sc = tb.column("score").to_numpy()
        tables[t] = (p, tid, sc)
        lon, lat = grid.lonlat(tid)
        lat_min, lat_max = min(lat_min, float(lat.min())), max(lat_max, float(lat.max()))
    south = np.floor(lat_min / STEP_DEG) * STEP_DEG
    north = np.ceil(lat_max / STEP_DEG) * STEP_DEG
    west, east = -180.0, 180.0
    width = int(round((east - west) / STEP_DEG))
    height = int(round((north - south) / STEP_DEG))
    lons = west + (np.arange(width) + 0.5) * STEP_DEG
    lats = north - (np.arange(height) + 0.5) * STEP_DEG
    LON, LAT = np.meshgrid(lons, lats)
    fwd = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
    X, Y = fwd.transform(LON.ravel(), LAT.ravel())
    ix = np.floor((X - grid.x0) / grid.cell).astype(np.int64)
    iy = np.floor((grid.y_top - Y) / grid.cell).astype(np.int64)
    inside = (ix >= 0) & (ix < grid.ncols) & (iy >= 0) & (iy < grid.nrows)
    flat = np.where(inside, iy * grid.ncols + ix, -1)
    pal = palette()
    for t in TARGETS:
        p, tid, sc = tables[t]
        order = np.argsort(tid, kind="stable")
        tid_s, sc_s = tid[order], sc[order]
        pos = np.searchsorted(tid_s, flat)
        pos = np.clip(pos, 0, len(tid_s) - 1)
        hit = (flat >= 0) & (tid_s[pos] == flat)
        val = np.where(hit, sc_s[pos], np.nan)
        idx = np.zeros(val.shape, dtype=np.uint8)
        ok = ~np.isnan(val)
        idx[ok] = (1 + np.rint(np.clip(val[ok], 0, 100) / 100.0 * 254)).astype(np.uint8)
        img = Image.fromarray(idx.reshape(height, width), mode="P")
        img.putpalette(pal)
        write_bytes(ctx.path(f"public/data/overlays/{t}.png"), png_bytes(img, transparency=0))
        summ = v1.json(run_dir.format(body=BODY[t], t=t) + "/summary.json")
        bs = summ["base_score_summary"]
        sources = [v1.src(p), v1.src(run_dir.format(body=BODY[t], t=t) + "/summary.json"), v1.src("data/processed/grid.json")]
        meta = make_meta(
            f"public/data/overlays/{t}.json",
            "Sidecar for the score overlay of one target, base profile.",
            OVERLAY_LIMITS,
            sources,
        )
        side = {
            "meta": meta,
            "target": t,
            "body": BODY[t],
            "profile": "base",
            "confidence": summ["confidence"],
            "image": f"{t}.png",
            "legend": "legend.json",
            "crs": "EPSG:4326",
            "bounds": {"west": num(west, 1), "south": num(south, 1), "east": num(east, 1), "north": num(north, 1)},
            "width": width,
            "height": height,
            "pixel_deg": STEP_DEG,
            "no_data": "transparent",
            "resampling": "nearest neighbour from the v1 equal-area tile grid, no interpolation",
            "value_range": {"min": 0, "max": 100},
            "colour_scale": SCALE_NAME,
            "n_scored_tiles": int(len(tid)),
            "observed_min": num(bs["min"], 4),
            "observed_median": num(bs["median"], 4),
            "observed_max": num(bs["max"], 4),
        }
        write_json(ctx.path(f"public/data/overlays/{t}.json"), side)
    # legend
    lw, lh = 512, 64
    bar = Image.new("RGB", (lw, lh), (255, 255, 255))
    d = ImageDraw.Draw(bar)
    for x in range(lw):
        t = x / (lw - 1)
        i = 1 + int(round(t * 254))
        d.line([(x, 8), (x, 36)], fill=tuple(pal[3 * i : 3 * i + 3]))
    font = ImageFont.load_default(size=14)
    for frac in (0.0, 0.5, 1.0):
        x = int(round(frac * (lw - 1)))
        d.line([(x, 36), (x, 42)], fill=(0, 0, 0))
        label = str(int(round(frac * 100)))
        w = d.textlength(label, font=font)
        d.text((min(max(x - w / 2, 0), lw - w), 44), label, fill=(0, 0, 0), font=font)
    write_bytes(ctx.path("public/data/overlays/legend.png"), png_bytes(bar))
    leg_meta = make_meta(
        "public/data/overlays/legend.json",
        "Shared colour scale for all score overlays.",
        OVERLAY_LIMITS,
        [v1.src("site_data/README_site_data.md")],
    )
    legend = {
        "meta": leg_meta,
        "image": "legend.png",
        "colour_scale": SCALE_NAME,
        "value_range": {"min": 0, "max": 100},
        "stops": [{"at": num(s[0], 2), "hex": s[1]} for s in STOPS],
        "no_data": "transparent",
        "no_data_means": "no v1 score for that tile",
    }
    write_json(ctx.path("public/data/overlays/legend.json"), legend)
    ctx.log(f"overlays: {len(TARGETS)} targets, {width}x{height}")
