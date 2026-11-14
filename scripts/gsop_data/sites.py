"""B2: validate the teammate's site CSV and write data/reference/sites.csv and sites_check.md.

Lookup and transformation only. Nothing here scores anything.
"""
import csv
import io
import math
import re
import zipfile

import yaml

ZIP_ROOT = "gsop_v1/"
SCHEMA = ["name", "body", "lat", "lon", "kind", "analog_of", "source_url_1", "source_url_2"]
OUT_COLUMNS = SCHEMA + ["v1_used"]

# Brief column -> column found in the teammate CSV. None means no such column exists.
# kind and analog_of have no unambiguous source column, so they are not guessed.
COLUMN_MAP = {
    "name": "Site_name",
    "body": "Body",
    "lat": "Latitude",
    "lon": "Longitude",
    "kind": None,
    "analog_of": None,
    "source_url_1": None,
    "source_url_2": None,
}

BANNED = re.compile(r"\b(validated|discovered|undiscovered|new sites?)\b", re.I)
URL = re.compile(r"^https?://\S+$")


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_v1_sites(zip_path):
    """Return (sites, match_radius_km, exclusion_km) read from the zip's config files."""
    with zipfile.ZipFile(zip_path) as z:
        known = yaml.safe_load(z.read(ZIP_ROOT + "config/known_sites.yaml"))
        run = yaml.safe_load(z.read(ZIP_ROOT + "config/run.yaml"))
    match_km = float(run["site_match_radius_km"])
    excl_km = float(run["discovery"]["min_distance_km"])
    sites = []
    for group in ("primary", "secondary", "gate_tests", "negative_controls"):
        for sid, v in known[group].items():
            sites.append(
                {
                    "id": f"{group}/{sid}",
                    "lat": float(v["lat"]),
                    "lon": float(v["lon"]),
                    "bodies": list(v.get("bodies", ["moon", "mars"])),
                    "radius_km": float(v.get("radius_km", match_km)),
                }
            )
    sites.sort(key=lambda s: s["id"])
    return sites, match_km, excl_km


def v1_flag(lat, lon, body, v1_sites, excl_km):
    """Return (flag, matched_site_id, km). flag is 'true', 'false' or 'unknown'.

    true: within v1's own match radius of a v1 site that v1 ran for this body.
    unknown: within the 100 km exclusion distance, or matched a v1 site that v1 did not run for this body.
    false: farther than the exclusion distance from every entry in known_sites.yaml, so the file shows v1 did not use it.
    """
    best = None
    for s in v1_sites:
        d = haversine_km(lat, lon, s["lat"], s["lon"])
        if best is None or d < best[0]:
            best = (d, s)
    d, s = best
    km = round(d, 1)
    if d <= s["radius_km"]:
        if body.lower() in s["bodies"]:
            return "true", s["id"], km
        return "unknown", s["id"], km
    if d <= excl_km:
        return "unknown", s["id"], km
    return "false", s["id"], km


def read_rows(csv_path):
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        rows = list(reader)
    return header, rows


def check(csv_path, zip_path):
    header, raw = read_rows(csv_path)
    v1_sites, match_km, excl_km = load_v1_sites(zip_path)
    missing_cols = [b for b, c in COLUMN_MAP.items() if c is None or c not in header]
    results = []
    seen_key = {}
    for i, r in enumerate(raw, start=2):  # line 1 is the header
        name = (r.get("Site_name") or "").strip()
        body = (r.get("Body") or "").strip()
        fails = []
        info = []
        lat = lon = None
        try:
            lat = float(r.get("Latitude", ""))
            lon = float(r.get("Longitude", ""))
            if not (-90 <= lat <= 90):
                fails.append("lat out of range")
            if not (-180 <= lon <= 180):
                fails.append("lon out of range")
            if lat == 0 and lon == 0:
                fails.append("coordinates 0,0")
        except ValueError:
            fails.append("bad coordinates")
        if not name:
            fails.append("missing name")
        if body not in ("Moon", "Mars"):
            fails.append("bad body")
        key = (name.lower(), body.lower())
        if key in seen_key:
            fails.append(f"duplicate of line {seen_key[key]}")
        else:
            seen_key[key] = i
        # Source rule: two source URLs are required. The CSV has no such columns.
        urls = [r.get(c, "") for c in ("source_url_1", "source_url_2") if c in r]
        n_src = sum(1 for u in urls if URL.match((u or "").strip()))
        if n_src < 2:
            fails.append(f"fewer than 2 source URLs ({n_src} found)")
        if "approx" in (r.get("Coordinate_note") or "").lower():
            info.append("coordinates marked approximate in the CSV")
        if any(BANNED.search(v or "") for v in r.values()):
            info.append("row text contains a banned term (not carried into any output)")
        flag = ("unknown", "", None)
        if lat is not None and lon is not None and "bad body" not in fails:
            flag = v1_flag(lat, lon, body, v1_sites, excl_km)
        results.append(
            {
                "line": i,
                "name": name,
                "body": body,
                "lat": lat,
                "lon": lon,
                "fails": fails,
                "info": info,
                "v1_used": flag[0],
                "v1_site": flag[1],
                "v1_km": flag[2],
            }
        )
    # Same coordinates under different rows (informational: the same place listed for both bodies)
    by_coord = {}
    for r in results:
        if r["lat"] is not None:
            by_coord.setdefault((round(r["lat"], 2), round(r["lon"], 2)), []).append(r)
    same_place = [v for k, v in sorted(by_coord.items()) if len(v) > 1]
    return {
        "header": header,
        "rows": results,
        "missing_cols": missing_cols,
        "same_place": same_place,
        "match_km": match_km,
        "excl_km": excl_km,
        "n_v1_sites": len(v1_sites),
    }


def clean_rows(rep, raw_rows):
    """Rows that pass every check. Output uses the contract schema; unmapped fields stay empty."""
    out = []
    for res, r in zip(rep["rows"], raw_rows):
        if res["fails"]:
            continue
        out.append(
            {
                "name": res["name"],
                "body": res["body"],
                "lat": f"{res['lat']:.4f}",
                "lon": f"{res['lon']:.4f}",
                "kind": "",
                "analog_of": "",
                "source_url_1": r["source_url_1"].strip(),
                "source_url_2": r["source_url_2"].strip(),
                "v1_used": res["v1_used"],
            }
        )
    return out


def write_sites_csv(path, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=OUT_COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())


def write_report(path, rep, csv_sha, zip_sha, n_kept):
    rows = rep["rows"]
    failing = [r for r in rows if r["fails"]]
    counts = {}
    for r in rows:
        counts[r["v1_used"]] = counts.get(r["v1_used"], 0) + 1
    L = []
    L.append("# Site check report (B2)")
    L.append("")
    L.append("Generated by `scripts/gsop_data/sites.py`. Internal report, not site text.")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append(f"- Input: `GSOP_analog_sites_moon_mars.csv`, sha256 `{csv_sha}`.")
    L.append(f"- Rows read: {len(rows)}. Rows kept in `data/reference/sites.csv`: {n_kept}. Rows listed below as failing: {len(failing)}.")
    L.append("- Every row fails the two-source rule: the CSV has no source URL column at all.")
    L.append("- Rows with fewer than two sources are excluded from the site list and stay in this report.")
    n_coord = sum(1 for r in rows if any(("coordinates" in f or "out of range" in f) for f in r["fails"]))
    n_dup = sum(1 for r in rows if any(f.startswith("duplicate") for f in r["fails"]))
    L.append(f"- Rows with bad or out-of-range coordinates: {n_coord}. Rows that repeat an earlier name and body: {n_dup}.")
    L.append("")
    L.append("## Schema mapping")
    L.append("")
    L.append("| Brief field | CSV column | Status |")
    L.append("|---|---|---|")
    notes = {
        "name": "mapped",
        "body": "mapped",
        "lat": "mapped",
        "lon": "mapped",
        "kind": "no matching column. `Category` holds a list label, `Process_type` holds geology. Not guessed.",
        "analog_of": "no matching column. `Scored_against` names a v2 weighting, not an analog target. Not guessed.",
        "source_url_1": "no column",
        "source_url_2": "no column",
    }
    for b in SCHEMA:
        c = COLUMN_MAP[b]
        L.append(f"| {b} | {('`' + c + '`') if c else 'none'} | {notes[b]} |")
    L.append("")
    L.append("## Concerns about the input file")
    L.append("")
    L.append(f"- The file has {len(rep['header'])} columns and {len(rows)} rows. The brief expects 8 columns and about 50 sites.")
    L.append("- Row groups in the file: 50 Moon rows and 50 Mars rows labelled as known sites, plus 10 Moon and 10 Mars rows labelled as low-profile candidates. The 50-site table in the plan does not match 100 known rows.")
    L.append("- Numeric columns (`Similarity_pct`, `MonteCarlo_5th_pct`, `MonteCarlo_95th_pct`, `MC_rank_range_of_60`, the `P_*` columns) are not in the v1 outputs. The `Scored_against` column says they were produced with \"GSOP v2 weights\". They are not carried into any data file (hard rule 2).")
    L.append("- `GSOP_gate_check`, `Nearest_known_km` and `Passes_100km_novelty_rule` are also not v1 outputs. They are not carried over.")
    L.append("- The 20 low-profile candidate rows are hand-picked with their own scores. v1 candidates come only from `regions.json` (B10), not from this list.")
    ban = sum(1 for r in rows if any("banned term" in x for x in r["info"]))
    L.append(f"- {ban} rows contain a term from the banned-word list in CLAUDE.md. One column header does too (the column about when each site was first recognised). None of that text is copied into outputs.")
    approx = sum(1 for r in rows if any("approximate" in x for x in r["info"]))
    L.append(f"- {approx} rows mark their coordinates as approximate. The site match for v1 uses a {rep['match_km']:.0f} km radius, so this affects the flag only for sites near that distance.")
    L.append("")
    L.append("## v1 used flag")
    L.append("")
    L.append(f"- Source: `config/known_sites.yaml` and `config/run.yaml` in the v1 zip ({rep['n_v1_sites']} entries: primary, secondary, gate tests, negative controls).")
    L.append(f"- `true`: within v1's own site match radius ({rep['match_km']:.0f} km, or the site's own radius) of a v1 site that v1 ran for the row's body.")
    L.append(f"- `unknown`: within {rep['excl_km']:.0f} km of a v1 site but outside its match radius, or near a v1 site that v1 did not run for this body. The files cannot say whether v1 meant the same place.")
    L.append(f"- `false`: farther than {rep['excl_km']:.0f} km from every entry in `known_sites.yaml`. The file shows v1 did not use it.")
    L.append(f"- Counts over all {len(rows)} rows: true {counts.get('true', 0)}, unknown {counts.get('unknown', 0)}, false {counts.get('false', 0)}.")
    L.append("- This is a coordinate match, not a name match. Descriptive only.")
    L.append("")
    L.append("## Same place listed more than once (informational)")
    L.append("")
    L.append("Same coordinates to 2 decimals. These are listed for both bodies, which the (name, body) key allows.")
    L.append("")
    L.append("| Lines | Names | Bodies |")
    L.append("|---|---|---|")
    for grp in rep["same_place"]:
        L.append("| " + ", ".join(str(g["line"]) for g in grp) + " | " + "; ".join(g["name"] for g in grp) + " | " + ", ".join(g["body"] for g in grp) + " |")
    L.append("")
    L.append("## Failing rows")
    L.append("")
    L.append("Line numbers refer to the CSV file (line 1 is the header).")
    L.append("")
    L.append("| Line | Name | Body | Lat | Lon | Failed checks | v1 used | Nearest v1 site (km) |")
    L.append("|---:|---|---|---:|---:|---|---|---|")
    for r in rows:
        if not r["fails"]:
            continue
        lat = "" if r["lat"] is None else f"{r['lat']:.4f}"
        lon = "" if r["lon"] is None else f"{r['lon']:.4f}"
        near = f"{r['v1_site']} ({r['v1_km']})" if r["v1_site"] else ""
        L.append(f"| {r['line']} | {r['name']} | {r['body']} | {lat} | {lon} | {'; '.join(r['fails'])} | {r['v1_used']} | {near} |")
    L.append("")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(L))


def sha256_file(path):
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(zip_path, csv_path, out_dir):
    import os

    os.makedirs(out_dir, exist_ok=True)
    _, raw = read_rows(csv_path)
    rep = check(csv_path, zip_path)
    kept = clean_rows(rep, raw)
    write_sites_csv(os.path.join(out_dir, "sites.csv"), kept)
    write_report(os.path.join(out_dir, "sites_check.md"), rep, sha256_file(csv_path), sha256_file(zip_path), len(kept))
    return rep, kept


if __name__ == "__main__":
    import sys

    rep, kept = run(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"rows {len(rep['rows'])}, kept {len(kept)}")
