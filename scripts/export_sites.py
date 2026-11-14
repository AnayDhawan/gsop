#!/usr/bin/env python3
"""Export public.sites from Supabase to data/reference/sites_export.json (B13). Standard library plus the system curl.

    python3 scripts/export_sites.py

Reads SUPABASE_URL and SUPABASE_ANON_KEY (or SUPABASE_SERVICE_KEY) from the environment or a local .env. The table is
public-read, so the anon key is enough and is preferred. Keys are never printed, never written to a file, and are passed
to curl through stdin so they do not show in a process list. The deployed site never calls Supabase: this runs at build
time and the snapshot is committed, so a clean clone rebuilds the same files without any key.

The snapshot holds every column except id, notes and created_at, sorted by body and slug. The LLM score columns are not
in this table (they live only in sites_llm_raw, which the anon key cannot read).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gsop_data.fmt import dumps  # noqa: E402

REPO = os.path.dirname(HERE)
OUT = "data/reference/sites_export.json"
DROP = {"id", "notes", "created_at"}
SCORE_LIKE = ("similarity", "monte", "rank", "passes", "nearest", "scored", "gate")


def load_env(repo=REPO):
    env = {k: os.environ[k] for k in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_KEY") if os.environ.get(k)}
    path = os.path.join(repo, ".env")
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    k = k.strip()
                    if k in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_KEY") and k not in env and v.strip():
                        env[k] = v.strip()
    return env


def have_keys(repo=REPO):
    e = load_env(repo)
    return bool(e.get("SUPABASE_URL") and (e.get("SUPABASE_ANON_KEY") or e.get("SUPABASE_SERVICE_KEY")))


def fetch(env, path):
    key = env.get("SUPABASE_ANON_KEY") or env["SUPABASE_SERVICE_KEY"]
    url = env["SUPABASE_URL"].rstrip("/") + "/rest/v1/" + path
    cfg = f'url = "{url}"\nheader = "apikey: {key}"\nheader = "Authorization: Bearer {key}"\nsilent\nshow-error\nfail\nmax-time = 60\n'
    r = subprocess.run(["curl", "--config", "-"], input=cfg, capture_output=True, text=True)
    if r.returncode != 0:
        msg = r.stderr.strip().replace(key, "***").replace(env["SUPABASE_URL"], "<url>")
        raise RuntimeError(f"Supabase request failed: {msg[:200]}")
    return json.loads(r.stdout)


def export(repo=REPO):
    env = load_env(repo)
    if not (env.get("SUPABASE_URL") and (env.get("SUPABASE_ANON_KEY") or env.get("SUPABASE_SERVICE_KEY"))):
        raise RuntimeError("no Supabase keys set")
    rows = fetch(env, "sites?select=*&limit=5000")
    if not rows:
        raise RuntimeError("public.sites returned no rows; refusing to overwrite the snapshot")
    cols = sorted(c for c in rows[0] if c not in DROP)
    bad = [c for c in cols if any(s in c.lower() for s in SCORE_LIKE)]
    if bad:
        raise RuntimeError(f"score-like columns in public.sites, refusing to export: {bad}")
    out = [{c: r.get(c) for c in cols} for r in rows]
    out.sort(key=lambda r: (r["body"], r["slug"]))
    doc = {"source": "Supabase table public.sites, exported by scripts/export_sites.py", "excluded_columns": sorted(DROP), "columns": cols, "rows": out}
    path = os.path.join(repo, OUT)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(dumps(doc))
    return len(out)


if __name__ == "__main__":
    try:
        n = export()
    except RuntimeError as e:
        sys.exit(f"export_sites: {e}")
    print(f"export_sites: {n} rows written to {OUT}")
