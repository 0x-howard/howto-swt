#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from budget import calculate_position_overview  # noqa: E402
from interaction import adapt_request, offer_selection_request, plan_interaction, validate_selection  # noqa: E402


def raw_offer(identifier, wage, rent, expected=32):
    return {
        "id": identifier, "label": f"Offer {identifier}", "state": "TX",
        "wage_usd_per_hour": wage, "expected_hours": expected, "min_hours": 20, "max_hours": 60,
        "work_weeks": 12, "rent_usd_per_week": rent, "food_usd_per_week": 0,
        "transport_usd_per_week": 0, "other_weekly_usd": 0, "project_cost_usd": 0,
        "tax": {"federal_income_tax_percent": 0, "state_income_tax_percent": 0, "fica_percent": 0},
    }


class OfferInteractionE2E(unittest.TestCase):
    def test_five_offers_select_three_recalculate_and_reuse_known_context(self):
        offers = [
            raw_offer("A", 10, 100), raw_offer("B", 12, 160), raw_offer("C", 15, 250),
            raw_offer("D", 17, 340), raw_offer("E", 20, 500),
        ]
        first = calculate_position_overview({"mode": "position_overview", "offers": offers})
        analysis = first["offer_return_analysis"]
        self.assertEqual(analysis["analysis_status"], "selection_required")
        self.assertEqual(len(analysis["functions"]), 5)

        request = offer_selection_request(analysis["functions"])
        fallback = adapt_request(request, {
            "host": "doubao-work", "native_interface": None,
            "supports_single_choice": False, "supports_multi_choice": False,
            "supports_free_text": False, "supports_structured_form": False,
            "supports_confirmation": False,
        })
        self.assertEqual(fallback["delivery"], "text_fallback")
        selected = validate_selection(request, ["A", "C", "E"])["selected_ids"]
        subset = [item for item in offers if item["id"] in selected]

        compared = calculate_position_overview({"mode": "position_overview", "offers": subset})
        functions = compared["offer_return_analysis"]
        self.assertEqual(len(functions["functions"]), 3)
        self.assertGreaterEqual(len(functions["intersections"]), 2)
        self.assertGreaterEqual(len(functions["optimal_regions"]), 2)

        changed = [dict(item, expected_hours=40) if item["id"] == "E" else item for item in subset]
        changed_result = calculate_position_overview({"mode": "position_overview", "offers": changed})
        old_e = next(item for item in functions["functions"] if item["id"] == "E")
        new_e = next(item for item in changed_result["offer_return_analysis"]["functions"] if item["id"] == "E")
        self.assertNotEqual(old_e["expected_weekly_net_surplus_usd"], new_e["expected_weekly_net_surplus_usd"])
        self.assertEqual(old_e["slope_after_tax_usd_per_hour"], new_e["slope_after_tax_usd_per_hour"])
        self.assertEqual(old_e["weekly_cost_usd"], new_e["weekly_cost_usd"])
        resumed = plan_interaction("CLARIFY", "enum", request, fact_key="selected_offer_ids", confirmed_context_keys=["selected_offer_ids"])
        self.assertEqual(resumed["action"], "direct")


if __name__ == "__main__":
    unittest.main()
