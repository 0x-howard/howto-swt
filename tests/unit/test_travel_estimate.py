#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import travel_estimate as te  # noqa: E402


class TravelEstimateTests(unittest.TestCase):
    def test_shanghai_nyc_myrtle_beach_round_trip(self):
        result = te.estimate("上海", "纽约", "Myrtle Beach", round_trip=True, advance_days=30)
        self.assertEqual(len(result["legs"]), 2)
        self.assertEqual(result["legs"][0]["kind"], "international")
        self.assertEqual(result["legs"][0]["currency"], "CNY")
        self.assertIn("宠物", result["legs"][0]["pet_note"])
        self.assertEqual(result["legs"][1]["kind"], "us_domestic")
        self.assertEqual(result["legs"][1]["currency"], "USD")
        self.assertIn("几乎带不了", result["legs"][1]["pet_note"])
        # T-30 mid center ~ international base 6250 → band around it
        mid = result["legs"][0]["bands"]["mid"]
        self.assertTrue(5000 <= mid[0] <= 6250 <= mid[1] <= 7500)
        text = te.render_text(result)
        self.assertIn("国际段", text)
        self.assertIn("Myrtle Beach", text)
        self.assertIn("提前 30 天", text)

    def test_late_booking_costs_more_than_early(self):
        early = te.estimate("广州", "纽约", "Myrtle Beach", advance_days=60, travel_month=9)
        late = te.estimate("广州", "纽约", "Myrtle Beach", advance_days=7, travel_month=6, prefer_direct=True)
        self.assertGreater(late["total_cny"]["plan"][0], early["total_cny"]["plan"][1])

    def test_gateway_only(self):
        result = te.estimate("广州", "洛杉矶")
        self.assertEqual(len(result["legs"]), 1)
        self.assertEqual(result["legs"][0]["label"], "广州 → 洛杉矶")

    def test_distance_fallback_for_unknown_pair(self):
        # Miami has coords but no city-pair row; should still estimate via distance
        result = te.estimate("上海", "纽约", "迈阿密", advance_days=30)
        self.assertEqual(result["legs"][1]["kind"], "us_domestic")
        self.assertIn("距离模型", result["legs"][1]["source"])


if __name__ == "__main__":
    unittest.main()
