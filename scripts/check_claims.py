#!/usr/bin/env python3
"""Claims check (B11). Standard library only. Lists every violation and exits non-zero.

  python3 scripts/check_claims.py [--root DIR]

Checks:
  (a) banned words in every site-facing text block (data/banned_words.txt itself and internal docs are not scanned)
  (b) every number in data text has a row in public/data/claims.csv, claims.csv matches the data files, and page source holds no typed number
  (c) the E32 sentence equals docs/E32.txt wherever it appears
  (d) data/MANIFEST.csv matches the files it lists and lists every file under public/data
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gsop_data import claims  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(HERE))
    a = ap.parse_args(argv)
    problems = claims.check(a.root)
    if problems:
        print(f"check_claims: {len(problems)} violation(s)")
        for p in problems[:200]:
            print("  -", p)
        if len(problems) > 200:
            print(f"  ... and {len(problems) - 200} more")
        return 1
    print("check_claims: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
