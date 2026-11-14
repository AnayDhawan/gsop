"""Tests for the optional v2 intake (B16). Standard library only: python3 -m unittest discover -s scripts/tests"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from gsop_data import claims, v2  # noqa: E402


class Ctx:
    def __init__(self, repo, root, sites):
        self.repo, self.root, self.sites, self.logged = repo, root, sites, []

    def log(self, m):
        self.logged.append(m)


SITES = [{"id": "askja-caldera-moon", "name": "Askja caldera", "body": "Moon"}, {"id": "dallol-mars", "name": "Dallol", "body": "Mars"}]
THERMAL = (
    "site_slug,body,layer,stat,value,units,product,version,source_url,sha256\n"
    "shackleton_rim,moon,prp_temp_max,min,76.75,K,Diviner PRP,v1,http://x,abc\n"
    "shackleton_rim,moon,prp_triangles,n,613,count,Diviner PRP,v1,http://x,abc\n"
    "jezero,mars,surface_temperature,not_covered,,,none,,,\n"
    "jezero,mars,tes_ti_day,primary_basis,all,label,TES,v1,http://y,def\n"
)
MEAS_HEAD = "site_name,body,list,radius_km,coord_flag,dataset,variable,stat,value,units,n_pixels,product_id,version,doi_or_url,date_range,page_ok,note\n"
MEAS = (
    MEAS_HEAD
    + "Askja caldera,Moon,known,10,ok,cop_dem,elevation,mean,1100.4,m,500,COP,2024_1,http://c,2010-2020,1,\n"
    + "Askja caldera,Moon,known,2,approx,cop_dem,elevation,mean,1099.9,m,20,COP,2024_1,http://c,2010-2020,0,\n"
    + "Askja caldera,Moon,known,10,ok,s1,vv,median,,dB,0,S1,none,http://s,2024,1,no_images\n"
    + "Nowhere,Moon,known,10,ok,cop_dem,elevation,mean,5,m,5,COP,2024_1,http://c,2010-2020,1,\n"
)


def write(base, rel, data):
    p = os.path.join(base, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode())


def full_fixture(repo):
    b = os.path.join(repo, "data/v2")
    doc_b = b"# PREREG B\nbody\n"
    doc_c = b"# PREREG C\nbody\n"
    write(b, "runs/v2/metrics.json", "{}")
    write(b, "runs/v2/ledger.json", "{}")
    write(b, "runs/v2/PREREG_B.md", doc_b)
    write(b, "runs/v2/prereg_b.sha256", f"# older entry\n{'0' * 64}  runs/v2/PREREG_B.md\n{hashlib.sha256(doc_b).hexdigest()}  runs/v2/PREREG_B.md\n")
    write(b, "runs/v2/PREREG_B_DEVIATIONS.md", "# deviations\n")
    write(b, "runs/v2/PREREG_C.md", doc_c)
    write(b, "runs/v2/prereg_c.sha256", f"sha256_lf: {'1' * 64}\n")  # does not match
    write(b, "data/reference/thermal_refs.csv", THERMAL)
    write(b, "data/reference/thermal_refs_files.csv", "file,url,bytes,sha256,date_pulled_ist,doi\nf.tab,http://f,1,aa,2026,10.1/x\n")
    write(b, "data/evidence/site_measurements.csv", MEAS)
    write(b, "public/img/sites/askja-caldera.jpg", b"\xff\xd8jpeg")
    write(b, "public/img/sites/credits.json", '{"credit":"Contains modified Copernicus Sentinel data"}')


class V2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = os.path.join(self.tmp, "repo")
        self.root = os.path.join(self.tmp, "out")
        os.makedirs(self.repo)
        os.makedirs(os.path.join(self.root, "public/data"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_build(self):
        ctx = Ctx(self.repo, self.root, SITES)
        v2.build(ctx)
        with open(os.path.join(self.root, "public/data/v2.json")) as f:
            return json.load(f)

    def test_all_inputs_absent(self):
        d = self.run_build()
        self.assertFalse(d["run_completed"])
        self.assertEqual(d["status_text"], "v2 run not completed")
        self.assertTrue(all(not i["present"] for i in d["inputs"]))
        self.assertIsNone(d["thermal_refs"])
        self.assertEqual(d["preregistrations"], [])
        self.assertFalse(d["has_site_measurements"])
        self.assertFalse(os.path.exists(os.path.join(self.root, "public/data/site_measurements.json")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "public/img/sites")))

    def test_all_inputs_present(self):
        full_fixture(self.repo)
        d = self.run_build()
        self.assertTrue(d["run_completed"])
        self.assertEqual(d["status_text"], "v2 run complete")
        rows = {(r["site"], r["layer"], r["stat"]): r for r in d["thermal_refs"]["rows"]}
        self.assertEqual(rows[("shackleton_rim", "prp_temp_max", "min")]["display"], "76.75")
        self.assertEqual(rows[("shackleton_rim", "prp_triangles", "n")]["display"], "613")
        self.assertEqual(rows[("jezero", "surface_temperature", "not_covered")]["status"], "not_covered")
        self.assertIsNone(rows[("jezero", "surface_temperature", "not_covered")]["display"])
        self.assertEqual(rows[("jezero", "tes_ti_day", "primary_basis")]["status"], "label")
        pre = {p["id"]: p for p in d["preregistrations"]}
        self.assertTrue(pre["B"]["matches"])  # the last matching line wins, comments are ignored
        self.assertFalse(pre["C"]["matches"])
        self.assertEqual(pre["B"]["deviations_file"], "runs/v2/PREREG_B_DEVIATIONS.md")
        self.assertTrue(d["has_site_measurements"])
        with open(os.path.join(self.root, "public/data/site_measurements.json")) as f:
            sm = json.load(f)
        rows = sm["by_site"]["askja-caldera-moon"]
        self.assertEqual(len(rows), 3)
        null = next(r for r in rows if r["variable"] == "vv")
        self.assertIsNone(null["value"])
        self.assertEqual(null["note"], "no_images")  # nulls stay, with their note
        approx = next(r for r in rows if r["radius_km"] == "2")
        self.assertFalse(approx["page_ok"])
        self.assertEqual(sm["unmatched_site_names"], ["Nowhere"])
        self.assertTrue(os.path.exists(os.path.join(self.root, "public/img/sites/askja-caldera.jpg")))

    def test_claims_cover_every_shown_number(self):
        full_fixture(self.repo)
        self.run_build()
        by_claim = {c[0]: c for c in claims.build_claims(self.root)}
        self.assertEqual(by_claim["v2.thermal.shackleton_rim.prp_temp_max.min"][1], "76.75")
        self.assertIn("v2.evidence.askja-caldera-moon.r10.cop_dem.elevation.mean", by_claim)
        self.assertEqual(by_claim["v2.evidence.askja-caldera-moon.r10.cop_dem.elevation.mean"][1], "1100")
        self.assertNotIn("v2.evidence.askja-caldera-moon.r10.s1.vv.median", by_claim)  # a null has no number to claim
        self.assertNotIn("v2.thermal.jezero.surface_temperature.not_covered", by_claim)

    def test_a_removed_input_does_not_leave_stale_output(self):
        full_fixture(self.repo)
        self.run_build()
        shutil.rmtree(os.path.join(self.repo, "data/v2"))
        d = self.run_build()
        self.assertFalse(d["has_site_measurements"])
        self.assertFalse(os.path.exists(os.path.join(self.root, "public/data/site_measurements.json")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "public/img/sites")))  # chips go too

    def test_wrong_measurement_layout_stops_the_build(self):
        write(os.path.join(self.repo, "data/v2"), "data/evidence/site_measurements.csv", "site_name,body\nA,Moon\n")
        with self.assertRaises(SystemExit):
            self.run_build()

    def test_partial_inputs(self):
        write(os.path.join(self.repo, "data/v2"), "data/reference/thermal_refs.csv", THERMAL)
        d = self.run_build()
        self.assertFalse(d["run_completed"])
        self.assertIsNotNone(d["thermal_refs"])
        self.assertFalse(d["has_site_measurements"])

    def test_display_rule(self):
        self.assertEqual(v2.sig("49.584"), "49.58")
        self.assertEqual(v2.sig("100"), "100")
        self.assertEqual(v2.sig("0.14392"), "0.1439")
        self.assertEqual(v2.sig("1234.567", 3), "1230")


if __name__ == "__main__":
    unittest.main()
