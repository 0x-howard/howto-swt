#!/usr/bin/env python3
"""Tests for the unified state-context and SWT market resolver."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import location_context
import state_context
import swt_market


MARKET_ROOT = ROOT / "references" / "knowledge" / "swt_market"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LocationContextTests(unittest.TestCase):
    def test_myrtle_beach_combines_both_contexts(self):
        result = location_context.get_location_context("Myrtle Beach", "SC")
        self.assertEqual(result["match_level"], "city_exact")
        self.assertEqual(result["location"], {
            "city": "Myrtle Beach", "state": "South Carolina", "state_code": "SC"
        })
        self.assertTrue(result["availability"]["state_context"])
        self.assertTrue(result["availability"]["swt_market"])
        self.assertEqual(result["swt_market"]["city_market"]["total"], 2050)
        self.assertEqual(result["swt_market"]["state_market"]["total"], 2852)
        self.assertIsNotNone(result["state_context"])

    def test_fenwick_beach_keeps_state_fallback_and_regional_support(self):
        result = location_context.get_location_context("Fenwick Beach", "DE")
        self.assertEqual(result["match_level"], "state_fallback")
        self.assertEqual(result["location"]["requested_city"], "Fenwick Beach")
        self.assertTrue(result["availability"]["swt_market"])
        self.assertIsNone(result["swt_market"]["city_market"])
        self.assertNotIn("Fenwick Island", json.dumps(result, ensure_ascii=False))
        self.assertTrue(any(
            row["location_raw"] == "Bethany Beach and Fenwick Beach, DE"
            for row in result["swt_market"]["support"]["regional_support"]
        ))
        self.assertEqual(result["swt_market"]["support"]["support_level"], "regional_evidence")

    def test_valid_state_and_missing_city_keep_state_context_without_guessing(self):
        result = location_context.get_location_context("No Such Place", "SC")
        self.assertTrue(result["matched"])
        self.assertEqual(result["match_level"], "state_fallback")
        self.assertEqual(result["location"]["requested_city"], "No Such Place")
        self.assertTrue(result["availability"]["state_context"])
        self.assertTrue(result["availability"]["swt_market"])
        self.assertIsNotNone(result["state_context"])
        self.assertIsNone(result["swt_market"]["city_market"])
        self.assertNotIn("city", result["location"])

    def test_duplicate_market_city_without_state_stays_ambiguous(self):
        data = swt_market.load_market_data()
        counts = Counter(row["city"].casefold() for row in data["cities"])
        city = next(name for name, count in counts.items() if count > 1)
        result = location_context.get_location_context(city=city)
        self.assertFalse(result["matched"])
        self.assertEqual(result["match_level"], "city_ambiguous")
        self.assertGreater(len(result["candidate_states"]), 1)
        self.assertIsNone(result["state_context"])
        self.assertIsNone(result["swt_market"])

    def test_nonexistent_state_is_not_guessed(self):
        result = location_context.get_location_context("Myrtle Beach", "Sout Carolina")
        self.assertFalse(result["matched"])
        self.assertEqual(result["match_level"], "state_not_found")
        self.assertFalse(result["availability"]["state_context"])
        self.assertFalse(result["availability"]["swt_market"])
        self.assertIsNone(result["state_context"])
        self.assertIsNone(result["swt_market"])

    def test_rhode_island_has_market_data_without_state_context_profile(self):
        result = location_context.get_location_context(state="Rhode Island")
        self.assertTrue(result["matched"])
        self.assertEqual(result["match_level"], "state_exact")
        self.assertEqual(result["location"]["state_code"], "RI")
        self.assertFalse(result["availability"]["state_context"])
        self.assertTrue(result["availability"]["swt_market"])
        self.assertIsNone(result["state_context"])
        self.assertEqual(result["swt_market"]["state_market"]["total"], 1030)

    def test_city_typo_is_not_automatically_corrected(self):
        result = location_context.get_location_context("Myrtle Beech", "SC")
        self.assertEqual(result["match_level"], "state_fallback")
        self.assertEqual(result["location"]["requested_city"], "Myrtle Beech")
        self.assertIsNone(result["swt_market"]["city_market"])

    def test_door_county_and_cape_cod_remain_regional_evidence(self):
        door = location_context.get_location_context("Door County", "WI")
        self.assertEqual(door["match_level"], "city_exact")
        self.assertFalse(door["swt_market"]["support"]["has_support_group"])
        self.assertTrue(any(
            row["location_raw"] == "Door County, WI"
            for row in door["swt_market"]["support"]["regional_support"]
        ))

        cape = location_context.get_location_context("Dennis", "MA")
        self.assertEqual(cape["match_level"], "city_exact")
        support = cape["swt_market"]["support"]
        self.assertFalse(support["has_support_group"])
        self.assertEqual(support["support_level"], "regional_evidence")
        cape_rows = [row for row in support["regional_support"] if row["location_raw"].startswith("Cape Cod Affiliate")]
        self.assertEqual(len(cape_rows), 1)
        self.assertEqual(cape_rows[0]["match_type"], "regional")
        self.assertEqual(cape_rows[0]["match_confidence"], "low")

    def test_state_only_query_has_no_synthetic_city(self):
        result = location_context.get_location_context(state="Wisconsin")
        self.assertEqual(result["match_level"], "state_exact")
        self.assertNotIn("city", result["location"])
        self.assertIsNone(result["swt_market"]["city_market"])

    def test_cli_resolves_from_outside_project_directory(self):
        script = SCRIPTS / "location_context.py"
        for args, expected in [
            (("--city", "Myrtle Beach", "--state", "SC"), "city_exact"),
            (("--state", "Wisconsin"), "state_exact"),
        ]:
            with tempfile.TemporaryDirectory() as cwd:
                run = subprocess.run(
                    [sys.executable, "-B", str(script), *args],
                    cwd=cwd,
                    text=True,
                    capture_output=True,
                    check=False,
                )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["match_level"], expected)

    def test_resolver_does_not_modify_state_context_or_market_sources(self):
        files = [
            *sorted((ROOT / "references/knowledge/state_context").glob("STATE_INDEX.md")),
            *sorted((ROOT / "references/knowledge/state_context/states").glob("*.md")),
            *[MARKET_ROOT / name for name in (
                "state_summary.json", "city_summary.json", "support_groups.json", "source_metadata.json"
            )],
        ]
        before = {str(path.relative_to(ROOT)): sha256(path) for path in files}
        result = location_context.get_location_context("Myrtle Beach", "SC")
        self.assertEqual(result["swt_market"]["city_market"]["total"], 2050)
        after = {str(path.relative_to(ROOT)): sha256(path) for path in files}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
