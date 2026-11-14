"""Tests for the Supabase snapshot path and the exporter (B13). Standard library only."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
sys.path.insert(0, SCRIPTS)

import export_sites  # noqa: E402
from gsop_data import sites  # noqa: E402


class FakeV1:
    def yaml(self, path):
        if path.endswith("known_sites.yaml"):
            return {"primary": {"lonar": {"lat": 19.98, "lon": 76.51, "bodies": ["mars", "moon"]}}, "secondary": {}, "gate_tests": {}, "negative_controls": {}}
        return {"site_match_radius_km": 20, "discovery": {"min_distance_km": 100}}


COLUMNS = ["body", "country", "elevation_m", "key_differences", "lat", "list", "lon", "name", "slug", "sources_ok", "status", "v1_used", "why_analog"]


def row(**o):
    r = {"body": "Moon", "country": "India", "elevation_m": 600.0, "key_differences": "Wet.", "lat": 19.98, "list": "known", "lon": 76.51, "name": "Lonar crater", "slug": "lonar-crater", "sources_ok": False, "status": "draft", "v1_used": None, "why_analog": "Basalt impact."}
    r.update(o)
    return r


class Ctx:
    def __init__(self, repo):
        self.repo, self.v1 = repo, FakeV1()


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "data/reference"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, rows):
        with open(os.path.join(self.tmp, sites.SNAPSHOT), "w") as f:
            json.dump({"columns": COLUMNS, "rows": rows}, f)

    def test_no_snapshot_means_the_csv_is_used(self):
        self.assertIsNone(sites.from_snapshot(Ctx(self.tmp), []))

    def test_copies_table_columns_and_fills_a_null_v1_flag_by_coordinates(self):
        self.write([row()])
        out, src, differ = sites.from_snapshot(Ctx(self.tmp), [])
        s = out[0]
        self.assertEqual(s["id"], "lonar-crater-moon")
        self.assertEqual(s["why_analog"], "Basalt impact.")
        self.assertIs(s["v1_used"], True)  # null in the table, within v1's radius of lonar, run for the moon
        self.assertEqual(s["v1_match"]["site_id"], "primary/lonar")
        self.assertEqual(s["elevation_m"], 600)
        self.assertEqual(src["source_file"], sites.SNAPSHOT)
        self.assertEqual(len(src["sha256"]), 64)

    def test_a_value_set_in_the_table_wins_over_the_coordinate_rule(self):
        self.write([row(v1_used=False)])
        out, _, _ = sites.from_snapshot(Ctx(self.tmp), [])
        self.assertIs(out[0]["v1_used"], False)

    def test_stops_on_a_banned_word_in_public_text(self):
        self.write([row(why_analog="A discovered crater.")])
        with self.assertRaises(SystemExit) as e:
            sites.from_snapshot(Ctx(self.tmp), [])
        self.assertIn("banned word", str(e.exception))

    def test_stops_on_duplicates_and_missing_coordinates(self):
        self.write([row(), row()])
        with self.assertRaises(SystemExit):
            sites.from_snapshot(Ctx(self.tmp), [])
        self.write([row(lat=None)])
        with self.assertRaises(SystemExit):
            sites.from_snapshot(Ctx(self.tmp), [])


class ExporterTests(unittest.TestCase):
    def test_no_keys_means_no_export(self):
        with mock.patch.dict(os.environ, {}, clear=True), tempfile.TemporaryDirectory() as d:
            self.assertFalse(export_sites.have_keys(d))

    def test_keys_from_a_local_env_file_are_found_but_not_exposed(self):
        with mock.patch.dict(os.environ, {}, clear=True), tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, ".env"), "w") as f:
                f.write("SUPABASE_URL=https://example.supabase.co\nSUPABASE_ANON_KEY=anon-secret-123\nSUPABASE_SERVICE_KEY=service-secret-456\n")
            self.assertTrue(export_sites.have_keys(d))

    def test_a_failed_request_never_puts_a_key_or_the_url_in_the_error(self):
        env = {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_ANON_KEY": "anon-secret-123"}
        failed = subprocess.CompletedProcess(args=[], returncode=22, stdout="", stderr="curl: (22) https://example.supabase.co/rest/v1/sites denied with anon-secret-123")
        with mock.patch.object(subprocess, "run", return_value=failed):
            with self.assertRaises(RuntimeError) as e:
                export_sites.fetch(env, "sites?select=*")
        msg = str(e.exception)
        self.assertNotIn("anon-secret-123", msg)
        self.assertNotIn("example.supabase.co", msg)

    def test_the_key_goes_to_curl_through_stdin_not_arguments(self):
        env = {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_ANON_KEY": "anon-secret-123"}
        ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="[]", stderr="")
        with mock.patch.object(subprocess, "run", return_value=ok) as run:
            export_sites.fetch(env, "sites")
        args, kwargs = run.call_args
        self.assertNotIn("anon-secret-123", " ".join(args[0]))
        self.assertIn("anon-secret-123", kwargs["input"])

    def test_refuses_to_overwrite_with_nothing(self):
        env = {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_ANON_KEY": "k"}
        with mock.patch.object(export_sites, "load_env", return_value=env), mock.patch.object(export_sites, "fetch", return_value=[]):
            with self.assertRaises(RuntimeError):
                export_sites.export(tempfile.gettempdir())

    def test_refuses_score_like_columns(self):
        env = {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_ANON_KEY": "k"}
        rows = [{"id": 1, "name": "a", "body": "Moon", "slug": "a", "Similarity_pct": 80}]
        with mock.patch.object(export_sites, "load_env", return_value=env), mock.patch.object(export_sites, "fetch", return_value=rows):
            with self.assertRaises(RuntimeError):
                export_sites.export(tempfile.gettempdir())


if __name__ == "__main__":
    unittest.main()
