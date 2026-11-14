#!/usr/bin/env python3
"""Copy the optional v2 sim outputs from AnayDhawan/sim into data/v2/ (B16). Needs the `gh` CLI, logged in.

    python3 scripts/sync_v2.py [--repo AnayDhawan/sim] [--out data/v2]

Every file is optional. Whatever exists on the listed branches is copied byte for byte, with its path kept, and
data/v2/SOURCES.csv records branch, commit and sha256 for each. A file that is missing is simply not copied; nothing
is invented. Later branches in BRANCHES win when the same path exists on more than one.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys

BRANCHES = ["main", "data/thermal-refs", "data/site-evidence"]
WANTED = re.compile(
    r"^(runs/v2/(metrics\.json|ledger\.json|claims_v2\.csv|claims_c\.csv|PREREG[^/]*\.md|prereg[^/]*\.sha256)"
    r"|data/reference/thermal_refs(_files)?\.csv"
    r"|data/evidence/(site_measurements\.csv|ledger_c\.json)"
    r"|public/img/sites/[^/]+\.(jpg|json)"
    r"|docs/(refs_limits|evidence_limits|data_resources)\.md)$"
)
MAX_BYTES = 5 * 1024 * 1024  # no single copied file may be larger than this


def gh(args, binary=False):
    r = subprocess.run(["gh", "api", *args], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode(errors="replace").strip()[:300])
    return r.stdout if binary else r.stdout.decode("utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="AnayDhawan/sim")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "v2"))
    a = ap.parse_args(argv)
    chosen = {}  # path -> (branch, commit, blob sha, size)
    for br in BRANCHES:
        try:
            commit = json.loads(gh([f"repos/{a.repo}/commits/{br}"]))["sha"]
            tree = json.loads(gh([f"repos/{a.repo}/git/trees/{commit}?recursive=1"]))["tree"]
        except RuntimeError as e:
            print(f"branch {br}: not readable ({e}); skipped")
            continue
        for t in tree:
            if t["type"] == "blob" and WANTED.match(t["path"]):
                chosen[t["path"]] = (br, commit, t["sha"], t.get("size", 0))
    rows = []
    for path in sorted(chosen):
        br, commit, blob, size = chosen[path]
        if size > MAX_BYTES:
            print(f"skipped {path}: {size} bytes is over the {MAX_BYTES} byte limit")
            continue
        data = gh(["-H", "Accept: application/vnd.github.raw", f"repos/{a.repo}/git/blobs/{blob}"], binary=True)
        dest = os.path.join(a.out, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        rows.append([path, br, commit, len(data), hashlib.sha256(data).hexdigest()])
        print(f"copied {path} ({br})")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["path", "branch", "commit", "bytes", "sha256"])
    w.writerows(rows)
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "SOURCES.csv"), "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())
    print(f"{len(rows)} files in {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
