"""B2 and B5: clean the site CSV and build sites.csv, sites_check.md and sites.json.

Lookup and transformation only. Nothing here scores anything.
The two-source rule from the brief was relaxed by instruction: the CSV has no source URLs, so rows are kept without them.
"""
import csv
import io
import math
import re

from .fmt import NOT_IN_V1, make_meta, num, sha256_file, write_json, write_text

SCHEMA = ["name", "body", "lat", "lon", "kind", "analog_of", "source_url_1", "source_url_2"]
OUT_COLUMNS = SCHEMA + ["v1_used"]
CSV_REF = "data/reference/raw/GSOP_analog_sites_moon_mars.csv"
NO_SOURCE = "not provided in site CSV"

# Brief field -> column in the site CSV. None means no such column exists.
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
MAP_NOTE = {
    "kind": "left empty: Process_type is ambiguous (see docs/sites_mapping.md), a person decides",
    "analog_of": "left empty: no CSV column (see docs/sites_mapping.md)",
    "source_url_1": "no column in the CSV; rule relaxed by instruction",
    "source_url_2": "no column in the CSV; rule relaxed by instruction",
}

BANNED = re.compile(r"\b(validated|discovered|undiscovered|new sites?)\b", re.I)
URL = re.compile(r"^https?://\S+$")


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def load_v1_sites(v1):
    known = v1.yaml("config/known_sites.yaml")
    run = v1.yaml("config/run.yaml")
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
    unknown: within the exclusion distance, or matched a v1 site that v1 did not run for this body.
    false: farther than the exclusion distance from every entry in known_sites.yaml.
    """
    best = None
    for s in v1_sites:
        d = haversine_km(lat, lon, s["lat"], s["lon"])
        if best is None or d < best[0]:
            best = (d, s)
    d, s = best
    km = round(d, 1)
    if d <= s["radius_km"]:
        return ("true" if body.lower() in s["bodies"] else "unknown"), s["id"], km
    if d <= excl_km:
        return "unknown", s["id"], km
    return "false", s["id"], km


def read_rows(csv_path):
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def check(csv_path, v1):
    header, raw = read_rows(csv_path)
    v1_sites, match_km, excl_km = load_v1_sites(v1)
    results = []
    seen = {}
    for i, r in enumerate(raw, start=2):  # line 1 is the header
        name = (r.get("Site_name") or "").strip()
        body = (r.get("Body") or "").strip()
        fails, info = [], []
        lat = lon = None
        try:
            lat = float(r.get("Latitude", ""))
            lon = float(r.get("Longitude", ""))
            if not (-90 <= lat <= 90):
                fails.append("lat out of range")
            if not (-180 <= lon <= 180):
                fails.append("lon out of range")
        except ValueError:
            fails.append("bad coordinates")
        if not name:
            fails.append("missing name")
        if body not in ("Moon", "Mars"):
            fails.append("bad body")
        key = (name.lower(), body.lower())
        if key in seen:
            fails.append(f"duplicate of line {seen[key]}")
        else:
            seen[key] = i
        in_list = (r.get("Category") or "").startswith("Known")
        if not in_list:
            fails.append("not a reference site (candidate row in the CSV)")
        n_src = sum(1 for c in ("source_url_1", "source_url_2") if URL.match((r.get(c) or "").strip()))
        if n_src < 2:
            info.append(f"source URLs: {n_src} (rule relaxed)")
        approx = "approx" in (r.get("Coordinate_note") or "").lower()
        for col in ("Site_name", "Where_analogy_breaks"):
            if BANNED.search(r.get(col) or ""):
                fails.append(f"banned term in {col}")
        flag = ("unknown", "", None)
        if not any(f.startswith(("lat", "lon", "bad")) for f in fails):
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
                "approx": approx,
                "limits": (r.get("Where_analogy_breaks") or "").strip(),
                "v1_used": flag[0],
                "v1_site": flag[1],
                "v1_km": flag[2],
            }
        )
    by_coord = {}
    for r in results:
        if r["lat"] is not None and not r["fails"]:
            by_coord.setdefault((round(r["lat"], 2), round(r["lon"], 2)), []).append(r)
    same_place = [v for k, v in sorted(by_coord.items()) if len(v) > 1]
    return {
        "header": header,
        "rows": results,
        "same_place": same_place,
        "match_km": match_km,
        "excl_km": excl_km,
        "n_v1_sites": len(v1_sites),
    }


def kept_rows(rep):
    out = [r for r in rep["rows"] if not r["fails"]]
    out.sort(key=lambda r: (r["body"], r["name"].lower(), r["line"]))
    return out


def write_sites_csv(path, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=OUT_COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(
            {
                "name": r["name"],
                "body": r["body"],
                "lat": f"{r['lat']:.4f}",
                "lon": f"{r['lon']:.4f}",
                "kind": "",
                "analog_of": "",
                "source_url_1": "",
                "source_url_2": "",
                "v1_used": r["v1_used"],
            }
        )
    write_text(path, buf.getvalue())


def write_report(path, rep, csv_sha, n_kept):
    rows = rep["rows"]
    failing = [r for r in rows if r["fails"]]
    counts = {}
    for r in rows:
        if not r["fails"]:
            counts[r["v1_used"]] = counts.get(r["v1_used"], 0) + 1
    L = ["# Site check report (B2)", ""]
    L.append("Generated by `scripts/make_data.py` (`scripts/gsop_data/sites.py`). Internal report, not site text.")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append(f"- Input: `{CSV_REF}`, sha256 `{csv_sha}`.")
    L.append(f"- Rows read: {len(rows)}. Rows kept in `data/reference/sites.csv`: {n_kept}. Rows listed below as failing: {len(failing)}.")
    L.append("- The two-source rule was relaxed by instruction. The CSV has no source URL column, so no kept row has a source link.")
    n_coord = sum(1 for r in rows if any(("coordinates" in f or "out of range" in f) for f in r["fails"]))
    n_dup = sum(1 for r in rows if any(f.startswith("duplicate") for f in r["fails"]))
    n_cand = sum(1 for r in rows if any(f.startswith("not a reference") for f in r["fails"]))
    n_ban = sum(1 for r in rows if any(f.startswith("banned") for f in r["fails"]))
    L.append(f"- Rows with bad or out-of-range coordinates: {n_coord}. Rows that repeat an earlier name and body: {n_dup}. Rows with a banned term in a carried field: {n_ban}.")
    L.append(f"- Rows left out because they are candidate rows, not reference sites: {n_cand}.")
    L.append("")
    L.append("## Schema mapping")
    L.append("")
    L.append("| Brief field | CSV column | Note |")
    L.append("|---|---|---|")
    for b in SCHEMA:
        c = COLUMN_MAP[b]
        L.append(f"| {b} | {('`' + c + '`') if c else 'none'} | {MAP_NOTE.get(b, 'mapped')} |")
    L.append("")
    L.append("## Concerns about the input file")
    L.append("")
    L.append(f"- The file has {len(rep['header'])} columns and {len(rows)} rows. The reference list kept here has {n_kept} rows (known sites for both bodies), not 50.")
    L.append("- Numeric columns (similarity, Monte Carlo band, per-parameter scores) are not v1 outputs; the `Scored_against` column says they used v2 weights. They are not carried into any data file.")
    L.append("- The gate-check labels and the novelty-rule columns are also not v1 outputs and are not carried over.")
    L.append("- The candidate rows are hand-picked with their own scores. v1 candidates come only from `regions.json` (B10).")
    L.append("- The carried free-text column (`Where_analogy_breaks`) is LLM-written and unreviewed. A few entries contain hand-typed numbers; those get claims rows pointing at `data/reference/sites.csv`.")
    L.append("- Column mapping decisions are in `docs/sites_mapping.md` and the row-level checks in `docs/sites_check.md` (both from the site-data PR). This report covers only what the build keeps, plus the v1 used flag.")
    approx = sum(1 for r in rows if not r["fails"] and r["approx"])
    L.append(f"- {approx} kept rows mark their coordinates as approximate.")
    L.append("")
    L.append("## v1 used flag")
    L.append("")
    L.append(f"- Source: `config/known_sites.yaml` and `config/run.yaml` in the v1 zip ({rep['n_v1_sites']} entries: primary, secondary, gate tests, negative controls).")
    L.append(f"- `true`: within v1's own site match radius ({rep['match_km']:.0f} km, or the site's own radius) of a v1 site that v1 ran for the row's body.")
    L.append(f"- `unknown`: within {rep['excl_km']:.0f} km of a v1 site but outside its match radius, or near a v1 site that v1 did not run for this body. The files cannot say whether v1 meant the same place.")
    L.append(f"- `false`: farther than {rep['excl_km']:.0f} km from every entry in `known_sites.yaml`. The file shows v1 did not use it.")
    L.append(f"- Counts over the {n_kept} kept rows: true {counts.get('true', 0)}, unknown {counts.get('unknown', 0)}, false {counts.get('false', 0)}.")
    L.append("- This is a coordinate match, not a name match. Descriptive only.")
    L.append("")
    L.append("## Same place listed more than once (informational)")
    L.append("")
    L.append("Same coordinates to 2 decimals. Listed for both bodies, which the (name, body) key allows.")
    L.append("")
    L.append("| Lines | Names | Bodies |")
    L.append("|---|---|---|")
    for grp in rep["same_place"]:
        L.append("| " + ", ".join(str(g["line"]) for g in grp) + " | " + "; ".join(g["name"] for g in grp) + " | " + ", ".join(g["body"] for g in grp) + " |")
    L.append("")
    L.append("## Rows not kept")
    L.append("")
    L.append("Line numbers refer to the CSV file (line 1 is the header).")
    L.append("")
    L.append("| Line | Name | Body | Lat | Lon | Reason |")
    L.append("|---:|---|---|---:|---:|---|")
    for r in failing:
        lat = "" if r["lat"] is None else f"{r['lat']:.4f}"
        lon = "" if r["lon"] is None else f"{r['lon']:.4f}"
        L.append(f"| {r['line']} | {r['name']} | {r['body']} | {lat} | {lon} | {'; '.join(r['fails'])} |")
    L.append("")
    write_text(path, "\n".join(L))


SITES_LIMITS = [
    "Sites are places named as analogs in an LLM-written list. They are not scored results.",
    "Coordinates come from an LLM-written CSV; many are approximate.",
    "The CSV gave no source links, so none are shown.",
    "Text about where the analogy breaks is LLM-written and has not been reviewed.",
    "The v1 used flag is a coordinate match against the v1 site list, not a name match.",
    "Earth sites differ from the Moon and Mars in gravity, air, radiation and dust; see the ledger.",
]


def build(ctx):
    """Write data/reference/sites.csv, sites_check.md and public/data/sites.json."""
    csv_path = ctx.csv_path
    rep = check(csv_path, ctx.v1)
    kept = kept_rows(rep)
    csv_sha = sha256_file(csv_path)
    write_sites_csv(ctx.path("data/reference/sites.csv"), kept)
    write_report(ctx.path("data/reference/sites_check.md"), rep, csv_sha, len(kept))
    sites = []
    ids = set()
    for r in kept:
        sid = f"{slug(r['name'])}-{r['body'].lower()}"
        if sid in ids:
            raise ValueError(f"duplicate site id {sid}")
        ids.add(sid)
        sites.append(
            {
                "id": sid,
                "name": r["name"],
                "body": r["body"],
                "lat": num(r["lat"], 4),
                "lon": num(r["lon"], 4),
                "kind": None,
                "analog_of": None,
                "source_url_1": NO_SOURCE,
                "source_url_2": NO_SOURCE,
                "coordinates_approximate": r["approx"],
                "v1_used": r["v1_used"],
                "v1_match": {"site_id": r["v1_site"], "km": num(r["v1_km"], 1)},
                "limits": r["limits"] if r["limits"] else NOT_IN_V1,
                "limits_source": "CSV column Where_analogy_breaks, LLM-written, unreviewed",
            }
        )
    sites.sort(key=lambda s: s["id"])
    meta = make_meta(
        "public/data/sites.json",
        "Reference sites from an LLM-written CSV. Descriptive list, not scored results.",
        SITES_LIMITS,
        [{"source_file": CSV_REF, "sha256": csv_sha}, ctx.v1.src("config/known_sites.yaml")],
        v1_used_rule=(
            "true: within the v1 site match radius of a v1 site run for the same body. "
            "unknown: near a v1 site but not matching, or v1 ran that site for the other body only. "
            "false: farther than the v1 exclusion distance from every v1 site."
        ),
    )
    write_json(ctx.path("public/data/sites.json"), {"meta": meta, "sites": sites})
    ctx.sites = sites
    ctx.log(f"sites: {len(sites)} kept of {len(rep['rows'])}")
