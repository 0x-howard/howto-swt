#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from second_job_supply import plan, score


class SecondJobSupplyTests(unittest.TestCase):
    def test_plan_queries(self):
        result = plan(address="123 Main St, Myrtle Beach, SC 29577")
        self.assertIn("restaurants", result["search_queries"])
        self.assertIn("Myrtle Beach", result["origin_label"])

    def test_four_stars_many_restaurants(self):
        result = score(restaurants=8, hotels=2, grocery=1, seasonal=0)
        self.assertEqual(result["stars"], 4)
        self.assertEqual(result["stars_display"], "🌟🌟🌟🌟")
        self.assertIn("周围餐馆较多，有二工机会", result["analysis_short_zh"])
        self.assertEqual(result["for_budget_details"]["second_job_supply_stars"], 4)

    def test_one_star_empty(self):
        result = score()
        self.assertEqual(result["stars"], 1)

    def test_high_competition_can_drop_tier(self):
        base = score(restaurants=5, hotels=1, grocery=1, competition="low")
        crowded = score(restaurants=5, hotels=1, grocery=1, competition="high")
        self.assertGreaterEqual(base["stars"], crowded["stars"])


if __name__ == "__main__":
    unittest.main()
