"""B16: intake of the optional v2 sim outputs. Standard library only.

Inputs live in data/v2/ (copied by scripts/sync_v2.py, hashes in data/v2/SOURCES.csv). Every input is optional.
The build works with all of them absent, with some present, and with all present. A missing input is reported as
missing and nothing is filled in. Numbers are never computed here: values are read from the files and shown with a
fixed display rule.

Writes:
  public/data/v2.json               status, input list with hashes, pre-registration check, thermal references
  public/data/site_measurements.json  only when data/evidence/site_measurements.csv is present
  public/img/sites/*                only when image chips are present
"""
import csv
import hashlib
import io
import json
import os
import re
import shutil
from decimal import ROUND_HALF_EVEN, Decimal

from .fmt import NOT_IN_V1, make_meta, write_json

V2_DIR = "data/v2"
RUN_NOT_COMPLETED = "v2 run not completed"

# Every file the site can use. Order is the order they are listed in v2.json.
EXPECTED = [
    "runs/v2/metrics.json",
    "runs/v2/ledger.json",
    "runs/v2/claims_v2.csv",
    "runs/v2/claims_c.csv",
    "data/reference/thermal_refs.csv",
    "data/reference/thermal_refs_files.csv",
    "data/evidence/site_measurements.csv",
    "data/evidence/ledger_c.json",
    "public/img/sites/credits.json",
    "docs/refs_limits.md",
    "docs/evidence_limits.md",
    "docs/data_resources.md",
]

V2_LIMITS = [
    "The v2 run adds measured reference layers and site measurements. It is optional: where a file is missing the site says so and shows nothing in its place.",
    "A pre-registration hash identifies a plan written before results were computed. It does not mean the plan was met.",
    "Thermal reference values are compared only by rank inside each body's own set, never by absolute value, because Earth cannot reach polar lunar temperatures.",
    "A layer marked not covered has no value in this run. It is not a zero.",
    "Reference layers are context for the Moon and Mars targets. They are not scores of Earth places.",
]


def sig(x, n=4):
    """Fixed display string with n significant digits, no exponent. Deterministic."""
    d = Decimal(repr(float(x)))
    if d == 0:
        return "0"
    q = Decimal(1).scaleb(d.adjusted() - n + 1)
    r = d.quantize(q, rounding=ROUND_HALF_EVEN)
    s = format(r, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".") if r == r.to_integral_value() else s
    return "0" if s in ("-0", "") else s


def is_number(s):
    try:
        float(s)
        return s.strip() != "" and s.strip().lower() not in ("nan", "inf", "-inf")
    except ValueError:
        return False


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def read(base, rel):
    p = os.path.join(base, rel)
    if not os.path.isfile(p):
        return None
    with open(p, "rb") as f:
        return f.read()


def lf(b):
    return b.replace(b"\r\n", b"\n")


def recorded_hash(sha_text, doc_name):
    """The sha256 a prereg_*.sha256 file records for the document. Comment lines are ignored. A line counts when it
    names the document or starts with 'sha256'. The last such line wins."""
    found = None
    for line in sha_text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        m = re.search(r"\b([0-9a-f]{64})\b", line)
        if m and (doc_name in line or line.strip().lower().startswith("sha256")):
            found = m.group(1)
    return found


def preregistrations(base):
    out = []
    d = os.path.join(base, "runs/v2")
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        m = re.fullmatch(r"PREREG_([A-Za-z0-9]+)\.md", f)
        if not m:
            continue
        key = m.group(1)
        doc = read(base, f"runs/v2/{f}")
        actual = sha256_bytes(lf(doc))
        sha_file = read(base, f"runs/v2/prereg_{key.lower()}.sha256")
        rec = recorded_hash(sha_file.decode("utf-8"), f) if sha_file is not None else None
        dev = f"PREREG_{key}_DEVIATIONS.md"
        title = next((l.lstrip("# ").strip() for l in doc.decode("utf-8").splitlines() if l.startswith("#")), f)
        out.append(
            {
                "id": key,
                "file": f"runs/v2/{f}",
                "title": title,
                "actual_sha256": actual,
                "recorded_sha256": rec if rec else NOT_IN_V1,
                "matches": (rec == actual) if rec else None,
                "deviations_file": f"runs/v2/{dev}" if read(base, f"runs/v2/{dev}") is not None else None,
            }
        )
    return out


def thermal(base):
    raw = read(base, "data/reference/thermal_refs.csv")
    if raw is None:
        return None
    rows = []
    for r in csv.DictReader(io.StringIO(raw.decode("utf-8"), newline="")):
        v = r["value"].strip()
        row = {
            "site": r["site_slug"],
            "body": r["body"],
            "layer": r["layer"],
            "stat": r["stat"],
            "units": r["units"],
            "product": r["product"],
            "version": r["version"],
            "source_url": r["source_url"],
            "source_sha256": r["sha256"],
        }
        if v == "":
            row["status"] = "not_covered" if r["stat"] == "not_covered" else "empty"
            row["value"] = None
            row["display"] = None
        elif is_number(v):
            row["status"] = "value"
            row["value"] = float(v)
            row["display"] = str(int(float(v))) if r["units"] == "count" and float(v) == int(float(v)) else sig(v)
        else:
            row["status"] = "label"
            row["value"] = None
            row["display"] = None
            row["text"] = v
        rows.append(row)
    files = []
    fr = read(base, "data/reference/thermal_refs_files.csv")
    if fr is not None:
        for r in csv.DictReader(io.StringIO(fr.decode("utf-8"), newline="")):
            files.append({"file": r["file"], "url": r["url"], "sha256": r["sha256"], "doi": r["doi"]})
    return {"rows": rows, "files": files, "sha256": sha256_bytes(raw), "path": "data/v2/data/reference/thermal_refs.csv"}


REQUIRED_MEASUREMENT_COLUMNS = ["site_name", "body", "list", "radius_km", "coord_flag", "dataset", "variable", "stat", "value", "units", "n_pixels", "product_id", "version", "doi_or_url", "date_range"]


def measurements(base, sites):
    """site_measurements.csv in the layout fixed by runs/v2/PREREG_C.md section 4. Nulls stay in as nulls with their note."""
    raw = read(base, "data/evidence/site_measurements.csv")
    if raw is None:
        return None
    rd = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    missing = [c for c in REQUIRED_MEASUREMENT_COLUMNS if c not in (rd.fieldnames or [])]
    if missing:
        raise SystemExit(f"site_measurements.csv is missing required columns: {missing}")
    by_name = {(s["name"].strip().lower(), s["body"].lower()): s["id"] for s in sites}
    out, unmatched = {}, set()
    for r in rd:
        key = (r["site_name"].strip().lower(), r["body"].strip().lower())
        sid = by_name.get(key)
        if sid is None:
            unmatched.add(r["site_name"])
            continue
        v = r["value"].strip()
        m = {
            "dataset": r["dataset"],
            "variable": r["variable"],
            "stat": r["stat"],
            "radius_km": r["radius_km"],
            "units": r["units"],
            "product_id": r["product_id"],
            "version": r["version"],
            "doi_or_url": r["doi_or_url"],
            "date_range": r["date_range"],
            "coord_flag": r["coord_flag"],
            "page_ok": (r.get("page_ok") or "1").strip() == "1",
            "note": (r.get("note") or "").strip(),
            "value": float(v) if is_number(v) else None,
            "display": sig(v, 3) if is_number(v) else None,
        }
        out.setdefault(sid, []).append(m)
    return {"by_site": {k: out[k] for k in sorted(out)}, "unmatched_site_names": sorted(unmatched), "sha256": sha256_bytes(raw), "path": "data/v2/data/evidence/site_measurements.csv"}


def copy_chips(base, root):
    src = os.path.join(base, "public/img/sites")
    dst = os.path.join(root, "public/img/sites")
    if not os.path.isdir(src):
        if os.path.isdir(dst):
            shutil.rmtree(dst)  # chips from an earlier run must not outlive their input
        return []
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst, exist_ok=True)
    names = sorted(f for f in os.listdir(src) if f.endswith((".jpg", ".json")))
    for f in names:
        shutil.copyfile(os.path.join(src, f), os.path.join(dst, f))
    return names


LIMITS_DOCS = [("refs_limits", "docs/refs_limits.md"), ("evidence_limits", "docs/evidence_limits.md"), ("data_resources", "docs/data_resources.md")]


def md_blocks(text):
    """The small markdown subset these documents use: headings, bullets nested by two spaces, paragraphs, inline code.

    Returns (title, blocks). Each block is {type: h2 | h3 | h4 | li | p, level, text}. The first level-one heading is the title.
    """
    title, blocks, para = None, [], []

    def flush():
        if para:
            blocks.append({"type": "p", "level": 0, "text": " ".join(s.strip() for s in para)})
            para.clear()

    for line in text.splitlines():
        if not line.strip():
            flush()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            flush()
            if len(m.group(1)) == 1 and title is None:
                title = m.group(2).strip()
            else:
                blocks.append({"type": f"h{max(len(m.group(1)), 2)}", "level": 0, "text": m.group(2).strip()})
            continue
        m = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if m:
            flush()
            blocks.append({"type": "li", "level": len(m.group(1)) // 2, "text": m.group(2).strip()})
            continue
        if blocks and blocks[-1]["type"] == "li" and line.startswith("  "):
            blocks[-1]["text"] += " " + line.strip()  # a wrapped bullet
            continue
        para.append(line)
    flush()
    return title, blocks


def limits_docs(base):
    out = []
    for key, rel in LIMITS_DOCS:
        b = read(base, rel)
        if b is None:
            continue
        title, blocks = md_blocks(b.decode("utf-8"))
        out.append({"id": key, "path": f"{V2_DIR}/{rel}", "sha256": sha256_bytes(b), "title": title or key, "blocks": blocks})
    return out


def build(ctx):
    base = os.path.join(ctx.repo, V2_DIR)
    inputs = []
    for rel in EXPECTED:
        b = read(base, rel)
        inputs.append({"path": rel, "present": b is not None, **({"bytes": len(b), "sha256": sha256_bytes(b)} if b is not None else {})})
    pre = preregistrations(base)
    th = thermal(base)
    docs = limits_docs(base)
    meas = measurements(base, ctx.sites)
    chips = copy_chips(base, ctx.root)
    done = all(i["present"] for i in inputs if i["path"] in ("runs/v2/metrics.json", "runs/v2/ledger.json"))
    sources = [{"source_file": f"{V2_DIR}/{i['path']}", "sha256": i["sha256"]} for i in inputs if i["present"]]
    sources += [{"source_file": f"{V2_DIR}/{p['file']}", "sha256": p["actual_sha256"]} for p in pre]
    sources = list({s["source_file"]: s for s in sources}.values())
    meta = make_meta(
        "public/data/v2.json",
        "Optional v2 sim outputs: status, input hashes, pre-registrations and thermal reference layers.",
        V2_LIMITS,
        sources,
    )
    doc = {
        "meta": meta,
        "run_completed": done,
        "status_text": "v2 run complete" if done else RUN_NOT_COMPLETED,
        "inputs": inputs,
        "preregistrations": pre,
        "thermal_refs": th,
        "limits_docs": docs,
        "has_site_measurements": meas is not None,
        "n_chip_files": len([c for c in chips if c.endswith(".jpg")]),
    }
    write_json(os.path.join(ctx.root, "public/data/v2.json"), doc)
    sm_path = os.path.join(ctx.root, "public/data/site_measurements.json")
    if meas is not None:
        m = make_meta(
            "public/data/site_measurements.json",
            "Measured evidence at site coordinates from open Earth data, in the layout fixed before the run. Nulls are shown with their note.",
            [
                "Each value is a summary over a circle around the listed coordinates, not a measurement of the site itself.",
                "Coordinates marked approximate: only the larger radius is shown on pages.",
                "A null means the product had no valid data there. It is not a zero.",
                "Measurements describe the place, not whether it is a good analog.",
            ],
            [{"source_file": meas["path"], "sha256": meas["sha256"]}],
        )
        write_json(sm_path, {"meta": m, "by_site": meas["by_site"], "unmatched_site_names": meas["unmatched_site_names"]})
    elif os.path.exists(sm_path):
        os.remove(sm_path)  # a stale file from an earlier run must not outlive its input
    ctx.v2 = doc
    ctx.log(f"v2: {sum(i['present'] for i in inputs)} of {len(inputs)} optional inputs present, {len(pre)} pre-registrations, {'thermal refs' if th else 'no thermal refs'}, {'measurements' if meas else 'no measurements'}")
