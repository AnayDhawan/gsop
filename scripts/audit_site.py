#!/usr/bin/env python3
"""Wording audit of the built site against the CLAUDE.md rules (issue C6, reused by F9). Standard library only.

    npm run build && npx next start -p 3100 &
    python3 scripts/audit_site.py --base http://localhost:3100 [--sample-sites 10]

Crawls the navigation routes and site pages, extracts the visible text, and checks:
  - banned words (data/banned_words.txt), with the E32 sentence allow-listed
  - no em dashes, no filler vocabulary (delve, seamless, leverage, unlock, showcase and similar)
  - the E32 sentence is printed word for word on every page that shows results, and never altered
  - pages that show results say the ranking has not been checked against independent data
  - pages that show Mars scores say Mars is a low-confidence secondary result
  - pages that show the controls say the negative-control test failed
  - every page has one h1; section headings are sentence case
  - candidates are called "candidates not in our reference list"
Exits non-zero and lists every problem.
"""
import argparse
import html
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gsop_data import claims  # noqa: E402

ROOT = os.path.dirname(HERE)
SLOP = ["delve", "seamless", "seamlessly", "leverage", "leveraging", "unlock", "unlocking", "showcase", "showcasing", "cutting-edge", "game-changer", "revolutionary", "groundbreaking", "tapestry", "elevate", "empower", "streamline", "holistic", "synergy", "dive into", "comprehensive solution", "state-of-the-art", "robust"]
# Pages that show scores or rankings and so must carry the standing statements.
RESULT_PAGES = {"/", "/map", "/ledger", "/method", "/sites"}
MARS_PAGES = {"/", "/map", "/ledger", "/method", "/sites"}
FAILED_CONTROL_PAGES = {"/", "/map", "/ledger", "/method"}
E32_PAGES = {"/", "/map", "/ledger", "/method"}
# Capitalised words allowed inside a sentence-case heading.
PROPER = {"Moon", "Mars", "Earth", "India", "GSOP", "Jezero", "Shackleton", "Connecting", "Ridge", "Failure-First", "Ledger", "Honest", "Map", "Natural", "Region", "NASA", "LP", "DAAC", "Monte", "Carlo", "Rub'", "Khali", "Namib", "Mars)"}


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def visible(page):
    page = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", page, flags=re.S)
    m = re.search(r"<main[^>]*>(.*?)</main>", page, flags=re.S)
    body = m.group(1) if m else page
    heads = [html.unescape(re.sub(r"<[^>]+>", "", h)).strip() for h in re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", body, flags=re.S)]
    levels = [int(x) for x in re.findall(r"<h([1-4])[\s>]", body)]
    text = re.sub(r"</(p|li|h[1-6]|tr|dd|dt|th|td|summary|blockquote|figcaption)>", "\n", body)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    text = "\n".join(re.sub(r"\s+", " ", l).strip() for l in text.split("\n"))
    return text, list(zip(levels, heads))


def sentence_case_problems(heads, skip_h1):
    out = []
    for level, h in heads:
        if level == 1 and skip_h1:
            continue
        words = h.split()
        for w in words[1:]:
            core = w.strip(".,:;()")
            if core and core[0].isupper() and core not in PROPER and not core.isupper() and not re.match(r"^[A-Z]\d", core):
                out.append(f'heading not in sentence case: "{h}" (word "{core}")')
                break
    return out


def audit_page(route, page, rx, e32, is_site_page):
    p = []
    text, heads = visible(page)
    body = text.replace(e32, "")
    for m in rx.finditer(body):
        p.append(f"banned word '{m.group(0)}'")
    if "—" in text:
        p.append("em dash in text")
    low = body.lower()
    for w in SLOP:
        if re.search(rf"\b{re.escape(w)}\b", low):
            p.append(f"filler word '{w}'")
    h1 = [h for lv, h in heads if lv == 1]
    if len(h1) != 1:
        p.append(f"expected one h1, found {len(h1)}")
    p += sentence_case_problems(heads, skip_h1=True)
    if route in E32_PAGES and e32 not in text:
        p.append("E32 sentence not printed word for word")
    if claims.KEY_PREFIX in text and e32 not in text:
        p.append("E32 sentence altered")
    if (route in RESULT_PAGES or is_site_page) and "independent data" not in text:
        p.append("does not say the ranking has not been checked against independent data")
    if route in MARS_PAGES and "low-confidence" not in text:
        p.append("shows Mars scores without saying Mars is a low-confidence secondary result")
    if route in FAILED_CONTROL_PAGES and not re.search(r"negative.control", text, re.I):
        p.append("does not mention the negative-control test")
    if route in FAILED_CONTROL_PAGES and not re.search(r"fail", text, re.I):
        p.append("does not say the test failed")
    if re.search(r"\bcandidates?\b", text, re.I) and not re.search(r"candidates? not in our reference list|not in our reference list", text, re.I):
        p.append("mentions candidates without saying they are not in our reference list")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:3100")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--sample-sites", type=int, default=10)
    a = ap.parse_args(argv)
    rx = claims.term_regex(claims.banned_terms(os.path.join(a.root, "data/banned_words.txt")))
    with open(os.path.join(a.root, "docs/E32.txt"), encoding="utf-8") as f:
        e32 = f.read().rstrip("\n")
    import json

    nav = re.findall(r'href: "(/[a-z]*)"', open(os.path.join(a.root, "src/lib/nav.ts"), encoding="utf-8").read())
    routes = ["/"] + [r for r in nav if r != "/"]
    sites = json.load(open(os.path.join(a.root, "public/data/sites.json"), encoding="utf-8"))["sites"]
    slugs = sorted({s["slug"] for s in sites})
    # A spread across the list: both bodies, known and candidate, one place on both bodies.
    pick = slugs[:: max(1, len(slugs) // a.sample_sites)][: a.sample_sites] if a.sample_sites else []
    for s in ("hi-seas-habitat-mauna-loa",):
        if s in slugs and s not in pick:
            pick.append(s)
    problems, n = [], 0
    for r in routes + [f"/sites/{s}" for s in pick]:
        status, page = get(a.base + r)
        n += 1
        if status != 200:
            problems.append((r, f"HTTP {status}"))
            continue
        for x in audit_page(r, page, rx, e32, r.startswith("/sites/")):
            problems.append((r, x))
    status, _ = get(a.base + "/no-such-page")
    if status != 404:
        problems.append(("/no-such-page", f"expected 404, got {status}"))
    if problems:
        print(f"audit_site: {len(problems)} problem(s) over {n} pages")
        for r, x in problems:
            print(f"  {r}: {x}")
        return 1
    print(f"audit_site: ok, {n} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
