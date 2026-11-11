#!/usr/bin/env python3

import sys
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from offer_return import (  # noqa: E402
    MAX_CHART_OFFERS,
    build_offer_function,
    calculate_offer_return_analysis,
    maximum_acceptable_rent,
)


def offer(identifier, wage, cost, *, expected=32, minimum=20, maximum=40, rate=0, estimated=False, weeks=10):
    gross = Decimal(str(wage)) * Decimal(str(expected)) * Decimal(str(weeks))
    tax = gross * Decimal(str(rate))
    return {
        "id": identifier, "label": f"Offer {identifier}",
        "work_weeks": str(weeks), "estimated_us_net_usd": str(gross - tax - Decimal(str(cost)) * Decimal(str(weeks))),
        "wage_usd_per_hour": str(wage), "gross_income_usd": str(gross),
        "estimated_taxes": {"total_usd": str(tax)},
        "weekly_costs_usd": {
            "rent_usd_per_week": str(cost), "food_usd_per_week": "0",
            "transport_usd_per_week": "0", "other_weekly_usd": "0",
        },
        "cost_sources": {
            "rent_usd_per_week": "global_estimate" if estimated else "provided",
            "food_usd_per_week": "provided", "transport_usd_per_week": "provided",
            "other_weekly_usd": "provided", "work_weeks": "provided_weeks",
            "project_cost": "provided", "fx": "provided",
        },
        "hours_range": {
            "min": None if minimum is None else str(minimum), "expected": str(expected),
            "max": None if maximum is None else str(maximum),
            "status": "point_only" if minimum is None else "provided_range", "basis": None,
        },
    }


class OfferReturnFunctionTests(unittest.TestCase):
    def test_single_offer(self):
        result = calculate_offer_return_analysis([offer("A", 15, 200)])
        self.assertEqual(len(result["functions"]), 1)
        self.assertEqual(result["analysis_status"], "complete")

    def test_two_and_three_offers(self):
        self.assertEqual(len(calculate_offer_return_analysis([offer("A", 10, 100), offer("B", 15, 250)])["functions"]), 2)
        self.assertEqual(len(calculate_offer_return_analysis([offer("A", 10, 100), offer("B", 15, 250), offer("C", 20, 500)])["functions"]), 3)

    def test_more_than_three_requires_selection(self):
        result = calculate_offer_return_analysis([offer(str(i), 10 + i, 100) for i in range(4)])
        self.assertEqual(result["analysis_status"], "selection_required")
        self.assertEqual(result["selection"]["max_selections"], MAX_CHART_OFFERS)

    def test_parallel_functions_have_no_intersection(self):
        result = calculate_offer_return_analysis([offer("A", 15, 100), offer("B", 15, 200)])
        self.assertEqual(result["intersections"], [])

    def test_one_meaningful_intersection(self):
        result = calculate_offer_return_analysis([offer("A", 10, 100), offer("B", 15, 250)])
        self.assertEqual(result["intersections"][0]["hours_per_week"], "30.00")
        self.assertTrue(result["intersections"][0]["meaningful_for_optimum"])

    def test_multiple_intersections(self):
        result = calculate_offer_return_analysis([offer("A", 10, 100, maximum=60), offer("B", 15, 250, maximum=60), offer("C", 20, 500, maximum=60)])
        self.assertGreaterEqual(len(result["intersections"]), 3)

    def test_intersection_outside_range_is_hidden(self):
        result = calculate_offer_return_analysis([offer("A", 10, 100), offer("B", 11, 200)])
        self.assertEqual(result["intersections"], [])

    def test_fully_dominated_offer_is_retained_and_marked(self):
        result = calculate_offer_return_analysis([offer("A", 10, 200), offer("B", 12, 100)])
        self.assertEqual(result["dominated_offers"], [{"offer_id": "A", "dominated_by": "B"}])
        self.assertEqual(len(result["functions"]), 2)

    def test_longer_season_is_counted(self):
        shorter = offer("A", 12, 100, expected=40, minimum=40, maximum=40, weeks=10)
        longer = offer("B", 12, 100, expected=40, minimum=40, maximum=40, weeks=12)
        result = calculate_offer_return_analysis([shorter, longer])
        self.assertEqual(result["dominated_offers"], [{"offer_id": "A", "dominated_by": "B"}])

    def test_fixed_hours_offer_is_not_judged_at_other_hours(self):
        variable = offer("A", 15.5, 150, expected=36, minimum=32, maximum=40, weeks=13)
        fixed = offer("B", 14, 125, expected=40, minimum=40, maximum=40, weeks=12)
        result = calculate_offer_return_analysis([variable, fixed])
        self.assertEqual(result["dominated_offers"], [])
        self.assertEqual(len(result["intersections"]), 1)
        crossing = Decimal(result["intersections"][0]["hours_per_week"])
        self.assertTrue(Decimal("32") < crossing < Decimal("40"))
        self.assertEqual(result["optimal_regions"][-1]["best_offer_ids"], ["A"])

    def test_expected_hours_point(self):
        function = build_offer_function(offer("A", 10, 100, expected=32))
        self.assertEqual(function["expected_weekly_net_surplus_usd"], "220.00")

    def test_hours_range_and_missing_range(self):
        complete = calculate_offer_return_analysis([offer("A", 10, 100, minimum=26, maximum=38)])
        self.assertEqual(complete["hours_range"]["min"], "26.00")
        point = calculate_offer_return_analysis([offer("A", 10, 100, minimum=None, maximum=None)])
        self.assertEqual(point["analysis_status"], "complete")
        self.assertEqual(point["hours_range"], {"min": "24.00", "max": "40.00", "source": "display_range_around_expected"})

    def test_estimated_inputs_are_labeled(self):
        function = build_offer_function(offer("A", 10, 100, estimated=True))
        self.assertIn("rent_usd_per_week", function["estimated_inputs"])

    def test_zero_or_negative_weekly_surplus_is_valid(self):
        function = build_offer_function(offer("A", 10, 500, expected=20))
        self.assertEqual(function["expected_weekly_net_surplus_usd"], "-300.00")

    def test_invalid_tax_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "less than gross"):
            build_offer_function(offer("A", 10, 100, rate=1))

    def test_weekly_break_even(self):
        self.assertEqual(build_offer_function(offer("A", 10, 100))["weekly_break_even_hours"], "10.00")

    def test_taxes_reduce_slope(self):
        no_tax = Decimal(build_offer_function(offer("A", 20, 100, rate=0))["slope_after_tax_usd_per_hour"])
        taxed = Decimal(build_offer_function(offer("A", 20, 100, rate="0.2"))["slope_after_tax_usd_per_hour"])
        self.assertEqual((no_tax, taxed), (Decimal("20.0000"), Decimal("16.0000")))

    def test_housing_changes_intercept_only(self):
        low = build_offer_function(offer("A", 15, 100))
        high = build_offer_function(offer("A", 15, 200))
        self.assertEqual(low["slope_after_tax_usd_per_hour"], high["slope_after_tax_usd_per_hour"])
        self.assertNotEqual(low["intercept_weekly_cost_usd"], high["intercept_weekly_cost_usd"])

    def test_wage_changes_slope(self):
        low = build_offer_function(offer("A", 10, 100))
        high = build_offer_function(offer("A", 15, 100))
        self.assertNotEqual(low["slope_after_tax_usd_per_hour"], high["slope_after_tax_usd_per_hour"])

    def test_chart_points_and_determinism(self):
        data = [offer("A", 10, 100, minimum=None, maximum=None), offer("B", 12, 200, minimum=None, maximum=None)]
        first = calculate_offer_return_analysis(data)
        self.assertEqual(first["chart"]["hours"][0], "24")
        self.assertEqual(first["chart"]["hours"][-1], "40")
        self.assertEqual(first["chart"]["series"][0]["values"][-1], "3000")
        self.assertEqual(first, calculate_offer_return_analysis(data))

    def test_project_cost_moves_chart_to_final_surplus(self):
        data = [offer("A", 10, 100), offer("B", 12, 200)]
        for item in data:
            item["project_cost_usd"] = "1000"
        chart = calculate_offer_return_analysis(data)["chart"]
        self.assertEqual(chart["y_basis"], "final_project_surplus")
        self.assertEqual(chart["series"][0]["values"][-1], "2000")

    def test_maximum_acceptable_rent_boundary(self):
        result = maximum_acceptable_rent(20, 30, "0.1", 100, 200)
        self.assertEqual(result["maximum_acceptable_rent_usd_per_week"], "240.00")


if __name__ == "__main__":
    unittest.main()
