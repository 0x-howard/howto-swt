#!/usr/bin/env python3
"""Position-skill contracts for using the unified location context."""

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from budget import calculate_position_overview, format_position_overview  # noqa: E402
from location_context import get_location_context, resolve_location  # noqa: E402


SKILL_TEXT = (ROOT / "skills/swt-position/SKILL.md").read_text(encoding="utf-8")


class SwtPositionLocationContextTests(unittest.TestCase):
    def test_myrtle_beach_offer_keeps_six_dimensions_and_adds_exact_market_evidence(self):
        context = get_location_context(city="Myrtle Beach", state="SC")
        self.assertEqual(context["match_level"], "city_exact")
        self.assertEqual(context["swt_market"]["city_market"]["total"], 2050)
        self.assertEqual(context["swt_market"]["state_market"]["total"], 2852)
        self.assertTrue(context["swt_market"]["support"]["has_support_group"])
        self.assertEqual(context["swt_market"]["support"]["support_level"], "city_exact")

        offer = {
            "mode": "position_overview",
            "offers": [{
                "id": "myrtle",
                "label": "Myrtle Beach offer",
                "state": "South Carolina",
                "city": "Myrtle Beach",
                "wage_usd_per_hour": 15,
                "hours_per_week": 35,
                "work_weeks": 12,
            }],
        }
        rendered = format_position_overview(calculate_position_overview(offer))
        core = rendered.split("## 2. 回本测算", 1)[0]
        for dimension in ("收入", "住宿", "生活成本", "交通", "二工", "落地便利"):
            self.assertIn(f"| {dimension} |", core)
        self.assertNotIn("年度有 2050 名学生", rendered)

        self.assertIn("location_context.py", SKILL_TEXT)
        self.assertIn("SWT Market 只为 Job、Infra", SKILL_TEXT)
        self.assertIn("不得据此推断工作好找、二工多", SKILL_TEXT)
        self.assertIn("不等同于年度去重参与者人数", SKILL_TEXT)

    def test_rhode_island_market_does_not_fabricate_state_context_fields(self):
        context = get_location_context(state="Rhode Island")
        self.assertTrue(context["matched"])
        self.assertFalse(context["availability"]["state_context"])
        self.assertTrue(context["availability"]["swt_market"])
        self.assertIsNone(context["state_context"])
        self.assertEqual(context["swt_market"]["state_market"]["total"], 1030)
        self.assertIn("market 数据不能补造州税、最低工资或生活成本", SKILL_TEXT)

        offer = {
            "mode": "position_overview",
            "offers": [{
                "id": "ri", "label": "Rhode Island offer", "state": "Rhode Island",
                "wage_usd_per_hour": 15, "hours_per_week": 35, "work_weeks": 12,
            }],
        }
        result = calculate_position_overview(offer)["offers"][0]
        self.assertEqual(result["state"], "RI")
        self.assertEqual(result["cost_sources"]["rent_usd_per_week"], "global_estimate")
        self.assertEqual(result["second_job"], "不计入收益（估）")

    def test_fenwick_beach_uses_state_fallback_without_a_city_count(self):
        context = get_location_context(city="Fenwick Beach", state="DE")
        self.assertEqual(context["match_level"], "state_fallback")
        self.assertIsNone(context["swt_market"]["city_market"])
        self.assertEqual(context["location"]["requested_city"], "Fenwick Beach")
        self.assertNotIn("Fenwick Island", json.dumps(context, ensure_ascii=False))
        support = context["swt_market"]["support"]
        self.assertEqual(support["support_level"], "regional_evidence")
        self.assertTrue(any(
            row["location_raw"] == "Bethany Beach and Fenwick Beach, DE"
            for row in support["regional_support"]
        ))
        self.assertIn("state_fallback", SKILL_TEXT)
        self.assertIn("city_market 必须保持为空", SKILL_TEXT)

    def test_door_county_and_cape_cod_support_are_not_city_exact(self):
        door = get_location_context(city="Door County", state="WI")
        door_support = door["swt_market"]["support"]
        self.assertFalse(door_support["has_support_group"])
        self.assertTrue(any(
            row["location_raw"] == "Door County, WI"
            and row["location_scope"] == "county_or_region"
            and row["match_type"] == "unmatched"
            for row in door_support["regional_support"]
        ))
        self.assertFalse(any(row["location_raw"] == "Door County Affiliate, WI"
                             for row in door_support["city_exact_support"]))

        cape = get_location_context(city="Dennis", state="MA")["swt_market"]["support"]
        self.assertFalse(cape["has_support_group"])
        cape_records = [row for row in cape["regional_support"]
                        if row["location_raw"].startswith("Cape Cod Affiliate")]
        self.assertEqual(len(cape_records), 1)
        self.assertEqual((cape_records[0]["match_type"], cape_records[0]["match_confidence"]),
                         ("regional", "low"))

    def test_offer_without_location_skips_location_context_and_keeps_fallback_rules(self):
        identity = resolve_location()
        self.assertEqual(identity["match_level"], "location_not_provided")
        self.assertIn("没有地点时跳过 Location Context", SKILL_TEXT)
        self.assertIn("沿用当前缺值与通用估算规则", SKILL_TEXT)

        offer = {
            "mode": "position_overview",
            "offers": [{
                "id": "unknown", "label": "Offer without location",
                "wage_usd_per_hour": 15, "hours_per_week": 35, "work_weeks": 12,
            }],
        }
        original = copy.deepcopy(offer)
        result = calculate_position_overview(offer)["offers"][0]
        self.assertEqual(offer, original)
        self.assertIsNone(result["state"])
        self.assertEqual(result["cost_sources"]["rent_usd_per_week"], "global_estimate")

    def test_high_participant_count_cannot_create_recommendation_or_job_claim(self):
        context = get_location_context(city="Myrtle Beach", state="SC")
        self.assertGreater(context["swt_market"]["city_market"]["total"], 0)
        for field in ("recommended", "good_for_swt", "swt_score", "maturity_score", "hot_city", "best_city", "good_offer"):
            self.assertNotIn(field, json.dumps(context, ensure_ascii=False))
        for prohibition in ("不得据此推断工作好找", "二工多", "不增加第七维", "不形成分数或推荐"):
            self.assertIn(prohibition, SKILL_TEXT)


if __name__ == "__main__":
    unittest.main()
