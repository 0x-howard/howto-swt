import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from ssa_offices import lookup, parse_offer_location


class SsaOfficesTests(unittest.TestCase):
    def test_myrtle_beach_same_city(self):
        result = lookup(state="SC", city="Myrtle Beach", limit=3)
        self.assertTrue(result["same_city"])
        self.assertEqual(result["offices"][0]["city"], "Myrtle Beach")
        self.assertIn("同城", result["student_hint_zh"])
        self.assertTrue(result["landing_line_zh"].startswith("SSA 办公室："))
        self.assertIn("Myrtle Beach", result["landing_line_zh"])

    def test_address_parses_zip_and_city(self):
        loc = parse_offer_location(address="611 Chapin Blvd, Myrtle Beach, SC 29577")
        self.assertEqual(loc["state"], "SC")
        self.assertEqual(loc["zip"], "29577")
        self.assertIn("Myrtle", loc["city"] or "")

    def test_zip_ranks_before_far_state_list(self):
        result = lookup(state="SC", zip_code="29577", limit=5)
        self.assertGreaterEqual(result["count"], 1)
        self.assertIn(result["offices"][0]["match"], {"same_zip", "same_city_zip", "same_zip3", "same_city"})

    def test_sparks_returns_candidates_and_distance_queries(self):
        result = lookup(state="NV", city="Sparks", limit=3)
        self.assertEqual(result["best_match"], "same_state")
        self.assertGreaterEqual(result["count"], 3)
        cities = {o["city"] for o in result["offices"]}
        self.assertIn("Reno", cities)
        self.assertTrue(result["landing_line_zh"].startswith("SSA 办公室："))
        self.assertNotIn("未命中", result["landing_line_zh"])
        self.assertTrue(result["distance_search_queries"])
        self.assertIn("Sparks", result["nearest_office_search_query"])


if __name__ == "__main__":
    unittest.main()
