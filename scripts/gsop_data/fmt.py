"""Deterministic output helpers: sorted keys, fixed number formatting, no timestamps."""
import hashlib
import json
import math
import os

NOT_IN_V1 = "not in v1 outputs"


def num(x, nd=4):
    """Round to a fixed number of decimals; return int when nd is 0. No negative zero."""
    x = float(x)
    if math.isnan(x) or math.isinf(x):
        raise ValueError("non-finite number in output")
    if nd == 0:
        return int(round(x))
    r = round(x, nd)
    return 0.0 if r == 0 else r


def dumps(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n"


def write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def write_text(path, text):
    write_bytes(path, text.encode("utf-8"))


def write_json(path, obj):
    write_text(path, dumps(obj))


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def make_meta(file, label, limits, sources, facts=None, **extra):
    """Header object for every JSON data file. `sources` is a list of {source_file, sha256}."""
    m = {
        "schema_version": 1,
        "file": file,
        "label": label,
        "limits": list(limits),
        "sources": sorted(sources, key=lambda s: s["source_file"]),
    }
    if facts:
        m["facts"] = sorted(facts, key=lambda f: f["claim"])
    m.update(extra)
    return m
