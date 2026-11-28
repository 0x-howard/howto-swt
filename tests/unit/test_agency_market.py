#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from agency_market import agency_ask_options, lookup, planning_fee_for


class AgencyMarketTests(unittest.TestCase):
    def test_lookup_ximi(self):
        result = lookup(name="西米")
        self.assertGreaterEqual(result["count"], 1)
        self.assertEqual(result["agencies"][0]["name"], "西米")
        self.assertEqual(result["agencies"][0]["planning_default_cny"], 20500)

    def test_planning_fee_for_alias(self):
        hit = planning_fee_for("USummer")
        self.assertIsNotNone(hit)
        self.assertEqual(hit["name"], "美夏")
        self.assertEqual(hit["planning_default_cny"], 19300)

    def test_ask_options_include_table_and_fallbacks(self):
        options = agency_ask_options(global_default_cny=25000)
        ids = [o["id"] for o in options]
        self.assertIn("agency:西米", ids)
        self.assertIn("agency_other", ids)
        self.assertIn("agency_unknown", ids)
        ximi = next(o for o in options if o["id"] == "agency:西米")
        self.assertEqual(ximi["proposed_project_cost_cny"], 20500)


if __name__ == "__main__":
    unittest.main()
