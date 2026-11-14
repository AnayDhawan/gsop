"""Tests for the submission text builder and its checks (E7). Standard library only."""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from gsop_data import claims, submission  # noqa: E402

E32 = "The Monte Carlo varies the weights and applies no systematic Earth bias."


def w(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        w(self.root, "docs/E32.txt", E32 + "\n")
        w(self.root, "data/banned_words.txt", "# banned\nvalidated\ndiscovered\nundiscovered\nnew sites\n")
        w(self.root, "public/data/claims.csv", "claim,number,source_file,sha256\nmetrics.x,90.2,f,aa\nregions.Region_04.n_tiles_in_india,94,f,aa\n")
        w(self.root, "public/data/regions.json", json.dumps({"regions": [{"id": "Region 04", "n_tiles_in_india": 94}, {"id": "Region 05", "n_tiles_in_india": 0}]}))
        w(self.root, "public/data/ledger.json", json.dumps({"meta": {"uncertainty_sentence": E32}, "entries": []}))
        w(self.root, "data/MANIFEST.csv", "path,bytes,sha256\n")

    def tearDown(self):
        shutil.rmtree(self.root)

    def build(self, template):
        w(self.root, "submission/template.md", template)
        text = submission.render(self.root)
        w(self.root, "submission/SUBMISSION.md", text)
        return text

    def problems(self):
        rx = claims.term_regex(claims.banned_terms(os.path.join(self.root, "data/banned_words.txt")))
        return claims.submission_problems(self.root, rx, E32)

    def test_placeholders_become_claims_and_the_e32_sentence(self):
        text = self.build("Scored {{claim:metrics.x}}. {{india_region}} has {{india_tiles}} tiles. \"{{e32}}\"\n")
        self.assertEqual(text, f"Scored 90.2. Region 04 has 94 tiles. \"{E32}\"\n")
        self.assertEqual(self.problems(), [])

    def test_a_missing_claim_stops_the_build(self):
        w(self.root, "submission/template.md", "{{claim:nope}}")
        with self.assertRaises(submission.SubmissionError):
            submission.render(self.root)

    def test_a_typed_number_is_a_violation_but_a_web_address_is_not(self):
        self.build("We found 42 places at https://example.org/a1 .\n")
        found = self.problems()
        self.assertTrue(any("number 42" in p for p in found), found)
        self.assertFalse(any("a1" in p for p in found))

    def test_a_stale_generated_file_is_a_violation(self):
        self.build("Scored {{claim:metrics.x}}.\n")
        w(self.root, "submission/SUBMISSION.md", "Scored 91.2.\n")
        self.assertTrue(any("stale" in p for p in self.problems()))

    def test_a_banned_word_in_the_output_is_a_violation(self):
        self.build("A discovered place.\n")
        self.assertTrue(any("banned word 'discovered'" in p for p in self.problems()))

    def test_the_e32_sentence_may_not_be_changed(self):
        self.build("The Monte Carlo varies the weights and applies a small Earth bias.\n")
        self.assertTrue(any("E32 sentence altered in submission" in p for p in self.problems()))

    def test_the_india_sentence_stops_when_the_count_changes(self):
        self.build("{{india_region}}")
        w(self.root, "public/data/regions.json", json.dumps({"regions": [{"id": "Region 04", "n_tiles_in_india": 94}, {"id": "Region 06", "n_tiles_in_india": 3}]}))
        with self.assertRaises(submission.SubmissionError):
            submission.render(self.root)


if __name__ == "__main__":
    unittest.main()
