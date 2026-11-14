"""controls.json: the negative controls v1 used, with coordinates and their stored result per run (for the Honest Map).

Values are read from results/<run>/validation.json. Nothing is computed.
"""
from .fmt import make_meta, num, write_json

RUNS = ["moon", "mars"]
LABEL = {
    "amazon_basin": "Amazon basin",
    "congo_basin": "Congo basin",
    "rub_al_khali": "Rub' al Khali",
    "namib_sand_sea": "Namib sand sea",
}
LIMITS = [
    "Negative controls are places that should score low. v1 used them to test whether the ranking separates good matches from poor ones.",
    "Two controls scored far above the pre-registered maximum on the Moon run, so the ranking failed this test.",
    "Controls that were gated out have no score. That does not count as a pass.",
    "Control coordinates are design choices, and most are not confirmed from a primary source.",
    "A control score is a percentile among scored tiles. It is a lookup of a stored v1 value.",
]


def build(ctx):
    v1 = ctx.v1
    sources, controls = [], {}
    for run in RUNS:
        path = f"results/{run}/validation.json"
        sources.append(v1.src(path))
        for cid, e in sorted(v1.json(path)["results"]["negative_controls"].items()):
            c = controls.setdefault(
                cid,
                {"id": cid, "label": LABEL[cid], "lat": num(e["lat"], 4), "lon": num(e["lon"], 4), "coordinates_confirmed": bool(e["confirmed"]), "runs": {}},
            )
            r = {"status": e["status"], "source_file": sources[-1]["source_file"], "sha256": sources[-1]["sha256"]}
            if e["status"] == "scored":
                r["rank_pct"] = num(e["rank_pct"], 6)
            else:
                r["reason"] = e.get("first_gate_reason") or e["status"]
            c["runs"][run] = r
    meta = make_meta(
        "public/data/controls.json",
        "Negative controls used by v1, with the stored result for each run. Descriptive, not a success claim.",
        LIMITS,
        sources,
    )
    write_json(ctx.path("public/data/controls.json"), {"meta": meta, "controls": [controls[k] for k in sorted(controls)]})
    ctx.log(f"controls: {len(controls)}")
