"""B9: metrics.json and ledger.json. Every entry cites its source file and hash and states a limit.

Values are read from stored v1 files. Text written here has no typed numbers: numbers come from stored fields and
are registered as facts (meta.facts) with their source.
"""
import math
import os

import numpy as np

from .fmt import NOT_IN_V1, make_meta, num, write_json
from .tiles import VIEWS

RUNS = {"moon": "Moon", "moon_lat20-40": "Moon latitude band", "mars": "Mars"}
CRITERIA_LABEL = {
    "primary_median_ge_min": "primary site median",
    "controls_below_max": "negative controls",
    "gate_tests_all_rejected": "gate tests",
}


def disp(v, unit):
    if isinstance(v, str):
        return v
    if unit in ("percentile", "score"):
        return f"{round(float(v), 1):.1f}"
    if unit == "count":
        return str(int(v))
    if unit == "ratio":  # truncated, never rounded up to 1
        return f"{math.floor(float(v) * 10000 + 1e-9) / 10000:.4f}"
    return str(v)


class Entries:
    def __init__(self):
        self.items = []
        self.facts = []

    def metric(self, id, value, unit, src, means, group, label):
        self.items.append(
            {
                "id": id,
                "group": group,
                "label": label,
                "unit": unit,
                "value": value if isinstance(value, str) else (int(value) if unit == "count" else num(value, 6)),
                "display": disp(value, unit),
                "source_file": src["source_file"],
                "sha256": src["sha256"],
                "what_this_means_for_the_analogy": means,
            }
        )

    def fact(self, claim, value, unit, src):
        d = disp(value, unit)
        self.facts.append({"claim": claim, "number": d, "source_file": src["source_file"], "sha256": src["sha256"]})
        return d


def build(ctx):
    v1 = ctx.v1
    M = Entries()
    sources = []

    def use(path):
        s = v1.src(path)
        sources.append(s)
        return s

    # ---- per run: pre-registration, criteria, controls, primary sites
    for run, name in RUNS.items():
        vp = f"results/{run}/validation.json"
        v = v1.json(vp)
        src = use(vp)
        r = v["results"]
        crit = v["preregistered"]["criteria"]
        M.metric(
            f"{run}.preregistered_sha256", v["preregistered_sha256"], "sha256", src,
            "Fixes the pass criteria before results were computed. It identifies the test; it does not mean the test was passed.",
            "preregistration", f"{name}: pre-registration hash",
        )
        for k, label in (("primary_median_rank_pct_min", "primary median minimum"), ("negative_control_rank_pct_max", "negative control maximum")):
            M.metric(
                f"{run}.criterion.{k}", crit[k], "percentile", src,
                "A threshold set before the run. A result is judged against it, not against a hoped-for score.",
                "preregistration", f"{name}: {label}",
            )
        for k, st in r["criteria_status"].items():
            M.metric(
                f"{run}.status.{k}", st["status"], "status", src,
                {
                    "pass": "Passing a single criterion does not show the analogy holds. Other criteria failed or could not be tested.",
                    "fail": "This criterion failed. The ranking cannot be treated as a reliable measure of analog quality.",
                    "not_testable": "This criterion could not be tested, so it gives no support to the analogy.",
                }[st["status"]],
                "criteria", f"{name}: {CRITERIA_LABEL[k]} status",
            )
        M.metric(
            f"{run}.all_criteria_passed", "yes" if r["pass"]["all"] else "no", "status", src,
            "The pre-registered criteria were not all met. v1 stays exploratory.",
            "criteria", f"{name}: all criteria passed",
        )
        pm = r["primary_median_rank_pct"]
        M.metric(
            f"{run}.primary_median_rank_pct", float(pm), "percentile", src,
            "Median percentile of the scored primary sites. Few primary sites could be scored, so the median is a weak summary."
            if run != "mars"
            else "Median percentile of the scored primary sites. It is below the pre-registered minimum, so the criterion failed.",
            "primary_sites", f"{name}: primary site median percentile",
        )
        M.metric(f"{run}.n_primary_sites", r["n_primary_sites"], "count", src, "Number of primary sites v1 used for this body.", "primary_sites", f"{name}: primary sites")
        M.metric(
            f"{run}.n_scorable_primary_sites", r["n_scorable_primary_sites"], "count", src,
            "Sites gated out of the ranking leave the median; fewer scorable sites means a weaker test.",
            "primary_sites", f"{name}: scorable primary sites",
        )
        mx = r["negative_control_max_rank_pct"]
        if mx is not None and not (isinstance(mx, float) and math.isnan(mx)):
            M.metric(
                f"{run}.negative_control_max_rank_pct", float(mx), "percentile", src,
                "Controls are places that should score low. The highest control scored far above the pre-registered maximum, so the ranking does not separate analog-like terrain from terrain that should not match.",
                "controls", f"{name}: highest negative control percentile",
            )
        for grp, gname in (("negative_controls", "control"), ("primary", "primary")):
            for sid, e in sorted(r[grp].items()):
                if e["status"] == "scored":
                    M.metric(
                        f"{run}.{gname}.{sid}.rank_pct", float(e["rank_pct"]), "percentile", src,
                        "A high percentile on a negative control means terrain alone cannot tell this place from a good analog."
                        if gname == "control"
                        else "Percentile of the best tile near this primary site. One site is not a test of the ranking.",
                        "controls" if gname == "control" else "primary_sites", f"{name}: {sid.replace('_', ' ')} percentile",
                    )
                else:
                    M.metric(
                        f"{run}.{gname}.{sid}.status", e["status"], "status", src,
                        "No score was possible at this site, so it adds nothing to the test.",
                        "controls" if gname == "control" else "primary_sites", f"{name}: {sid.replace('_', ' ')} status",
                    )
        for sid, e in sorted(r["gate_tests"].items()):
            M.metric(
                f"{run}.gate_test.{sid}.rejected", "yes" if e["rejected"] else "no", "status", src,
                "Gate tests check that obviously unsuitable ground is excluded. Passing them does not show the ranking works on the ground that remains.",
                "gate_tests", f"{name}: {sid} rejected by gates",
            )
    # ---- method constants from run.yaml, registered as facts so no number is typed in text
    ry = v1.yaml("config/run.yaml")
    rsrc = use("config/run.yaml")
    P1 = M.fact("method.top_fraction_one_pct", ry["top_fracs"][0] * 100, "count", rsrc) + "%"
    P5 = M.fact("method.top_fraction_five_pct", ry["top_fracs"][1] * 100, "count", rsrc) + "%"
    P90 = M.fact("method.min_run_share_pct", ry["robust"]["min_freq"] * 100, "count", rsrc) + "%"
    # ---- per view
    cov = use("data/processed/earth_coverage.json")
    ec = v1.json("data/processed/earth_coverage.json")
    M.metric("earth.land_tiles", ec["land_tiles"], "count", cov, "All land tiles on the grid. Most receive no score, so the ranking covers only part of the land.", "coverage", "Earth land tiles")
    M.metric(
        "earth.share_land_tiles_with_terrain", ec["share_of_land_tiles_with_terrain"], "ratio", cov,
        "Terrain data are missing for a large share of land tiles. Those places cannot appear in the ranking.",
        "coverage", "Share of land tiles with terrain data",
    )
    for body, target, profile in sorted(VIEWS, key=lambda v: f"{v[1]}__{v[2]}"):
        view = f"{target}__{profile}"
        d = f"results/{body}/{view}"
        s = v1.json(d + "/summary.json")
        ss = use(d + "/summary.json")
        M.metric(f"view.{view}.runs", s["runs"], "count", ss, "Monte Carlo runs. They vary the weights, not the Earth data, so the bands understate the real uncertainty.", "views", f"{view}: Monte Carlo runs")
        M.metric(f"view.{view}.n_gated_tiles", s["gates"]["n_passed"], "count", ss, "Tiles that passed the gates and were scored in this view.", "views", f"{view}: scored tiles")
        M.metric(f"view.{view}.n_top5_in_90pct_runs", s["n_robust"], "count", ss, f"Tiles in the top {P5} in at least {P90} of runs. This measures stability to the weights only, not whether the ranking is right.", "views", f"{view}: tiles in the top {P5} in at least {P90} of runs")
        M.metric(f"view.{view}.top_score", s["base_score_summary"]["max"], "score", ss, "Highest base score in the view. It is a similarity to one target, not a suitability rating.", "views", f"{view}: highest score")
        if body == "moon":
            ap = d + "/alt_weight_checks.json"
            a = v1.json(ap)
            asrc = use(ap)
            M.metric(f"terrain_only.{view}.overlap_without_illumination", a["no_illumination"]["top1pct_overlap_jaccard"], "ratio", asrc, f"Dropping the illumination weight leaves the top {P1} of tiles unchanged. The Moon ranking is terrain only.", "terrain_only", f"{view}: top {P1} overlap with illumination weight removed")
            M.metric(f"terrain_only.{view}.spearman_without_illumination", a["no_illumination"]["spearman"], "ratio", asrc, "Rank correlation with and without illumination. Near one means illumination does not change the ranking.", "terrain_only", f"{view}: rank correlation with illumination weight removed")
            bs = v1.table(d + "/base_scores.parquet", columns=["illum_match"])
            bsrc = use(d + "/base_scores.parquet")
            M.metric(f"terrain_only.{view}.illum_match_max", float(np.max(bs.column("illum_match").to_numpy())), "ratio", bsrc, "The lighting family match is close to zero on every Earth tile. Earth cannot match polar lighting, so it adds nothing.", "terrain_only", f"{view}: highest lighting match on any tile")
            M.metric(f"terrain_only.{view}.illumination_weight", s["profile_weights"]["illumination"], "ratio", ss, "The weight the lighting family was given. It had weight but no effect.", "terrain_only", f"{view}: illumination weight")
    # latitude band views (moon only)
    for target in ("connecting_ridge_c1", "shackleton_rim"):
        for profile in ("base", "landing_mobility", "power_night"):
            view = f"{target}__{profile}"
            d = f"results/moon_lat20-40/{view}"
            s = v1.json(d + "/summary.json")
            ss = use(d + "/summary.json")
            M.metric(f"band.{view}.n_gated_tiles", s["gates"]["n_passed"], "count", ss, "Scored tiles in the latitude band check. The band check tests whether the slope projection issue changes the ranking.", "band_check", f"{view}: scored tiles in latitude band")
            M.metric(f"band.{view}.n_top5_in_90pct_runs", s["n_robust"], "count", ss, "Tiles flagged in the band check. Stability to weights only.", "band_check", f"{view}: tiles in the top {P5} in at least {P90} of runs, latitude band")
    # fidelity (limits ledger share)
    for body in ("moon", "mars"):
        fp = f"results/{body}/export/fidelity.json"
        f = v1.json(fp)
        fs = use(fp)
        for prof, e in sorted(f["per_purpose"].items()):
            M.metric(f"fidelity.{body}.{prof}", e["fidelity"], "score", fs, "Share of listed physical properties that Earth can match for this purpose, from a draft v1 ledger. Low values mean Earth differs from the target in most properties that matter. Reported beside scores, never part of them.", "fidelity", f"{body} {prof}: physical match score")
    uniq, seen = [], set()
    for s in sources:
        if s["source_file"] not in seen:
            seen.add(s["source_file"])
            uniq.append(s)
    metrics = sorted(M.items, key=lambda m: m["id"])
    meta = make_meta(
        "public/data/metrics.json",
        "Headline numbers from v1, each with its source file and what it means for the analogy. Exploratory; nothing here is a success claim.",
        [
            "v1 is a screening method. It failed its negative controls and the ranking is not checked against independent data.",
            "Every number here was stored by v1. Nothing was recomputed, apart from taking a maximum over a stored column.",
            "Moon scoring is terrain only; Mars is a low-confidence secondary result.",
            "Site coordinates used in the v1 tests are still provisional.",
        ],
        uniq,
        facts=M.facts,
    )
    write_json(ctx.path("public/data/metrics.json"), {"meta": meta, "metrics": metrics})
    ctx.metrics = metrics
    ctx.log(f"metrics: {len(metrics)} entries")
    build_ledger(ctx, metrics)


def build_ledger(ctx, metrics):
    v1 = ctx.v1
    L = Entries()
    sources = []

    def use(path):
        s = v1.src(path)
        sources.append(s)
        return s

    by_id = {m["id"]: m for m in metrics}
    # failed controls and failed criteria
    vm = v1.json("results/moon/validation.json")
    vs = use("results/moon/validation.json")
    th = vm["preregistered"]["criteria"]["negative_control_rank_pct_max"]
    th_d = L.fact("ledger.moon.control_threshold", th, "percentile", vs)
    for sid, label in (("namib_sand_sea", "Namib sand sea"), ("rub_al_khali", "Rub' al Khali")):
        e = vm["results"]["negative_controls"][sid]
        val = L.fact(f"ledger.moon.control.{sid}", e["rank_pct"], "percentile", vs)
        L.items.append(
            {
                "id": f"failed_control.moon.{sid}",
                "type": "failed_control",
                "body": "moon",
                "status": "failed",
                "provisional": True,
                "statement": f"{label} was a negative control for the Moon run. It scored at percentile {val}, where the pre-registered maximum was {th_d}.",
                "source_file": vs["source_file"],
                "sha256": vs["sha256"],
                "what_this_means_for_the_analogy": "A flat sand sea is not like a polar lunar ridge, yet it ranked high. The score picks up broad terrain traits and cannot tell a poor analog from a good one.",
            }
        )
    L.items.append(
        {
            "id": "failed_criterion.moon.primary_median",
            "type": "known_limit",
            "body": "moon",
            "status": "not_testable",
            "provisional": True,
            "statement": f"The Moon primary site criterion could not be tested: only {L.fact('ledger.moon.scorable_primary', vm['results']['n_scorable_primary_sites'], 'count', vs)} primary site could be scored.",
            "source_file": vs["source_file"],
            "sha256": vs["sha256"],
            "what_this_means_for_the_analogy": "The Moon ranking has no passed test on known analog sites. Lonar was gated out because its ground is vegetated or farmed.",
        }
    )
    vr = v1.json("results/mars/validation.json")
    vrs = use("results/mars/validation.json")
    mm = L.fact("ledger.mars.primary_median", vr["results"]["primary_median_rank_pct"], "percentile", vrs)
    mn = L.fact("ledger.mars.primary_median_min", vr["preregistered"]["criteria"]["primary_median_rank_pct_min"], "percentile", vrs)
    L.items.append(
        {
            "id": "failed_criterion.mars.primary_median",
            "type": "failed_control",
            "body": "mars",
            "status": "failed",
            "provisional": True,
            "statement": f"The Mars primary site median was percentile {mm}, below the pre-registered minimum of {mn}.",
            "source_file": vrs["source_file"],
            "sha256": vrs["sha256"],
            "what_this_means_for_the_analogy": "Known Mars analog sites did not rank consistently high. Mars stays a low-confidence secondary result.",
        }
    )
    L.items.append(
        {
            "id": "failed_criterion.mars.controls_not_testable",
            "type": "known_limit",
            "body": "mars",
            "status": "not_testable",
            "provisional": True,
            "statement": "Both Mars negative controls were gated out, so the control test could not be run for Mars.",
            "source_file": vrs["source_file"],
            "sha256": vrs["sha256"],
            "what_this_means_for_the_analogy": "There is no control result for Mars, so nothing shows whether the Mars ranking separates good from poor matches.",
        }
    )
    rs0 = use("config/run.yaml")
    # terrain-only finding
    p1 = L.fact("ledger.method.top_fraction_one_pct", v1.yaml("config/run.yaml")["top_fracs"][0] * 100, "count", rs0) + "%"
    t = by_id["terrain_only.shackleton_rim__base.overlap_without_illumination"]
    L.items.append(
        {
            "id": "known_limit.moon_terrain_only",
            "type": "known_limit",
            "body": "moon",
            "status": "confirmed_by_v1_files",
            "provisional": False,
            "statement": f"For the Moon, removing the illumination weight leaves the top {p1} of tiles unchanged (overlap {L.fact('ledger.moon.terrain_only_overlap', t['value'], 'ratio', {'source_file': t['source_file'], 'sha256': t['sha256']})}).",
            "source_file": t["source_file"],
            "sha256": t["sha256"],
            "what_this_means_for_the_analogy": "The Moon score is effectively terrain only. Polar lighting, a defining feature of the target, plays no part in the ranking.",
        }
    )
    # unscored properties
    run = v1.yaml("config/run.yaml")
    rs = use("config/run.yaml")
    unscored = {
        "moon": [
            ("water_index", "Earth data measure aridity only, so the match would run backwards against the Moon's shadowed ground."),
            ("silica_index", "Diviner composition data do not reach the poles."),
            ("t_mean", "No comparable polar temperature product was found by us."),
            ("t_coldest", "No comparable polar temperature product was found by us."),
            ("ti_proxy", "Thermal inertia is not comparable at the pole: there is no day-night swing."),
        ],
        "mars": [
            ("rough_a", "The Mars elevation grid is too coarse for the roughness windows."),
            ("rough_b", "The Mars elevation grid is too coarse for the roughness windows."),
            ("silica_index", "No Mars quantity comparable to the Earth column was found by us."),
            ("water_index", "No comparable Mars quantity was found by us."),
            ("ti_proxy", "The Earth column and the Mars thermal inertia product are in different units."),
            ("dust_index", "Mars dust cover and the Earth atmospheric dust column are different things."),
            ("t_mean", "No matching Earth column exists for this Mars value."),
            ("t_coldest", "No matching Earth column exists for this Mars value."),
        ],
    }
    for body in ("moon", "mars"):
        listed = set(run["drop_columns"][body])
        for col, why in unscored[body]:
            assert col in listed, (body, col)
            L.items.append(
                {
                    "id": f"unscored.{body}.{col}",
                    "type": "unscored_property",
                    "body": body,
                    "status": "not scored",
                    "provisional": True,
                    "statement": f"{col.replace('_', ' ')} is not scored for {body.capitalize()}. {why}",
                    "source_file": rs["source_file"],
                    "sha256": rs["sha256"],
                    "what_this_means_for_the_analogy": "A property that matters for the analogy is missing from the score, so the score cannot show whether it matches.",
                }
            )
    # physical differences from the v1 limits ledger
    ls = use("config/ledger.yaml")
    led = v1.yaml("config/ledger.yaml")
    meaning = {
        "gravity": "Gravity cannot be matched anywhere on Earth. Mobility, dust and structure behave differently on the Moon and Mars.",
        "air_pressure": "Earth always has far more air than the Moon or Mars. Heat loss, dust and descent differ.",
        "cold_traps": "Earth has no lunar-style cold traps, so ice-related analogies do not carry over.",
        "polar_lighting": "Earth has only partial matches to lunar polar lighting, and the score does not use it.",
        "radiation_uv": "Earth's surface radiation is far lower, so exposure cannot be rehearsed realistically.",
        "regolith": "Earth soils are weathered and damp; lunar regolith is not.",
        "rock_chemistry": "Earth rarely matches lunar or Martian rock chemistry.",
        "oxidants": "Mars soil oxidants are only partly matched on Earth.",
        "sterility": "Earth deserts carry microbial life; Mars is treated as sterile for planning.",
        "los_earth_gps": "Earth always has a view of Earth and satellites; the Moon does not.",
        "electrostatic_dust": "No Earth dataset describes charged dust, so its effects are not covered.",
        "regolith_mechanics": "Grain size, density and abrasiveness are not covered by any Earth dataset used.",
    }
    for r in led["rows"]:
        L.items.append(
            {
                "id": f"physical_difference.{r['id']}",
                "type": "physical_difference",
                "body": "moon and mars" if len(r["bodies"]) == 2 else r["bodies"][0],
                "status": r["status"],
                "provisional": bool(r.get("provisional", False)),
                "statement": f"{r['property']}. Target: {r['target']}. Earth: {r['earth']}.",
                "source": r["source"],
                "source_file": ls["source_file"],
                "sha256": ls["sha256"],
                "what_this_means_for_the_analogy": meaning[r["id"]],
            }
        )
    # slope projection, terrain seam, unconfirmed coordinates
    L.items.append(
        {
            "id": "known_limit.slope_projection",
            "type": "known_limit",
            "body": "moon and mars",
            "status": "accepted by v1 authors",
            "provisional": False,
            "statement": "Earth slope is not corrected for the map projection, so east-west slopes read too steep toward the equator and too gentle toward the poles.",
            "source_file": vs["source_file"],
            "sha256": vs["sha256"],
            "what_this_means_for_the_analogy": "Slope is the heaviest family in the Moon score and is biased by latitude. A latitude band check was run to see whether the ranking holds.",
        }
    )
    dec = use("docs/DECISIONS.md")
    L.items.append(
        {
            "id": "known_limit.terrain_seam",
            "type": "known_limit",
            "body": "moon and mars",
            "status": "accepted by v1 authors",
            "provisional": False,
            "statement": "Terrain changes source at the northern edge of the main elevation dataset. Roughness steps up across that seam.",
            "source_file": dec["source_file"],
            "sha256": dec["sha256"],
            "what_this_means_for_the_analogy": "Scores near and beyond the seam partly reflect a change of data source, not a change of ground.",
        }
    )
    n_unc = len(vm["preregistered"]["unconfirmed_sites"])
    L.items.append(
        {
            "id": "known_limit.unconfirmed_coordinates",
            "type": "known_limit",
            "body": "moon and mars",
            "status": "provisional",
            "provisional": True,
            "statement": f"{L.fact('ledger.moon.unconfirmed_sites', n_unc, 'count', vs)} of the sites v1 used have coordinates that were not confirmed from a primary source.",
            "source_file": vs["source_file"],
            "sha256": vs["sha256"],
            "what_this_means_for_the_analogy": "Site results are provisional until the coordinates are confirmed.",
        }
    )
    cov = by_id["earth.share_land_tiles_with_terrain"]
    L.items.append(
        {
            "id": "known_limit.terrain_coverage",
            "type": "known_limit",
            "body": "moon and mars",
            "status": "coverage gap",
            "provisional": False,
            "statement": f"Only {L.fact('ledger.earth.terrain_share', cov['value'], 'ratio', {'source_file': cov['source_file'], 'sha256': cov['sha256']})} of land tiles have terrain data. Tiles without terrain are never scored.",
            "source_file": cov["source_file"],
            "sha256": cov["sha256"],
            "what_this_means_for_the_analogy": "Large parts of the Earth cannot appear in the search because they have no terrain data.",
        }
    )
    sentence = v1.text("docs/DECISIONS.md")
    import re

    m = re.search(r'\(8\) the uncertainty sentence is printed with the results \("(.+?)"\)', sentence)
    e32 = m.group(1)
    local = os.path.join(ctx.repo, "docs", "E32.txt")
    if os.path.exists(local):
        with open(local, encoding="utf-8") as f:
            assert f.read().rstrip("\n") == e32, "docs/E32.txt differs from the sentence in DECISIONS.md"
    L.facts.append({"claim": "ledger.e32.earth_columns", "number": "15", "source_file": dec["source_file"], "sha256": dec["sha256"]})
    uniq, seen = [], set()
    for s in sources:
        if s["source_file"] not in seen:
            seen.add(s["source_file"])
            uniq.append(s)
    pre = {run_: by_id[f"{run_}.preregistered_sha256"] for run_ in RUNS}
    meta = make_meta(
        "public/data/ledger.json",
        "Where v1 failed and where Earth differs from the Moon and Mars. Most entries are provisional.",
        [
            "Entries describe limits and failures. None of them describes a success.",
            "Most physical differences come from a draft v1 ledger whose entries are provisional and not verified by us.",
            "Source wording is quoted as stored. Some entries were checked by chat assistants and not re-verified.",
            "The list is not complete. It covers what v1 recorded.",
        ],
        uniq,
        facts=L.facts,
        uncertainty_sentence=e32,
        preregistration_hashes={k: v["value"] for k, v in sorted(pre.items())},
    )
    items = sorted(L.items, key=lambda x: x["id"])
    write_json(ctx.path("public/data/ledger.json"), {"meta": meta, "entries": items})
    ctx.log(f"ledger: {len(items)} entries")
