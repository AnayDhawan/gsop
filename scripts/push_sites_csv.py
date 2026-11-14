#!/usr/bin/env python3
"""Load GSOP_analog_sites_moon_mars.csv into Supabase.

Default is a dry run (prints counts, writes nothing). Flags:
  --docs   write docs/sites_check.md and docs/SOURCES_TODO.md
  --apply  write to Supabase (sites_llm_raw reload, sites insert/update)

The CSV is LLM output. Its scores (Similarity_pct, P_*, Monte Carlo bounds,
rank ranges, Scored_against, Passes_*, Nearest_*) are estimates, not simulation
output. They go to sites_llm_raw only, never to sites.

Keys come from the local .env (SUPABASE_URL, SUPABASE_SERVICE_KEY, and
SUPABASE_ANON_KEY for the RLS check). Nothing from .env is ever printed.
Standard library only; this script is never imported by the site.
"""
import argparse
import csv
import difflib
import json
import math
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data/reference/raw/GSOP_analog_sites_moon_mars.csv"
EXPECTED = {("Moon", "known"): 50, ("Moon", "candidate"): 10, ("Mars", "known"): 50, ("Mars", "candidate"): 10}

BANNED = re.compile(r"validated|discovered|undiscovered|new sites", re.I)
# Known rewrites only. Anything else that matches BANNED stops the run.
REWRITES = [
    (re.compile(r"\bDiscovered (\d{4})"), r"first described \1"),
    (re.compile(r"\bdiscovered (\d{4})"), r"first described \1"),
    (re.compile(r"\bplatinum first described (\d{4})", re.I), r"platinum first reported \1"),
    (re.compile(r"Apollo-validated"), "Apollo-era"),
    (re.compile(r"\bfield-validated", re.I), None),  # capitalisation kept, see _field
    (re.compile(r"find new sites"), "list candidate sites for review"),
]

# CSV column -> sites column. Everything not listed here is "raw only".
DIRECT = {
    "Site_name": "name",
    "Body": "body",
    "Country": "country",
    "Elevation_m": "elevation_m",
    "Justification": "why_analog",
    "Where_analogy_breaks": "key_differences",
    "Experiments_conducted": "experiments_done",
    "Experiments_that_can_be_conducted": "experiments_possible",
    "How_to_modify_artificially": "how_to_modify",
}
# sites text columns that can reach public/data (notes never does)
PUBLIC_TEXT = ["name", "country", "why_analog", "key_differences", "experiments_done",
               "experiments_possible", "how_to_modify", "source_note", "coord_source"]


def slugify(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")


def to_float(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def clean_text(v):
    """Apply the known rewrites. Returns (text, [rewrites applied])."""
    if v is None:
        return None, []
    out, hits = v, []
    for pat, rep in REWRITES:
        def sub(m, rep=rep):
            hits.append(m.group(0))
            if rep is None:  # field-validated -> field-measured, keep first letter case
                return ("F" if m.group(0)[0] == "F" else "f") + "ield-measured"
            return m.expand(rep)
        out = pat.sub(sub, out)
    return out, hits


def haversine(a, b, c, d):
    p = math.pi / 180
    h = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(h))


def load_csv():
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build(rows):
    sites, raws, rewrites, banned_left = [], [], [], []
    used = set()
    for i, r in enumerate(rows, start=1):
        raws.append({"row_num": i, "raw": r})
        lat, lon = to_float(r["Latitude"]), to_float(r["Longitude"])
        bad = lat is None or lon is None or abs(lat) > 90 or abs(lon) > 180 or (lat == 0 and lon == 0)
        if bad:
            lat = lon = None
        base = slugify(r["Site_name"])
        slug, n = base, 2
        while (slug, r["Body"]) in used:
            slug = f"{base}-{n}"
            n += 1
        used.add((slug, r["Body"]))
        first_used = (r["First_used_as_analog"] or "").strip()
        ym = re.match(r"^(\d{4})\b", first_used)
        notes = "\n".join(x for x in (
            f"Discovered_or_recognised (CSV): {r['Discovered_or_recognised']}" if r["Discovered_or_recognised"] else "",
            f"Prior_analog_use (CSV): {r['Prior_analog_use']}" if r["Prior_analog_use"] else "",
            f"First_used_as_analog (CSV): {first_used}" if first_used else "",
            f"Process_type (CSV): {r['Process_type']}" if r["Process_type"] else "",
        ) if x)
        row = {
            "slug": slug,
            "list": "known" if r["Category"].startswith("Known") else "candidate",
            "lat": lat, "lon": lon,
            "coord_flag": "bad" if bad else None,
            "coord_source": "csv_approx" if "approx" in (r["Coordinate_note"] or "").lower() else "csv",
            "year_first_used_as_analog": int(ym.group(1)) if ym else None,
            "notes": notes or None,
            "origin": "llm_csv", "status": "draft", "sources_ok": False,
            "source_url_1": None, "source_url_2": None, "source_url_3": None,
            "source_note": "no sources in CSV", "v1_used": None,
        }
        for src, dst in DIRECT.items():
            v = (r[src] or "").strip()
            if dst == "elevation_m":
                row[dst] = to_float(v)
            else:
                row[dst], hits = clean_text(v or None)
                for h in hits:
                    rewrites.append((i, dst, h))
        for c in PUBLIC_TEXT:
            for m in BANNED.finditer(row.get(c) or ""):
                banned_left.append((i, c, m.group(0)))
        sites.append(row)
    return sites, raws, rewrites, banned_left


def hard_checks(sites, banned_left):
    errs = []
    if len(sites) != 120:
        errs.append(f"row count {len(sites)} != 120")
    keys = Counter((s["slug"], s["body"]) for s in sites)
    errs += [f"duplicate (slug, body): {k}" for k, n in keys.items() if n > 1]
    errs += [f"empty slug: row {i + 1}" for i, s in enumerate(sites) if not s["slug"]]
    errs += [f"banned word left: row {i} col {c} word {w!r}" for i, c, w in banned_left]
    nk = Counter((s["body"], s["list"]) for s in sites)
    for k, want in EXPECTED.items():
        if nk[k] != want:
            errs.append(f"count {k}: {nk[k]} != {want}")
    return errs


def check_doc(rows, sites, rewrites):
    L = ["# Sites CSV check", "",
         "Source: `data/reference/raw/GSOP_analog_sites_moon_mars.csv`. The CSV is LLM output. Scores in it are estimates, not simulation output. This file lists problems and changes nothing.", ""]
    nk = Counter((s["body"], s["list"]) for s in sites)
    L += ["## Counts by body and list", "", "| Body | List | Rows | Expected |", "|---|---|---|---|"]
    for k, want in EXPECTED.items():
        L.append(f"| {k[0]} | {k[1]} | {nk[k]} | {want} |")
    L.append(f"\nTotal: {len(sites)}\n")

    L += ["## Coordinates", ""]
    bad = [(i + 1, s) for i, s in enumerate(sites) if s["coord_flag"] == "bad"]
    L.append(f"- Rows flagged coord_flag='bad' (blank, unparseable, out of range or 0,0): {len(bad)}")
    for i, s in bad:
        L.append(f"  - row {i}: {s['name']} ({s['body']})")
    approx = sum(s["coord_source"] == "csv_approx" for s in sites)
    L.append(f"- Approximate coordinates (Coordinate_note contains 'approx'): {approx} (expected about 60)")
    pts = [(i + 1, s) for i, s in enumerate(sites) if s["lat"] is not None]
    close = []
    for a in range(len(pts)):
        for b in range(a + 1, len(pts)):
            (ia, sa), (ib, sb) = pts[a], pts[b]
            if sa["body"] == sb["body"]:
                d = haversine(sa["lat"], sa["lon"], sb["lat"], sb["lon"])
                if d < 1:
                    close.append((d, ia, sa, ib, sb))
    L.append(f"- Same-body points within 1 km: {len(close)}")
    for d, ia, sa, ib, sb in sorted(close, key=lambda t: t[0]):
        L.append(f"  - {d:.2f} km: row {ia} {sa['name']} / row {ib} {sb['name']} ({sa['body']})")

    L += ["", "## Same slug on both bodies (one page, two sections by design)", ""]
    by = defaultdict(set)
    for s in sites:
        by[s["slug"]].add(s["body"])
    both = sorted(k for k, v in by.items() if len(v) > 1)
    L.append(f"- Count: {len(both)}")
    L += [f"  - {k}" for k in both]

    L += ["", "## Possible merges (similar names across bodies, no auto-merge)", ""]
    def norm(n):
        return re.sub(r"\s+", " ", re.sub(r"\(.*?\)", "", n.lower())).strip()
    moon = [(i + 1, s) for i, s in enumerate(sites) if s["body"] == "Moon"]
    mars = [(i + 1, s) for i, s in enumerate(sites) if s["body"] == "Mars"]
    pairs = []
    for ia, sa in moon:
        for ib, sb in mars:
            if sa["slug"] == sb["slug"]:
                continue
            ratio = difflib.SequenceMatcher(None, norm(sa["name"]), norm(sb["name"])).ratio()
            if ratio >= 0.75:
                pairs.append((ratio, ia, sa, ib, sb))
    L.append(f"- Pairs with name similarity >= 0.75 and different slugs: {len(pairs)}")
    for r, ia, sa, ib, sb in sorted(pairs, key=lambda t: -t[0]):
        L.append(f"  - {r:.2f}: Moon row {ia} {sa['name']} / Mars row {ib} {sb['name']}")

    L += ["", "## Candidate novelty check (nearest known site, haversine over all 100 known rows)", "",
          "Tolerance 2 km against the CSV's Nearest_known_km. Known rows without coordinates are skipped.", "",
          "| Row | Candidate | Body | CSV nearest | CSV km | Recomputed nearest | Recomputed km | Diff km | Note |",
          "|---|---|---|---|---|---|---|---|---|"]
    known = [s for s in sites if s["list"] == "known" and s["lat"] is not None]
    diffs = 0
    for i, (s, r) in enumerate(zip(sites, rows), start=1):
        if s["list"] != "candidate":
            continue
        csv_km = to_float(r["Nearest_known_km"])
        if s["lat"] is None:
            L.append(f"| {i} | {s['name']} | {s['body']} | {r['Nearest_known_analog_site']} | {r['Nearest_known_km']} | n/a | n/a | n/a | no coordinates |")
            diffs += 1
            continue
        d, n = min(((haversine(s["lat"], s["lon"], k["lat"], k["lon"]), k["name"]) for k in known),
                   key=lambda t: t[0])
        diff = None if csv_km is None else abs(d - csv_km)
        note = "unverifiable (CSV km blank)" if csv_km is None else ("DIFF" if diff > 2 else "ok")
        if csv_km is None or diff > 2:
            diffs += 1
        L.append(f"| {i} | {s['name']} | {s['body']} | {r['Nearest_known_analog_site']} | {r['Nearest_known_km']} | {n} | {d:.0f} | {'' if diff is None else f'{diff:.0f}'} | {note} |")
    L.append(f"\nCandidates needing review: {diffs}\n")

    L += ["## Empty-field counts (sites columns mapped from the CSV)", "", "| Column | Empty of 120 |", "|---|---|"]
    for c in ["name", "body", "list", "slug", "country", "lat", "lon", "elevation_m", "why_analog", "key_differences",
              "experiments_done", "experiments_possible", "how_to_modify", "year_first_used_as_analog", "notes"]:
        L.append(f"| {c} | {sum(1 for s in sites if s.get(c) in (None, ''))} |")
    L.append("\nColumns with no CSV equivalent stay null: kind, analog_of, region, summary, terrain_geology, climate, parameters_matched, access_and_facilities, hazards, elevation source.")

    L += ["", "## Banned-word rewrites applied to public columns", "",
          "Wording rule E32. Only the agreed rewrites were applied. Original text stays in sites_llm_raw. Capitalisation of the first letter was kept for field-measured.", ""]
    if rewrites:
        L += [f"- row {i} column {c}: `{h}`" for i, c, h in rewrites]
    else:
        L.append("- none")
    return "\n".join(L) + "\n"


def todo_doc(sites):
    L = ["# Sources to add", "",
         "The CSV has no source URLs. Every row needs two real sources added by a person before sources_ok can be set to true.", "",
         f"Rows: {len(sites)}", ""]
    for body in ("Moon", "Mars"):
        for lst in ("known", "candidate"):
            sel = [s for s in sites if s["body"] == body and s["list"] == lst]
            L += [f"## {body}, {lst} ({len(sel)})", "", "| slug | body | sources_ok |", "|---|---|---|"]
            L += [f"| {s['slug']} | {s['body']} | false |" for s in sel]
            L.append("")
    return "\n".join(L)


# ---------- Supabase (PostgREST over urllib; keys only from .env) ----------
def env():
    d = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


class Api:
    def __init__(self, key_name):
        e = env()
        self.base = e["SUPABASE_URL"].rstrip("/") + "/rest/v1/"
        self.key = e[key_name]

    def call(self, method, path, body=None, prefer=None):
        h = {"apikey": self.key, "Authorization": "Bearer " + self.key, "Content-Type": "application/json"}
        if prefer:
            h["Prefer"] = prefer
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                t = r.read().decode()
                return r.status, (json.loads(t) if t else None)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()[:300]


def apply(sites, raws):
    api = Api("SUPABASE_SERVICE_KEY")
    st, out = api.call("GET", "sites?select=slug,origin,sources_ok,list&limit=1")
    if st != 200:
        sys.exit(f"STOP: probe of sites(slug,origin,sources_ok,list) failed ({st}): {out}. Run SQL v2 and add the list column.")
    # sites_llm_raw: delete by row_num, then insert (no duplicates on rerun)
    st, out = api.call("DELETE", "sites_llm_raw?row_num=gte.0", prefer="return=minimal")
    if st >= 300:
        sys.exit(f"STOP: sites_llm_raw delete failed ({st}): {out}")
    st, out = api.call("POST", "sites_llm_raw", raws, prefer="return=minimal")
    if st >= 300:
        sys.exit(f"STOP: sites_llm_raw insert failed ({st}): {out}")
    # sites: insert new, update only origin='llm_csv' AND status='draft'
    st, ex = api.call("GET", "sites?select=id,name,body,origin,status&limit=1000")
    if st != 200:
        sys.exit(f"STOP: reading existing sites failed ({st}): {ex}")
    existing = {(e["name"], e["body"]): e for e in ex}
    new, upd, skipped = [], [], []
    for s in sites:
        e = existing.get((s["name"], s["body"]))
        if e is None:
            new.append(s)
        elif e["origin"] == "llm_csv" and e["status"] == "draft":
            upd.append((e["id"], s))
        else:
            skipped.append(s["name"])
    if new:
        st, out = api.call("POST", "sites", new, prefer="return=minimal")
        if st >= 300:
            sys.exit(f"STOP: sites insert failed ({st}): {out}")
    for id_, s in upd:
        st, out = api.call("PATCH", f"sites?id=eq.{id_}&origin=eq.llm_csv&status=eq.draft", s, prefer="return=minimal")
        if st >= 300:
            sys.exit(f"STOP: sites update failed ({st}) for {s['name']}: {out}")
    print(f"apply: sites_llm_raw {len(raws)} rows; sites inserted {len(new)}, updated {len(upd)}, skipped (hand-edited) {len(skipped)}")
    return skipped


def verify():
    svc, anon = Api("SUPABASE_SERVICE_KEY"), Api("SUPABASE_ANON_KEY")
    st, rows = svc.call("GET", "sites?select=*&limit=1000")
    assert st == 200, rows
    print("verify sites:", len(rows), dict(Counter((r["body"], r["list"]) for r in rows)))
    st, raw = svc.call("GET", "sites_llm_raw?select=row_num&limit=1000")
    print("verify sites_llm_raw (service key):", len(raw))
    st, araw = anon.call("GET", "sites_llm_raw?select=row_num&limit=1000")
    print("verify sites_llm_raw (anon key):", len(araw) if st == 200 else f"http {st}", "-> RLS blocks anon" if (st != 200 or not araw) else "-> RLS NOT blocking")
    score_cols = [c for c in rows[0] if re.search(r"similarity|^p_|monte|rank|passes|nearest|scored|gate", c, re.I)]
    print("verify score-like columns in sites:", score_cols or "none", "| parameters_matched non-null:", sum(1 for r in rows if r.get("parameters_matched")))
    hits = [(r["slug"], c) for r in rows for c, v in r.items()
            if c not in ("notes", "id", "created_at") and isinstance(v, str) and BANNED.search(v)]
    print("verify banned words in public columns:", len(hits), hits[:5])
    pct = [(r["slug"], c) for r in rows for c, v in r.items()
           if c not in ("notes", "id", "created_at") and isinstance(v, str) and re.search(r"\d+\s?%", v)]
    print("note: % strings in public text (informational):", len(pct))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--docs", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if not CSV_PATH.exists():
        sys.exit(f"STOP: {CSV_PATH} missing")
    rows = load_csv()
    sites, raws, rewrites, banned_left = build(rows)
    errs = hard_checks(sites, banned_left)
    nk = Counter((s["body"], s["list"]) for s in sites)
    print(f"rows {len(rows)} | by body/list {dict(nk)} | coord bad {sum(s['coord_flag'] == 'bad' for s in sites)}"
          f" | approx {sum(s['coord_source'] == 'csv_approx' for s in sites)}"
          f" | years parsed {sum(s['year_first_used_as_analog'] is not None for s in sites)}"
          f" | rewrites {len(rewrites)} | banned left {len(banned_left)}")
    if errs:
        print("HARD CHECK FAILED:")
        print("\n".join("  " + e for e in errs))
        sys.exit(1)
    print("hard checks: pass")
    if a.docs:
        (ROOT / "docs/sites_check.md").write_text(check_doc(rows, sites, rewrites), encoding="utf-8")
        (ROOT / "docs/SOURCES_TODO.md").write_text(todo_doc(sites), encoding="utf-8")
        print("wrote docs/sites_check.md, docs/SOURCES_TODO.md")
    if a.apply:
        apply(sites, raws)
    if a.verify:
        verify()
    if not (a.apply or a.docs or a.verify):
        print("dry run: nothing written")


if __name__ == "__main__":
    main()
