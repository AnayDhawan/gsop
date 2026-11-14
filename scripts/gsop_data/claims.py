"""B11: claims builder and claims check. Standard library only, so CI can run it without installing packages.

claims.csv columns: claim, number, source_file, sha256.
`number` is the display string pages must print. Display rules are in docs/DATA_CONTRACT.md.
"""
import csv
import hashlib
import io
import json
import os
import re

CLAIM_COLUMNS = ["claim", "number", "source_file", "sha256"]
DATA = "public/data"
SITES_CSV = "data/reference/sites.csv"

# Keys whose string values are identifiers, paths, hashes or citations, not statements with numbers.
SKIP_KEYS = {"id", "claim", "source_file", "sha256", "file", "image", "legend", "hex", "nearest_reference_site", "unit", "source", "group", "crs", "colour_scale", "limits_source", "slug", "site_id"}
SKIP_META = {"sources", "facts"}
NUM_RE = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")
YEAR_RE = re.compile(r"^(19|20)\d\d$")  # citation years are not statistics
KEY_PREFIX = "The Monte Carlo varies the weights"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def d(v, dp):
    """Fixed-decimal display string; no negative zero."""
    r = round(float(v), dp)
    s = f"{r:.{dp}f}" if dp else str(int(r))
    return "0" if s in ("-0", "-0.0", "-0.00", "-0.000") and dp == 0 else (s[1:] if s.startswith("-0.") and float(s) == 0 else s)


def text_numbers(s):
    out = []
    for m in NUM_RE.findall(s):
        raw = m.rstrip(",")
        if YEAR_RE.match(raw.lstrip("-")):
            continue
        out.append(raw.replace(",", ""))
    return out


def load(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return json.load(f)


def iter_strings(obj, path="", skip=False):
    """Yield (path, string) for every site-facing string, skipping meta.sources, meta.facts and identifier keys."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in SKIP_KEYS:
                continue
            if path == "meta" and k in SKIP_META:
                continue
            yield from iter_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def build_claims(root):
    """Return a sorted list of (claim, number, source_file, sha256) built only from the data files under root."""
    rows = {}

    def add(claim, number, src, sha):
        if claim in rows and rows[claim] != (number, src, sha):
            raise ValueError(f"conflicting claim {claim}")
        rows[claim] = (number, src, sha)

    def local_sha(rel):
        return sha256_file(os.path.join(root, rel))

    files = sorted(
        os.path.relpath(os.path.join(dp, f), os.path.join(root, DATA)).replace(os.sep, "/")
        for dp, _, fs in os.walk(os.path.join(root, DATA))
        for f in fs
        if f.endswith(".json")
    )
    docs = {f: load(root, f"{DATA}/{f}") for f in files}
    # facts in every file header
    for f, doc in docs.items():
        for fa in doc.get("meta", {}).get("facts", []):
            add(fa["claim"], fa["number"], fa["source_file"], fa["sha256"])
    # metrics
    for m in docs.get("metrics.json", {}).get("metrics", []):
        if m["unit"] in ("status", "sha256"):
            continue
        add(f"metrics.{m['id']}", m["display"], m["source_file"], m["sha256"])
    # tiles
    for view, v in docs.get("tiles_top.json", {}).get("views", {}).items():
        add(f"tiles.{view}.n_gated_tiles", d(v["n_gated_tiles"], 0), v["source_file"], v["sha256"])
        add(f"tiles.{view}.n_top5_in_90pct_runs", d(v["n_top5_in_90pct_runs"], 0), v["source_file"], v["sha256"])
        spec = [("lat", 2), ("lon", 2), ("score", 1), ("mc_median", 1), ("mc_p05", 1), ("mc_p95", 1), ("freq_top5", 2), ("illum_match", 3), ("km_to_nearest_reference_site", 0)]
        for t in v["tiles"]:
            for k, dp in spec:
                if k in t:
                    add(f"tiles.{view}.{t['tile_id']}.{k}", d(t[k], dp), v["source_file"], v["sha256"])
    # site lookup
    lk = docs.get("site_lookup.json")
    if lk:
        for sid, views in lk["sites"].items():
            for view, e in views.items():
                if e["status"] == "scored":
                    for k, dp in (("km_to_tile", 1), ("score", 1), ("percentile", 1)):
                        add(f"lookup.{sid}.{view}.{k}", d(e[k], dp), e["source_file"], e["sha256"])
        for view, s in lk["summary_by_view"].items():
            for grp in ("v1_used_true", "v1_used_false", "v1_used_unknown"):
                for k in ("n", "n_group"):
                    add(f"lookup.summary.{view}.{grp}.{k}", d(s[grp][k], 0), s["source_file"], s["sha256"])
                if "median_percentile" in s[grp] and not isinstance(s[grp]["median_percentile"], str):
                    add(f"lookup.summary.{view}.{grp}.median_percentile", d(s[grp]["median_percentile"], 1), s["source_file"], s["sha256"])
    # regions
    rg = docs.get("regions.json")
    if rg:
        rsha = local_sha(f"{DATA}/regions.json")
        rsrc = f"{DATA}/regions.json"
        add("regions.count", d(len(rg["regions"]), 0), rsrc, rsha)
        for view, s in rg["meta"]["by_view"].items():
            for k, val in sorted(s.items()):
                add(f"regions.by_view.{view}.{k}", d(val, 0), rsrc, rsha)
        add("regions.tile_area_km2", d(rg["meta"]["tile_area_km2"], 0), rsrc, rsha)
        for r in rg["regions"]:
            for k, dp in (("n_tiles", 0), ("area_km2", 0), ("centroid_lat", 2), ("centroid_lon", 2), ("median_score", 1), ("median_mc_median", 1), ("km_to_nearest_reference_site", 0), ("n_tiles_in_india", 0)):
                add(f"regions.{r['id'].replace(' ', '_')}.{k}", d(r[k], dp), r["source_file"], r["sha256"])
    # overlays
    for f, doc in docs.items():
        if f.startswith("overlays/") and "observed_max" in doc:
            src = doc["meta"]["sources"][0] if doc["meta"]["sources"] else {"source_file": "", "sha256": ""}
            base = next(s for s in doc["meta"]["sources"] if s["source_file"].endswith("summary.json"))
            for k in ("observed_min", "observed_median", "observed_max"):
                add(f"overlay.{doc['target']}.{k}", d(doc[k], 1), base["source_file"], base["sha256"])
            data_src = next(s for s in doc["meta"]["sources"] if s["source_file"].endswith("base_scores.parquet"))
            add(f"overlay.{doc['target']}.n_scored_tiles", d(doc["n_scored_tiles"], 0), data_src["source_file"], data_src["sha256"])
    # sites: coordinates, elevation, year, and numbers inside names and CSV text
    st = docs.get("sites.json")
    if st:
        csv_rel = st["meta"]["sources"][0]["source_file"]
        ssha = st["meta"]["sources"][0]["sha256"]  # hash of the CSV as read by make_data
        for s in st["sites"]:
            add(f"sites.{s['id']}.lat", d(s["lat"], 2), csv_rel, ssha)
            add(f"sites.{s['id']}.lon", d(s["lon"], 2), csv_rel, ssha)
            if s["elevation_m"] is not None:
                add(f"sites.{s['id']}.elevation_m", d(s["elevation_m"], 0), csv_rel, ssha)
            if s["year_first_used_as_analog"] is not None:
                add(f"sites.{s['id']}.year_first_used_as_analog", str(s["year_first_used_as_analog"]), csv_rel, ssha)
            for field in ("name", "country", "why_analog", "key_differences", "experiments_done", "experiments_possible", "how_to_modify"):
                for i, n in enumerate(text_numbers(s[field] or "")):
                    add(f"sites.{s['id']}.{field}.text{i}", n, csv_rel, ssha)
    # ledger: numbers inside quoted v1 text
    lg = docs.get("ledger.json")
    if lg:
        for e in lg["entries"]:
            if e["type"] == "physical_difference":
                for i, n in enumerate(text_numbers(e["statement"])):
                    add(f"ledger.{e['id']}.statement.text{i}", n, e["source_file"], e["sha256"])
    return sorted((c, *v) for c, v in rows.items())


def claims_text(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CLAIM_COLUMNS)
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def read_claims(path):
    with open(path, encoding="utf-8", newline="") as f:
        return [tuple(r) for r in list(csv.reader(f))[1:]]


# ---------------- check ----------------

def banned_terms(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line.lower())
    return out


def term_regex(terms):
    return re.compile(r"\b(" + "|".join(re.escape(t).replace(r"\ ", r"\s+") for t in terms) + r")\b", re.I)


def text_scan_files(root):
    """Site-facing text outside the data JSON: page source under src/app, content/ and public/*.html or *.md."""
    for base in ("src/app", "content"):
        for dp, _, fs in os.walk(os.path.join(root, base)):
            for f in sorted(fs):
                if f.endswith((".tsx", ".ts", ".mdx", ".md", ".jsx", ".js")) and ".test." not in f:
                    yield os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")
    pub = os.path.join(root, "public")
    for dp, _, fs in os.walk(pub):
        if os.path.relpath(dp, pub).replace(os.sep, "/").startswith(("data", "brand")):
            continue
        for f in sorted(fs):
            if f.endswith((".html", ".md", ".txt")):
                yield os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")


def jsx_text(src):
    """Rough pass over page source: JSX text between tags and string literals that read like sentences."""
    for m in re.finditer(r">([^<>{}]*[A-Za-z][^<>{}]*)<", src):
        yield m.group(1)
    for m in re.finditer(r"""(["'`])((?:(?!\1)[^\\\n]|\\.)*?\s(?:(?!\1)[^\\\n]|\\.)*?)\1""", src):
        yield m.group(2)


def check(root):
    """Return a list of violation strings. Empty means pass."""
    v = []
    bw = os.path.join(root, "data/banned_words.txt")
    rx = term_regex(banned_terms(bw))
    data_files = sorted(
        os.path.relpath(os.path.join(dp, f), os.path.join(root, DATA)).replace(os.sep, "/")
        for dp, _, fs in os.walk(os.path.join(root, DATA))
        for f in fs
        if f.endswith(".json")
    )
    docs = {f: load(root, f"{DATA}/{f}") for f in data_files}
    claims_path = os.path.join(root, DATA, "claims.csv")
    committed = read_claims(claims_path) if os.path.exists(claims_path) else []
    # (0) claims.csv equals what the data files produce, and every source hash that is a repo file is current
    rebuilt = build_claims(root)
    if [tuple(r) for r in rebuilt] != committed:
        a, b = {r[0]: r for r in rebuilt}, {r[0]: r for r in committed}
        miss = sorted(set(a) - set(b))[:5]
        extra = sorted(set(b) - set(a))[:5]
        diff = sorted(k for k in set(a) & set(b) if a[k] != b[k])[:5]
        v.append(f"claims.csv does not match the data files (missing {len(set(a) - set(b))}, extra {len(set(b) - set(a))}, changed {sum(1 for k in set(a) & set(b) if a[k] != b[k])}); examples: missing {miss}, extra {extra}, changed {diff}")
    for c, n, src, sha in committed:
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            v.append(f"claims.csv: bad sha256 for {c}")
        local = os.path.join(root, src)
        if os.path.isfile(local) and sha256_file(local) != sha:
            v.append(f"claims.csv: sha256 for {c} does not match {src}")
    nums = {r[1] for r in committed}
    # (a) banned words and (b) numbers, in the data files' text
    for f, doc in docs.items():
        for p, s in iter_strings(doc):
            for m in rx.finditer(s):
                v.append(f"banned word '{m.group(0)}' in {DATA}/{f} at {p}")
            for n in text_numbers(s):
                if n not in nums:
                    v.append(f"number {n} in {DATA}/{f} at {p} has no row in claims.csv")
    # (a) and (b) in page source and static text
    for rel in text_scan_files(root):
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            src = fh.read()
        for m in rx.finditer(src):
            v.append(f"banned word '{m.group(0)}' in {rel}")
        for s in jsx_text(src):
            for n in text_numbers(s):
                if n not in nums:
                    v.append(f"number {n} in {rel} has no row in claims.csv: {s.strip()[:60]!r}")
    # (c) the E32 sentence
    e32_path = os.path.join(root, "docs/E32.txt")
    with open(e32_path, encoding="utf-8") as fh:
        e32 = fh.read().rstrip("\n")
    led = docs.get("ledger.json")
    if led is None or led["meta"].get("uncertainty_sentence") != e32:
        v.append("ledger.json meta.uncertainty_sentence differs from docs/E32.txt (or is missing)")
    for f, doc in docs.items():
        for p, s in iter_strings(doc):
            if KEY_PREFIX in s and s != e32:
                v.append(f"E32 sentence altered in {DATA}/{f} at {p}")
    for rel in text_scan_files(root):
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            src = fh.read()
        if KEY_PREFIX in src and e32 not in src:
            v.append(f"E32 sentence altered in {rel}")
    # (d) manifest
    mp = os.path.join(root, "data/MANIFEST.csv")
    if os.path.exists(mp):
        with open(mp, encoding="utf-8", newline="") as fh:
            for row in list(csv.reader(fh))[1:]:
                p, size, sha = row
                loc = os.path.join(root, p)
                if not os.path.isfile(loc):
                    v.append(f"MANIFEST lists a missing file: {p}")
                elif sha256_file(loc) != sha or os.path.getsize(loc) != int(size):
                    v.append(f"MANIFEST hash or size differs for {p}")
        listed = {r[0] for r in csv.reader(open(mp, encoding="utf-8"))}
        for dp, _, fs in os.walk(os.path.join(root, DATA)):
            for f in fs:
                rel = os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")
                if rel not in listed:
                    v.append(f"file not in MANIFEST: {rel}")
    else:
        v.append("data/MANIFEST.csv is missing")
    return v
