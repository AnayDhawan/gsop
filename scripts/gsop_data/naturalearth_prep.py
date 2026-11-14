#!/usr/bin/env python3
"""One-off: trim Natural Earth GeoJSON to the layers the region naming uses and write them under data/reference/naturalearth/.

Not part of make_data (it needs the raw downloads). Run by hand, then commit the output and the hashes in its README.

    python3 scripts/gsop_data/naturalearth_prep.py POLYS.geojson PLACES.geojson OUT_DIR

Natural Earth is public domain. Source: https://github.com/nvkelso/natural-earth-vector (release v5.1.2).
"""
import csv
import hashlib
import io
import json
import os
import sys

CLASSES = {"Desert", "Plateau", "Range/mtn"}
PLACE_CLASSES = {"Populated place", "Populated Place", "Admin-1 capital", "Admin-0 capital", "Admin-1 region capital", "Admin-0 region capital", "Admin-0 capital alt"}


def rnd(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 4), round(c[1], 4)]
    return [rnd(x) for x in c]


def main(polys_path, places_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    polys = json.load(open(polys_path, encoding="utf-8"))
    feats = []
    for f in polys["features"]:
        p = f["properties"]
        if p["FEATURECLA"] in CLASSES:
            feats.append({"type": "Feature", "properties": {"name": p["NAME"], "featurecla": p["FEATURECLA"]}, "geometry": {"type": f["geometry"]["type"], "coordinates": rnd(f["geometry"]["coordinates"])}})
    feats.sort(key=lambda f: (f["properties"]["featurecla"], f["properties"]["name"]))
    out = json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":"), sort_keys=True, ensure_ascii=False) + "\n"
    open(os.path.join(out_dir, "regions_desert_plateau_range.geojson"), "w", encoding="utf-8", newline="").write(out)
    places = json.load(open(places_path, encoding="utf-8"))
    rows = []
    for f in places["features"]:
        p = f["properties"]
        if p["featurecla"] in PLACE_CLASSES:
            lon, lat = f["geometry"]["coordinates"][:2]
            rows.append((p["name"], p.get("adm0name") or "", f"{lat:.4f}", f"{lon:.4f}"))
    rows.sort(key=lambda r: (r[0], r[2], r[3]))
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["name", "country", "lat", "lon"])
    w.writerows(rows)
    open(os.path.join(out_dir, "populated_places.csv"), "w", encoding="utf-8", newline="").write(buf.getvalue())
    for p in (polys_path, places_path):
        print(hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p))
    print(len(feats), "region features,", len(rows), "places")


if __name__ == "__main__":
    main(*sys.argv[1:4])
