#!/usr/bin/env python3
"""Data validation and state-context unit tests."""
import json
import re
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from state_context import (  # noqa: E402
    MISSING_VALUE, REQUIRED_FIELDS, SECTIONS, compare_offer_wage,
    load_state_profile, render_state_reference, resolve_state,
)
from validate_records import validate  # noqa: E402

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "assets/collection-record-example.json").read_text(encoding="utf-8"))

    def claim(self):
        return self.data["agencies"][0]["claims"][0]

    def test_empty_is_not_ready(self):
        empty = json.loads((ROOT / "assets/collection-records.json").read_text(encoding="utf-8"))
        self.assertEqual(validate(empty)["readiness"], "empty template")
        self.assertEqual(validate(self.data)["pending_claims"], 6)

    def test_missing_source_rejected(self):
        self.claim()["source_ids"] = ["does-not-exist"]
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_unverified_cannot_be_upgraded(self):
        self.claim()["status"] = "verified"
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_missing_foreign_entity_rejected(self):
        self.claim()["field"] = "sponsor_id"
        self.claim()["value"] = "missing-sponsor"
        with self.assertRaises(ValueError):
            validate(self.data)

class StateContextTests(unittest.TestCase):
    STATES_ROOT = ROOT / "references/knowledge/state_context/states"
    EXPECTED_CODES = {
        "AK", "AL", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "IA", "ID", "IL",
        "KY", "LA", "MA", "MD", "ME", "MI", "MN", "MO", "MT", "NC", "ND", "NH",
        "NJ", "NV", "NY", "OH", "PA", "SC", "SD", "TN", "TX", "UT", "VA", "VT",
        "WA", "WI", "WY",
    }

    def test_common_swt_locations_route_to_the_expected_state_profile(self):
        for location, code in {
            "Myrtle Beach": "SC",
            "Wisconsin Dells": "WI",
            "Ocean City": "MD",
        }.items():
            with self.subTest(location=location):
                resolution = resolve_state(location)
                self.assertIsNotNone(resolution)
                self.assertEqual(resolution.code, code)
                self.assertEqual(resolution.source, "state_index")
                self.assertTrue((self.STATES_ROOT / f"{code}.md").is_file())

    def test_state_index_points_only_to_existing_profiles(self):
        index = ROOT / "references/knowledge/state_context/STATE_INDEX.md"
        entries = []
        for line in index.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) == 2 and cells[0] not in {"地点", "---"}:
                entries.append(cells[1])
        self.assertTrue(entries)
        self.assertTrue(all((self.STATES_ROOT / f"{code}.md").is_file() for code in entries))

    def test_explicit_state_beats_the_index(self):
        resolution = resolve_state("Myrtle Beach, South Carolina")
        self.assertIsNotNone(resolution)
        self.assertEqual((resolution.code, resolution.source), ("SC", "explicit_state_name"))
        direct_code = resolve_state("SC")
        self.assertIsNotNone(direct_code)
        self.assertEqual((direct_code.code, direct_code.source), ("SC", "explicit_state_code"))

    def test_unknown_location_does_not_guess_a_state(self):
        self.assertIsNone(resolve_state("A made-up resort town"))

    def test_offer_wage_stays_authoritative_when_compared_with_state_context(self):
        profile = load_state_profile("SC")
        self.assertEqual(profile["常见时薪"], "$10–12.99/h")
        self.assertEqual(compare_offer_wage(15, profile["常见时薪"]), "higher")
        self.assertEqual(profile["常见时薪"], "$10–12.99/h")

    def test_missing_state_field_renders_the_required_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            profile_path = Path(directory) / "SC.md"
            profile_path.write_text("# South Carolina\n\n州: South Carolina\n州缩写: SC\n常见时薪: \n", encoding="utf-8")
            profile = load_state_profile("SC", Path(directory))
        self.assertEqual(profile["常见时薪"], MISSING_VALUE)
        self.assertEqual(profile["医疗"], MISSING_VALUE)

    def test_every_excel_covered_state_has_the_exact_product_schema(self):
        profiles = {path.stem for path in self.STATES_ROOT.glob("*.md")}
        self.assertEqual(profiles, self.EXPECTED_CODES)
        forbidden = ("overtime", "tips", "水电", "押金", "居住条件", "Uber", "是否依赖汽车", "淡旺季", "排班兼容度", "evidence")
        for code in profiles:
            content = (self.STATES_ROOT / f"{code}.md").read_text(encoding="utf-8")
            with self.subTest(state=code):
                for section in SECTIONS:
                    self.assertIn(f"## {section}", content)
                for field in REQUIRED_FIELDS:
                    self.assertEqual(len(re.findall(rf"^{re.escape(field)}:", content, re.MULTILINE)), 1)
                self.assertFalse(any(term.casefold() in content.casefold() for term in forbidden))

    def test_state_reference_is_never_written_as_city_level_data(self):
        output = render_state_reference(load_state_profile("SC"), ("常见时薪", "好不好找"))
        self.assertIn("South Carolina 州级参考", output)
        self.assertIn("常见时薪", output)
        self.assertNotIn("###", output)
        self.assertNotIn("常见周租", output)
        for city in ("Myrtle Beach", "Wisconsin Dells", "Ocean City"):
            self.assertNotIn(city, output)
        position = (ROOT / "skills/swt-position/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("具体 Offer 数据优先于州级常见数据", position)
        self.assertIn("绝不猜测", position)
        self.assertIn("禁止把州级资料写成“某城市平均工资”", position)

    def test_state_reference_requires_relevant_fields(self):
        profile = load_state_profile("SC")
        with self.assertRaises(ValueError):
            render_state_reference(profile, ())
