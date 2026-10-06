#!/usr/bin/env python3
"""Exact, read-only lookup tests for the SWT market resolver."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from swt_market import (  # noqa: E402
    get_city_market,
    get_market_context,
    get_state_market,
    get_support_context,
    load_market_data,
    resolve_city,
    resolve_state,
)


MARKET_ROOT = ROOT / "references" / "knowledge" / "swt_market"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SwtMarketResolverTests(unittest.TestCase):
    def test_myrtle_beach_with_state_code_is_city_exact(self):
        result = resolve_city("Myrtle Beach", "SC")
        self.assertTrue(result["matched"])
        self.assertEqual(result["match_level"], "city_exact")
        self.assertEqual((result["state"], result["state_code"], result["city"]),
                         ("South Carolina", "SC", "Myrtle Beach"))

    def test_case_and_outer_spaces_resolve_same_city_record(self):
        first = resolve_city("Myrtle Beach", "SC")
        second = resolve_city(" myrtle beach ", " south carolina ")
        self.assertEqual(second["match_level"], "city_exact")
        self.assertEqual(first["city_market"], second["city_market"])

    def test_state_code_resolves_state_name_and_market(self):
        result = resolve_state(" sc ")
        self.assertTrue(result["matched"])
        self.assertEqual(result["match_level"], "state_exact")
        self.assertEqual((result["state"], result["state_code"]), ("South Carolina", "SC"))
        self.assertEqual(get_state_market("SC")["state_market"], result["state_market"])

    def test_nonexistent_state_is_not_guessed(self):
        result = resolve_state("Sout Carolina")
        self.assertFalse(result["matched"])
        self.assertEqual(result["match_level"], "state_not_found")

    def test_unknown_city_in_valid_state_returns_state_fallback(self):
        result = get_city_market("Fenwick Beach", "DE")
        self.assertTrue(result["matched"])
        self.assertEqual(result["match_level"], "state_fallback")
        self.assertFalse(result["city_found"])
        self.assertEqual(result["requested_city"], "Fenwick Beach")
        self.assertEqual((result["state"], result["state_code"]), ("Delaware", "DE"))

    def test_duplicate_city_without_state_is_ambiguous(self):
        data = load_market_data()
        counts = Counter(row["city"].casefold() for row in data["cities"])
        duplicate = next(name for name, count in counts.items() if count > 1)
        result = resolve_city(duplicate)
        self.assertFalse(result["matched"])
        self.assertEqual(result["match_level"], "city_ambiguous")
        self.assertGreater(len(result["candidate_states"]), 1)

    def test_fenwick_beach_is_not_rebound_to_fenwick_island(self):
        result = get_market_context("Fenwick Beach", "DE")
        self.assertEqual(result["match_level"], "state_fallback")
        self.assertIsNone(result["city_market"])
        self.assertEqual(result["location"]["requested_city"], "Fenwick Beach")
        self.assertNotIn("Fenwick Island", json.dumps(result, ensure_ascii=False))
        regional = result["support"]["regional_support"]
        self.assertTrue(any(row["location_raw"] == "Bethany Beach and Fenwick Beach, DE" for row in regional))
        self.assertFalse(result["support"]["has_support_group"])
        self.assertEqual(result["support"]["support_level"], "regional_evidence")

    def test_door_county_records_do_not_attach_to_a_concrete_wisconsin_city(self):
        result = get_support_context("Wisconsin Dells", "WI")
        self.assertTrue(result["has_support_group"])
        self.assertTrue(any(row["location_raw"] == "Wisconsin Dells, WI" for row in result["city_exact_support"]))
        self.assertFalse(any("Door County" in row["location_raw"] for row in result["regional_support"]))
        state_result = get_support_context(state="WI")
        door_rows = [row for row in state_result["regional_support"] if row["location_raw"].startswith("Door County")]
        self.assertEqual(len(door_rows), 2)
        self.assertEqual({row["match_type"] for row in door_rows}, {"unmatched"})

    def test_cape_cod_is_returned_as_regional_evidence_not_city_exact(self):
        result = get_market_context("Dennis", "MA")
        self.assertEqual(result["match_level"], "city_exact")
        self.assertFalse(result["support"]["has_support_group"])
        self.assertEqual(result["support"]["city_exact_support"], [])
        cape = [row for row in result["support"]["regional_support"] if row["location_raw"].startswith("Cape Cod Affiliate")]
        self.assertEqual(len(cape), 1)
        self.assertEqual((cape[0]["location_scope"], cape[0]["match_type"], cape[0]["match_confidence"]),
                         ("affiliate", "regional", "low"))
        self.assertEqual(result["support"]["support_level"], "regional_evidence")

    def test_myrtle_beach_market_context_includes_source_and_limitations(self):
        result = get_market_context(city="myrtle beach", state="SC")
        self.assertEqual(result["match_level"], "city_exact")
        self.assertEqual(result["location"], {
            "city": "Myrtle Beach", "state": "South Carolina", "state_code": "SC"
        })
        self.assertEqual(result["city_market"]["total"], 2050)
        self.assertEqual(result["state_market"]["total"], 2852)
        self.assertEqual(result["support"]["has_support_group"], True)
        self.assertEqual(result["support"]["support_level"], "city_exact")
        self.assertEqual(result["source"]["source_name"], "SWTDashboard")
        self.assertIsNotNone(result["source"]["dataset_last_refresh"])
        self.assertIsNotNone(result["source"]["retrieved_at"])
        self.assertIn("not verified as deduplicated annual participants", result["limitations"])

    def test_market_context_for_state_has_no_synthetic_city(self):
        result = get_market_context(state="South Carolina")
        self.assertEqual(result["match_level"], "state_exact")
        self.assertIsNone(result["city_market"])
        self.assertEqual(result["location"]["state_code"], "SC")

    def test_city_typo_is_not_automatically_corrected(self):
        result = resolve_city("Myrtle Beech", "SC")
        self.assertEqual(result["match_level"], "state_fallback")
        self.assertFalse(result["city_found"])

    def test_unresolved_location_does_not_receive_unscoped_support_records(self):
        unknown_city = get_support_context("No Such Place")
        self.assertEqual(unknown_city["match_level"], "city_not_found")
        self.assertEqual(unknown_city["regional_support"], [])
        unknown_state = get_market_context(state="Sout Carolina")
        self.assertEqual(unknown_state["match_level"], "state_not_found")
        self.assertEqual(unknown_state["support"]["regional_support"], [])

    def test_cli_works_outside_project_working_directory(self):
        script = SCRIPTS / "swt_market.py"
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(script), "--city", "Myrtle Beach", "--state", "SC"],
                cwd=directory,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["match_level"], "city_exact")

    def test_runtime_knowledge_works_without_build_time_source_data(self):
        script = SCRIPTS / "swt_market.py"
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ.copy()
            env["HOWTO_SWT_SOURCE_DATA_ROOT"] = str(Path(directory) / "missing-source-data")
            result = subprocess.run(
                [sys.executable, str(script), "--city", "Myrtle Beach", "--state", "SC"],
                cwd=directory, env=env, text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads(result.stdout)
        self.assertEqual(context["match_level"], "city_exact")
        self.assertEqual(context["city_market"]["total"], 2050)

    def test_resolver_does_not_modify_reference_files_or_participant_totals(self):
        files = [
            MARKET_ROOT / "state_summary.json",
            MARKET_ROOT / "city_summary.json",
            MARKET_ROOT / "support_groups.json",
            MARKET_ROOT / "source_metadata.json",
        ]
        before = {path.name: sha256(path) for path in files}
        data = load_market_data()
        self.assertEqual((len(data["states"]), len(data["cities"]), len(data["support_groups"])),
                         (51, 2465, 15))
        for field, expected in (("active", 87679), ("initial", 3754), ("total", 91433)):
            self.assertEqual(sum(row[field] for row in data["states"]), expected)
            self.assertEqual(sum(row[field] for row in data["cities"]), expected)
        resolve_state("SC")
        resolve_city("Myrtle Beach", "SC")
        get_state_market("SC")
        get_city_market("Myrtle Beach", "SC")
        get_support_context("Myrtle Beach", "SC")
        get_market_context("Myrtle Beach", "SC")
        after = {path.name: sha256(path) for path in files}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
