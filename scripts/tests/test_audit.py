"""Tests for the wording audit (C6). Standard library only."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import audit_site  # noqa: E402
from gsop_data import claims  # noqa: E402

E32 = "The Monte Carlo varies the weights and applies no systematic Earth bias to any of the 15 Earth columns, so the reported score bands and robust-tile counts understate the real uncertainty."
RX = claims.term_regex(["validated", "discovered", "undiscovered", "new sites"])

GOOD = (
    "<main><h1>Honest Map</h1><h2>What failed</h2>"
    "<p>The negative-control test failed. The ranking has not been checked against independent data. Mars is a low-confidence secondary result.</p>"
    f"<p>{E32}</p><p>Candidates not in our reference list are unreviewed.</p></main>"
)


def run(page, route="/map", site=False):
    return audit_site.audit_page(route, page, RX, E32, site)


class AuditTests(unittest.TestCase):
    def test_a_good_page_passes(self):
        self.assertEqual(run(GOOD), [])

    def test_the_e32_sentence_may_contain_the_word_robust_and_still_pass(self):
        self.assertEqual(run(GOOD), [])  # "robust-tile" is inside the verbatim sentence

    def test_banned_word(self):
        self.assertTrue(any("banned word 'discovered'" in p for p in run(GOOD.replace("unreviewed", "a discovered site"))))

    def test_filler_word_outside_e32(self):
        self.assertTrue(any("filler word 'leverage'" in p for p in run(GOOD.replace("unreviewed", "we leverage data"))))

    def test_em_dash(self):
        self.assertTrue(any("em dash" in p for p in run(GOOD.replace("unreviewed", "unreviewed — always"))))

    def test_altered_e32(self):
        bad = GOOD.replace("applies no systematic Earth bias", "applies a small Earth bias")
        found = run(bad)
        self.assertTrue(any("E32" in p for p in found), found)

    def test_missing_standing_statements(self):
        found = run("<main><h1>Map</h1><p>Scores.</p></main>")
        self.assertTrue(any("independent data" in p for p in found))
        self.assertTrue(any("low-confidence" in p for p in found))
        self.assertTrue(any("negative-control" in p for p in found))

    def test_candidates_must_be_called_not_in_our_reference_list(self):
        page = GOOD.replace("Candidates not in our reference list are unreviewed.", "Candidates are shown here.")
        self.assertTrue(any("not in our reference list" in p for p in run(page)))

    def test_heading_case_and_single_h1(self):
        found = run(GOOD.replace("<h2>What failed</h2>", "<h2>What Failed Here</h2><h1>Another</h1>"))
        self.assertTrue(any("sentence case" in p for p in found), found)
        self.assertTrue(any("one h1" in p for p in found), found)

    def test_a_site_page_needs_the_independent_data_statement(self):
        self.assertTrue(any("independent data" in p for p in run("<main><h1>Askja</h1></main>", route="/sites/askja", site=True)))


if __name__ == "__main__":
    unittest.main()
