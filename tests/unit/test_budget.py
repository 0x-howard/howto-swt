#!/usr/bin/env python3
"""Deterministic budget and calculation unit tests."""
import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from compare_budget import calculate  # noqa: E402
from budget import (  # noqa: E402
    calculate_net_income, calculate_position_overview, format_calculation,
    format_position_detail, format_position_overview,
)

class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "assets/budget-example.json").read_text(encoding="utf-8"))

    def scenario(self):
        return self.data["offers"][0]["scenarios"]["base"]

    def result(self):
        return calculate(self.data)["offers"][0]["scenarios"]["base"]

    def test_independent_arithmetic(self):
        result = self.result()
        self.assertEqual(result["gross_earned_usd"], "4992.00")
        self.assertEqual(result["living_expenses_usd"], "3120.00")
        self.assertEqual(result["net_cash_change_usd"], "-1928.00")
        self.assertEqual(result["net_cash_change_cny"], "-13881.60")
        self.assertEqual(result["startup_cash_required_usd"], "4400.00")

    def test_first_pay_cash_not_double_counted(self):
        self.scenario()["cash_living_before_first_pay_usd"] += 100
        self.assertEqual(self.result()["net_cash_change_usd"], "-1928.00")
        self.assertEqual(self.result()["startup_cash_required_usd"], "4500.00")

    def test_refund_timing_and_unpaid_wages(self):
        self.scenario()["deposit_returned_by_end_usd"] = 300
        self.assertEqual(self.result()["net_cash_change_usd"], "-1628.00")
        self.scenario()["gross_pay_unreceived_usd"] = 200
        self.assertEqual(self.result()["net_cash_change_usd"], "-1828.00")

    def test_unknown_not_zero(self):
        for value in (None, "140", True, float("nan"), float("inf"), -1):
            with self.subTest(value=value):
                self.scenario()["housing_weekly_usd"] = value
                with self.assertRaises(ValueError):
                    calculate(self.data)

    def test_second_job_not_in_base(self):
        self.scenario()["second_job_income_usd"] = 1000
        with self.assertRaises(ValueError):
            calculate(self.data)

    def test_input_not_mutated_or_sorted(self):
        original = copy.deepcopy(self.data)
        result = calculate(self.data)
        self.assertEqual(self.data, original)
        self.assertEqual([x["id"] for x in result["offers"]], [x["id"] for x in original["offers"]])

    def test_budget_cli_smoke(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "budget.py"), "--json", str(ROOT / "assets/net-income-example.json")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"offers"', result.stdout)

class NetIncomeCalculatorTests(unittest.TestCase):
    def manual_offer(self, **overrides):
        offer = {
            "id": "offer-a",
            "label": "Offer A",
            "state": "Texas",
            "wage_usd_per_hour": 16,
            "hours_per_week": 40,
            "start_date": "2027-06-01",
            "end_date": "2027-09-01",
            "rent_usd_per_week": 150,
            "transport_usd_per_week": 10,
            "food_usd_per_week": 50,
            "other_fixed_usd": 100,
            "tax": {
                "federal_income_tax_percent": 10,
                "state_income_tax_percent": 0,
            },
        }
        offer.update(overrides)
        return offer

    def calculate(self, offers, tax_mode="manual_rates", fx=7.2):
        data = {"tax_mode": tax_mode, "offers": offers}
        if fx is not None:
            data["fx_cny_per_usd"] = fx
        return calculate_net_income(data)

    def test_dates_calculate_days_weeks_and_full_net_income(self):
        item = self.calculate([self.manual_offer()])["offers"][0]
        self.assertEqual(item["period"]["calendar_days"], 93)
        self.assertEqual(item["period"]["work_weeks"], "13.28571428571428571428571429")
        self.assertEqual(item["gross_income_usd"], "8502.86")
        self.assertEqual(item["estimated_taxes"]["total_usd"], "850.29")
        self.assertEqual(item["housing_cost_usd"], "1992.86")
        self.assertEqual(item["other_known_costs_usd"], "897.14")
        self.assertEqual(item["estimated_net_income_usd"], "4762.57")
        self.assertEqual(item["estimated_net_income_cny"], "34290.48")

    def test_date_and_direct_weeks_conflict_needs_confirmation(self):
        offer = self.manual_offer(work_weeks=13)
        item = self.calculate([offer])["offers"][0]
        self.assertEqual(item["calculation_status"], "needs_confirmation")
        self.assertEqual(item["period"]["status"], "needs_confirmation")
        self.assertIsNone(item.get("estimated_net_income_usd"))

    def test_manual_mode_never_defaults_federal_tax_rate(self):
        offer = self.manual_offer(tax={"state_income_tax_percent": 0})
        item = self.calculate([offer])["offers"][0]
        self.assertEqual(item["calculation_status"], "tax_pending")
        self.assertEqual(item["estimated_taxes"]["status"], "needs_rates")
        self.assertIsNone(item["estimated_taxes"]["total_usd"])
        self.assertIsNone(item["estimated_net_income_usd"])

    def test_data_assisted_texas_uses_only_documented_state_zero(self):
        offer = self.manual_offer(
            work_weeks=13,
            tax={"known_federal_income_tax_withheld_usd": 500},
        )
        offer.pop("start_date")
        offer.pop("end_date")
        item = self.calculate([offer], tax_mode="data_assisted", fx=None)["offers"][0]
        self.assertEqual(item["estimated_taxes"]["status"], "known_withholding")
        self.assertEqual(item["estimated_taxes"]["federal_income_tax_usd"], "500.00")
        self.assertEqual(item["estimated_taxes"]["state_income_tax_usd"], "0.00")
        self.assertEqual(item["estimated_net_income_usd"], "4990.00")
        self.assertIsNone(item["estimated_net_income_cny"])
        self.assertEqual(item["fx_status"], "needs_current_or_user_provided_rate")

    def test_data_assisted_nonzero_state_stays_pending_without_evidence(self):
        offer = self.manual_offer(
            state="California",
            work_weeks=13,
            tax={"known_federal_income_tax_withheld_usd": 500},
        )
        offer.pop("start_date")
        offer.pop("end_date")
        item = self.calculate([offer], tax_mode="data_assisted")["offers"][0]
        self.assertEqual(item["calculation_status"], "tax_pending")
        self.assertIn("州所得税", item["estimated_taxes"]["pending_components"])
        self.assertIsNone(item["estimated_net_income_usd"])

    def test_named_work_states_are_accepted_without_inventing_rates(self):
        expected_codes = {
            "Texas": "TX", "California": "CA", "South Carolina": "SC", "New York": "NY",
        }
        for state, code in expected_codes.items():
            with self.subTest(state=state):
                offer = self.manual_offer(state=state, work_weeks=13, tax={})
                offer.pop("start_date")
                offer.pop("end_date")
                item = self.calculate([offer], tax_mode="data_assisted")["offers"][0]
                self.assertEqual(item["state"], code)
                if code == "TX":
                    self.assertEqual(item["estimated_taxes"]["state_income_tax_usd"], "0.00")
                else:
                    self.assertIn("州所得税", item["estimated_taxes"]["pending_components"])

    def test_multiple_offers_compare_only_complete_net_estimates(self):
        data = json.loads((ROOT / "assets/net-income-example.json").read_text(encoding="utf-8"))
        result = calculate_net_income(data)
        self.assertEqual(result["comparison"]["status"], "complete")
        self.assertEqual(result["comparison"]["offers_with_net_estimate"], ["offer-a", "offer-b"])
        output = format_calculation(result)
        self.assertIn("Offer 比较", output)
        self.assertIn("Offer A", output)
        self.assertIn("按 ¥7.20 / $", output)

    def test_overtime_requires_explicit_rate(self):
        offer = self.manual_offer(overtime_hours_per_week=2)
        with self.assertRaises(ValueError):
            self.calculate([offer])

class PositionOverviewTests(unittest.TestCase):
    def setUp(self):
        self.defaults = json.loads((ROOT / "tests/unit/fixtures/position_assumptions.json").read_text(encoding="utf-8"))

    def overview(self, *offers, **top):
        state_fixture = {
            "常见周租": "$100–150/week",
            "每周基础开销": "$80–120/week",
            "好不好找": "一般偏难",
            "SSN": "一般",
        }
        with patch("budget._overview_defaults", return_value=copy.deepcopy(self.defaults)), \
                patch("budget._state_reference", side_effect=lambda state: state_fixture if state else {}):
            return calculate_position_overview({"offers": list(offers), **top})

    def test_minimal_wage_and_hours_generates_complete_answer(self):
        item = self.overview({"wage_usd_per_hour": 16, "hours_per_week": 32})["offers"][0]
        self.assertEqual(item["cost_sources"]["work_weeks"], "global_estimate")
        self.assertEqual(item["cost_sources"]["rent_usd_per_week"], "global_estimate")
        self.assertGreater(float(item["estimated_taxes"]["total_usd"]), 0)
        answer = format_position_overview(self.overview({"wage_usd_per_hour": 16, "hours_per_week": 32}))
        self.assertEqual(re.findall(r"(?m)^## \d\. ", answer), ["## 1. ", "## 2. ", "## 3. ", "## 4. ", "## 5. "])
        self.assertIn("## 3. 岗位收益函数 / ROI Comparison", answer)
        self.assertEqual(len(re.findall(r"(?m)^\|---(?:\|---)+\|$", answer)), 4)
        self.assertEqual(answer.count("?"), 0)
        self.assertEqual(answer.count("你接下来想先展开哪一项？"), 1)
        self.assertIn("最终预计结余", answer)

    def test_user_rent_overrides_defaults(self):
        item = self.overview({"wage_usd_per_hour": 16, "hours_per_week": 32, "rent_usd_per_week": 100})["offers"][0]
        self.assertEqual(item["weekly_costs_usd"]["rent_usd_per_week"], "100.00")
        self.assertEqual(item["cost_sources"]["rent_usd_per_week"], "provided")

    def test_state_living_cost_overrides_global(self):
        item = self.overview({"wage_usd_per_hour": 16, "hours_per_week": 32, "state": "AK"})["offers"][0]
        self.assertEqual(item["weekly_costs_usd"]["rent_usd_per_week"], "125.00")
        self.assertEqual(item["weekly_costs_usd"]["food_usd_per_week"], "100.00")
        self.assertEqual(item["cost_sources"]["food_usd_per_week"], "state_estimate")

    def test_two_offers_produce_six_rows_and_four_parallel_tables(self):
        result = self.overview(
            {"label": "甲", "wage_usd_per_hour": 16, "hours_per_week": 32},
            {"label": "乙", "wage_usd_per_hour": 17, "hours_per_week": 35},
        )
        answer = format_position_overview(result)
        self.assertEqual(answer.count("|---|---|---|"), 4)
        core = answer.split("## 1. 核心数据\n\n", 1)[1].split("## 2.", 1)[0]
        self.assertEqual(len(re.findall(r"(?m)^\| (?:收入|住宿|生活成本|交通|二工|落地便利) \|", core)), 6)

    def test_missing_caution_uses_dash(self):
        answer = format_position_overview(self.overview(
            {"label": "甲", "wage_usd_per_hour": 16, "hours_per_week": 32, "cautions": {"工时": "尚未保证"}},
            {"label": "乙", "wage_usd_per_hour": 17, "hours_per_week": 35},
        ))
        self.assertIn("| 工时 | 尚未保证 | - |", answer)

    def test_housing_followup_only_expands_housing(self):
        detail = format_position_detail(self.overview({"wage_usd_per_hour": 16, "hours_per_week": 32}), "housing")
        self.assertIn("住宿按", detail)
        self.assertNotIn("## 1.", detail)
        self.assertNotIn("餐饮", detail)
        self.assertNotIn("预计税费", detail)

    def test_hours_change_reuses_other_inputs(self):
        raw = {"wage_usd_per_hour": 16, "hours_per_week": 32, "rent_usd_per_week": 110, "food_usd_per_week": 60}
        before = self.overview(raw)["offers"][0]
        after = self.overview({**raw, "hours_per_week": 40})["offers"][0]
        self.assertEqual(before["weekly_costs_usd"], after["weekly_costs_usd"])
        self.assertEqual(before["cost_sources"], after["cost_sources"])
        self.assertGreater(float(after["final_project_surplus_usd"]), float(before["final_project_surplus_usd"]))

    def test_real_food_cost_overrides_estimate(self):
        before = self.overview({"wage_usd_per_hour": 16, "hours_per_week": 32})["offers"][0]
        after = self.overview({"wage_usd_per_hour": 16, "hours_per_week": 32, "food_usd_per_week": 45})["offers"][0]
        self.assertEqual(after["weekly_costs_usd"]["food_usd_per_week"], "45.00")
        self.assertEqual(after["cost_sources"]["food_usd_per_week"], "provided")
        self.assertGreater(float(after["final_project_surplus_usd"]), float(before["final_project_surplus_usd"]))

    def test_federal_tax_uses_brackets_not_a_permanent_flat_ten_percent(self):
        item = self.overview({"state": "TX", "wage_usd_per_hour": 100, "hours_per_week": 40})["offers"][0]
        self.assertEqual(item["gross_income_usd"], "52000.00")
        self.assertEqual(item["estimated_taxes"]["federal_income_tax_usd"], "6152.00")
        self.assertEqual(item["estimated_taxes"]["state_income_tax_usd"], "0.00")

    def test_city_value_precedes_state_value_when_configured(self):
        self.defaults["city_cost_overrides"]["AK|city a"] = {"rent_usd_per_week": 118}
        item = self.overview({"city": "City A", "state": "AK", "wage_usd_per_hour": 16, "hours_per_week": 32})["offers"][0]
        self.assertEqual(item["state"], "AK")
        self.assertEqual(item["weekly_costs_usd"]["rent_usd_per_week"], "118.00")
        self.assertEqual(item["cost_sources"]["rent_usd_per_week"], "city_estimate")
        self.assertEqual(item["cost_sources"]["food_usd_per_week"], "state_estimate")

    def test_user_dates_precede_offer_dates_and_weeks(self):
        item = self.overview({
            "wage_usd_per_hour": 16, "hours_per_week": 32,
            "start_date": "2026-06-01", "end_date": "2026-08-30",
            "offer_start_date": "2026-06-10", "offer_end_date": "2026-09-10", "work_weeks": 13,
        })["offers"][0]
        self.assertEqual(item["cost_sources"]["work_weeks"], "user_dates")
        self.assertEqual(item["work_weeks"], "13.00")

    def test_exact_fallback_arithmetic_uses_test_fixture(self):
        item = self.overview({"wage_usd_per_hour": 16, "hours_per_week": 20})["offers"][0]
        self.assertEqual(item["gross_income_usd"], "4160.00")
        self.assertEqual(item["estimated_taxes"]["federal_income_tax_usd"], "416.00")
        self.assertEqual(item["estimated_taxes"]["state_income_tax_usd"], "208.00")
        self.assertEqual(item["estimated_us_net_usd"], "1391.00")
        self.assertEqual(item["final_project_surplus_usd"], "91.00")
        self.assertEqual(item["break_even_work_weeks"], "12.20")
