#!/usr/bin/env python3
"""make_data: one command that turns the v1 results zip and the site CSV into every contract file.

    python3 scripts/make_data.py [--zip ZIP] [--csv CSV] [--root DIR] [--skip-verify]

Deterministic: sorted keys, fixed number formatting, no timestamps. Reads stored v1 values only.
Writes under ROOT (default: the repo): public/data/*, data/reference/*, data/MANIFEST.csv.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gsop_data import fmt  # noqa: E402
from gsop_data.v1 import V1  # noqa: E402

REPO = os.path.dirname(HERE)


class Ctx:
    def __init__(self, v1, csv_path, root):
        self.v1 = v1
        self.csv_path = csv_path
        self.root = root
        self.sites = []
        self.repo = REPO

    def path(self, rel):
        return os.path.join(self.root, rel)

    def log(self, msg):
        print(msg, flush=True)


def write_manifest(ctx):
    """data/MANIFEST.csv: path, bytes, sha256 for public/data/**, data/reference/sites.csv, data/reference/raw/*, data/v2/** and public/img/sites/**."""
    rels = []
    base = ctx.path("public/data")
    for dp, _, fs in os.walk(base):
        for f in fs:
            rels.append(os.path.relpath(os.path.join(dp, f), ctx.root).replace(os.sep, "/"))
    for f in ("data/reference/sites.csv", "data/reference/sites_export.json"):
        if os.path.exists(ctx.path(f)):
            rels.append(f)
    for extra in ("data/v2", "public/img/sites"):
        d = ctx.path(extra)
        for dp, _, fs in os.walk(d):
            for f in fs:
                rels.append(os.path.relpath(os.path.join(dp, f), ctx.root).replace(os.sep, "/"))
    raw = ctx.path("data/reference/raw")
    if os.path.isdir(raw):
        rels += [f"data/reference/raw/{f}" for f in sorted(os.listdir(raw))]
    rows = ["path,bytes,sha256"]
    for rel in sorted(rels):
        p = ctx.path(rel)
        rows.append(f"{rel},{os.path.getsize(p)},{fmt.sha256_file(p)}")
    fmt.write_text(ctx.path("data/MANIFEST.csv"), "\n".join(rows) + "\n")
    ctx.log(f"manifest: {len(rels)} files")


KB, MB = 1024, 1024 * 1024
SIZE_LIMITS = {
    "public/data/sites.json": 250 * KB,
    "public/data/site_lookup.json": 300 * KB,
    "public/data/tiles_top.json": 600 * KB,
    "public/data/regions.json": 150 * KB,
    "public/data/metrics.json": 100 * KB,
    "public/data/ledger.json": 60 * KB,
    "public/data/controls.json": 20 * KB,
    "public/data/v2.json": 250 * KB,
    "public/data/site_measurements.json": 2 * MB,
    "public/data/claims.csv": 3 * MB,
}
PNG_LIMIT = 2 * MB
TOTAL_LIMIT = 8 * MB


def check_sizes(ctx):
    """Fail the build when a file exceeds the limit in docs/DATA_CONTRACT.md."""
    bad, total = [], 0
    base = ctx.path("public/data")
    for dp, _, fs in os.walk(base):
        for f in fs:
            rel = os.path.relpath(os.path.join(dp, f), ctx.root).replace(os.sep, "/")
            size = os.path.getsize(os.path.join(dp, f))
            total += size
            limit = PNG_LIMIT if rel.endswith(".png") else SIZE_LIMITS.get(rel)
            if limit is not None and size > limit:
                bad.append(f"{rel}: {size} bytes over limit {limit}")
    if total > TOTAL_LIMIT:
        bad.append(f"public/data total {total} bytes over limit {TOTAL_LIMIT}")
    if bad:
        raise SystemExit("size limit exceeded:\n" + "\n".join(bad))
    ctx.log(f"sizes ok, public/data total {total} bytes")


def write_claims(ctx):
    """B11 builder: claims.csv from the data files already written under ROOT."""
    from gsop_data import claims

    rows = claims.build_claims(ctx.root)
    fmt.write_text(ctx.path("public/data/claims.csv"), claims.claims_text(rows))
    ctx.log(f"claims: {len(rows)} rows")


def steps():
    from gsop_data import controls, ledger, lookup, overlays, regions, sites, tiles, v2

    return [("sites", sites.build), ("overlays", overlays.build), ("tiles", tiles.build), ("lookup", lookup.build), ("ledger", ledger.build), ("regions", regions.build), ("controls", controls.build), ("v2", v2.build)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=os.path.join(REPO, "gsop_v1_results_2026-11-14.zip"))
    ap.add_argument("--csv", default=os.path.join(REPO, "data", "reference", "raw", "GSOP_analog_sites_moon_mars.csv"))
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--skip-verify", action="store_true")
    ap.add_argument("--no-export", action="store_true", help="do not refresh the Supabase snapshot even when keys are set")
    a = ap.parse_args(argv)
    if not a.no_export:
        import export_sites

        if export_sites.have_keys():
            try:
                print(f"supabase export: {export_sites.export()} rows refreshed")
            except RuntimeError as e:
                print(f"supabase export failed ({e}); using the committed snapshot", file=sys.stderr)
        else:
            print("supabase export: no keys set, using the committed snapshot (or the CSV if there is none)")
    v1 = V1(a.zip)
    ctx = Ctx(v1, a.csv, a.root)
    if not a.skip_verify:
        n, problems = v1.verify_all()
        if problems:
            print("v1 hash check FAILED:\n" + "\n".join(problems), file=sys.stderr)
            return 1
        ctx.log(f"v1 hash check: {n} files ok")
    for name, fn in steps():
        fn(ctx)
    write_claims(ctx)
    check_sizes(ctx)
    write_manifest(ctx)
    return 0


if __name__ == "__main__":
    sys.exit(main())
