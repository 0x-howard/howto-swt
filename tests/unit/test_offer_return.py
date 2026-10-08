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


def offer(identifier, wage, cost, *, expected=32, minimum=20, maximum=40, rate=0, estimated=False):
    gross = Decimal(str(wage)) * Decimal(str(expected)) * Decimal("10")
    tax = gross * Decimal(str(rate))
    return {
        "id": identifier, "label": f"Offer {identifier}",
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

    def test_expected_hours_point(self):
        function = build_offer_function(offer("A", 10, 100, expected=32))
        self.assertEqual(function["expected_weekly_net_surplus_usd"], "220.00")

    def test_hours_range_and_missing_range(self):
        complete = calculate_offer_return_analysis([offer("A", 10, 100, minimum=26, maximum=38)])
        self.assertEqual(complete["hours_range"]["min"], "26.00")
        point = calculate_offer_return_analysis([offer("A", 10, 100, minimum=None, maximum=None)])
        self.assertEqual(point["analysis_status"], "point_only")

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

    def test_visualization_fallback_and_determinism(self):
        data = [offer("A", 10, 100, minimum=None, maximum=None)]
        first = calculate_offer_return_analysis(data)
        self.assertEqual(first["visualization"]["status"], "textual_fallback")
        self.assertEqual(first, calculate_offer_return_analysis(data))

    def test_maximum_acceptable_rent_boundary(self):
        result = maximum_acceptable_rent(20, 30, "0.1", 100, 200)
        self.assertEqual(result["maximum_acceptable_rent_usd_per_week"], "240.00")


if __name__ == "__main__":
    unittest.main()
