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

    def path(self, rel):
        return os.path.join(self.root, rel)

    def log(self, msg):
        print(msg, flush=True)


def write_manifest(ctx):
    """data/MANIFEST.csv: path, bytes, sha256 for public/data/** and data/reference/sites.csv. Lists nothing else."""
    rels = []
    base = ctx.path("public/data")
    for dp, _, fs in os.walk(base):
        for f in fs:
            rels.append(os.path.relpath(os.path.join(dp, f), ctx.root).replace(os.sep, "/"))
    if os.path.exists(ctx.path("data/reference/sites.csv")):
        rels.append("data/reference/sites.csv")
    rows = ["path,bytes,sha256"]
    for rel in sorted(rels):
        p = ctx.path(rel)
        rows.append(f"{rel},{os.path.getsize(p)},{fmt.sha256_file(p)}")
    fmt.write_text(ctx.path("data/MANIFEST.csv"), "\n".join(rows) + "\n")
    ctx.log(f"manifest: {len(rels)} files")


def steps():
    from gsop_data import sites

    return [("sites", sites.build)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=os.path.join(REPO, "gsop_v1_results_2026-11-14.zip"))
    ap.add_argument("--csv", default=os.path.join(REPO, "GSOP_analog_sites_moon_mars.csv"))
    ap.add_argument("--root", default=REPO)
    ap.add_argument("--skip-verify", action="store_true")
    a = ap.parse_args(argv)
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
    write_manifest(ctx)
    return 0


if __name__ == "__main__":
    sys.exit(main())
