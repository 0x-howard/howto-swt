#!/usr/bin/env python3
"""Position-skill contracts for market context in multi-offer comparisons."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from budget import calculate_position_overview, format_position_overview  # noqa: E402
from location_context import get_location_context, resolve_location  # noqa: E402


SKILL_TEXT = (ROOT / "skills/swt-position/SKILL.md").read_text(encoding="utf-8")


def make_offer(offer_id, label, *, city=None, state=None, wage=15, hours=35, rent=None):
    offer = {
        "id": offer_id,
        "label": label,
        "wage_usd_per_hour": wage,
        "hours_per_week": hours,
        "work_weeks": 12,
    }
    if city is not None:
        offer["city"] = city
    if state is not None:
        offer["state"] = state
    if rent is not None:
        offer["rent_usd_per_week"] = rent
    return offer


class SwtPositionComparisonMarketTests(unittest.TestCase):
    def test_myrtle_beach_vs_ocean_city_have_independent_city_and_support_evidence(self):
        contexts = {
            "Myrtle Beach, SC": get_location_context(city="Myrtle Beach", state="SC"),
            "Ocean City, MD": get_location_context(city="Ocean City", state="MD"),
        }
        myrtle = contexts["Myrtle Beach, SC"]
        ocean = contexts["Ocean City, MD"]
        self.assertEqual(myrtle["match_level"], "city_exact")
        self.assertEqual(ocean["match_level"], "city_exact")
        self.assertEqual(myrtle["swt_market"]["city_market"]["total"], 2050)
        self.assertEqual(myrtle["swt_market"]["state_market"]["total"], 2852)
        self.assertEqual(ocean["swt_market"]["city_market"]["total"], 3693)
        self.assertEqual(ocean["swt_market"]["state_market"]["total"], 5918)
        self.assertEqual(
            myrtle["swt_market"]["support"]["city_exact_support"][0]["support_group_name"],
            "Myrtle Beach ISOP",
        )
        self.assertEqual(
            ocean["swt_market"]["support"]["city_exact_support"][0]["support_group_name"],
            "Ocean City Summer Work Travel Committee",
        )

        result = calculate_position_overview({"offers": [
            make_offer("myrtle", "Myrtle Beach", city="Myrtle Beach", state="SC", rent=120),
            make_offer("ocean", "Ocean City", city="Ocean City", state="MD", wage=16, rent=145),
        ]})
        rendered = format_position_overview(result)
        main_table = rendered.split("## 2. 回本测算", 1)[0]
        for dimension in ("收入", "住宿", "生活成本", "交通", "二工", "落地便利"):
            self.assertIn(f"| {dimension} |", main_table)
        self.assertNotIn("| SWT Market |", main_table)
        self.assertIn("逐个岗位解析地点", SKILL_TEXT)
        self.assertIn("不得把一个岗位的州或城市 context 套用到其他岗位", SKILL_TEXT)

    def test_myrtle_beach_vs_fenwick_beach_keeps_state_fallback_and_regional_support(self):
        myrtle = get_location_context(city="Myrtle Beach", state="SC")
        fenwick = get_location_context(city="Fenwick Beach", state="DE")
        self.assertEqual(myrtle["match_level"], "city_exact")
        self.assertEqual(fenwick["match_level"], "state_fallback")
        self.assertIsNone(fenwick["swt_market"]["city_market"])
        self.assertEqual(fenwick["swt_market"]["state_market"]["total"], 1791)
        self.assertNotIn("Fenwick Island", json.dumps(fenwick, ensure_ascii=False))
        support = fenwick["swt_market"]["support"]
        self.assertEqual(support["support_level"], "regional_evidence")
        self.assertTrue(any(
            row["location_raw"] == "Bethany Beach and Fenwick Beach, DE"
            and row["match_type"] == "multi_city"
            for row in support["regional_support"]
        ))
        self.assertIn("City participant count 和 City rank 写 `-`", SKILL_TEXT)
        self.assertIn("Regional evidence", SKILL_TEXT)

    def test_rhode_island_market_context_does_not_block_multi_offer_budget(self):
        myrtle = get_location_context(city="Myrtle Beach", state="SC")
        newport = get_location_context(city="Newport", state="RI")
        self.assertEqual(myrtle["match_level"], "city_exact")
        self.assertTrue(newport["matched"])
        self.assertFalse(newport["availability"]["state_context"])
        self.assertTrue(newport["availability"]["swt_market"])
        self.assertIsNone(newport["state_context"])
        self.assertEqual(newport["swt_market"]["state_market"]["total"], 1030)

        result = calculate_position_overview({"offers": [
            make_offer("myrtle", "Myrtle Beach", city="Myrtle Beach", state="SC"),
            make_offer("newport", "Newport", city="Newport", state="RI"),
        ]})
        self.assertEqual(len(result["offers"]), 2)
        ri = next(item for item in result["offers"] if item["id"] == "newport")
        self.assertEqual(ri["state"], "RI")
        self.assertEqual(ri["cost_sources"]["rent_usd_per_week"], "global_estimate")
        self.assertIn("state_context 不可用的岗位仍可列入", SKILL_TEXT)
        self.assertIn("state_context 不可用但 swt_market 可用时继续分析", SKILL_TEXT)

    def test_high_vs_low_participant_counts_do_not_become_a_ranking_or_job_claim(self):
        high = get_location_context(city="Myrtle Beach", state="SC")
        low = get_location_context(city="Decatur", state="AL")
        high_count = high["swt_market"]["city_market"]["total"]
        low_count = low["swt_market"]["city_market"]["total"]
        self.assertGreater(high_count, low_count)
        self.assertEqual(low_count, 1)

        offers = [
            make_offer("high", "Higher count", city="Myrtle Beach", state="SC"),
            make_offer("low", "Lower count", city="Decatur", state="AL"),
        ]
        result = calculate_position_overview({"offers": offers})
        self.assertEqual(len(result["offers"]), 2)
        self.assertNotIn("participant_count", json.dumps(result, ensure_ascii=False))
        for prohibited in ("不用于 Offer 排序", "participant count 高低不得改变顺序", "不得据此推断工作好找、二工多"):
            self.assertIn(prohibited, SKILL_TEXT)

    def test_same_city_offers_can_reuse_context_but_keep_financial_inputs_separate(self):
        shared_context = get_location_context(city="Myrtle Beach", state="SC")
        self.assertEqual(shared_context["match_level"], "city_exact")
        self.assertIn("完全相同的规范化 city/state 可复用结果", SKILL_TEXT)

        result = calculate_position_overview({"offers": [
            make_offer("one", "Employer A", city="Myrtle Beach", state="SC", wage=14, hours=32, rent=110),
            make_offer("two", "Employer B", city="Myrtle Beach", state="SC", wage=18, hours=40, rent=160),
        ]})
        self.assertEqual(len(result["offers"]), 2)
        one, two = result["offers"]
        self.assertEqual((one["label"], one["wage_usd_per_hour"], one["weekly_costs_usd"]["rent_usd_per_week"]),
                         ("Employer A", "14.00", "110.00"))
        self.assertEqual((two["label"], two["wage_usd_per_hour"], two["weekly_costs_usd"]["rent_usd_per_week"]),
                         ("Employer B", "18.00", "160.00"))
        self.assertIn("在六维、回本和注意事项表中仍各自保留", SKILL_TEXT)

    def test_offer_without_location_in_mixed_comparison_keeps_missing_location_fallback(self):
        offers = [
            make_offer("unknown", "No location supplied"),
            make_offer("known", "Myrtle Beach", city="Myrtle Beach", state="SC"),
        ]
        located = [offer for offer in offers if offer.get("city") or offer.get("state")]
        contexts = [get_location_context(city=item.get("city"), state=item.get("state")) for item in located]
        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0]["match_level"], "city_exact")
        self.assertEqual(resolve_location()["match_level"], "location_not_provided")

        result = calculate_position_overview({"offers": offers})
        missing = next(item for item in result["offers"] if item["id"] == "unknown")
        self.assertIsNone(missing["state"])
        self.assertEqual(missing["cost_sources"]["rent_usd_per_week"], "global_estimate")
        self.assertIn("没有 city/state 的岗位不调用 Resolver", SKILL_TEXT)


if __name__ == "__main__":
    unittest.main()
