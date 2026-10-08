#!/usr/bin/env python3
"""Deterministic linear Offer Return Function analysis for SWT positions."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


ZERO = Decimal("0")
EPSILON = Decimal("0.0000001")
MAX_CHART_OFFERS = 3


def _d(value: Any, path: str, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(f"{path}: requires a number")
    try:
        number = Decimal(str(value))
    except Exception as error:
        raise ValueError(f"{path}: requires a number") from error
    if not number.is_finite() or number < ZERO or (positive and number == ZERO):
        raise ValueError(f"{path}: requires a {'positive' if positive else 'nonnegative'} finite number")
    return number


def _s(value: Decimal | None, places: str = ".01") -> str | None:
    return None if value is None else str(value.quantize(Decimal(places), rounding=ROUND_HALF_UP))


def _value(function: dict[str, Any], hours: Decimal) -> Decimal:
    return Decimal(function["slope_after_tax_usd_per_hour"]) * hours + Decimal(function["intercept_weekly_cost_usd"])


def build_offer_function(offer: dict[str, Any]) -> dict[str, Any]:
    """Create y=ax+b from one completed position-overview offer."""
    wage = _d(offer["wage_usd_per_hour"], "offer.wage", positive=True)
    expected = _d(offer["hours_range"]["expected"], "offer.hours.expected", positive=True)
    gross = _d(offer["gross_income_usd"], "offer.gross")
    tax = _d(offer["estimated_taxes"]["total_usd"], "offer.tax")
    rate = tax / gross if gross > ZERO else ZERO
    if rate >= Decimal("1"):
        raise ValueError("offer tax estimate must be less than gross income")
    weekly_cost = sum(_d(value, f"offer.weekly_costs.{key}") for key, value in offer["weekly_costs_usd"].items())
    slope = wage * (Decimal("1") - rate)
    intercept = -weekly_cost
    expected_net = slope * expected + intercept
    break_even_hours = weekly_cost / slope if slope > ZERO else None
    return {
        "id": offer["id"],
        "label": offer["label"],
        "formula": f"y = {_s(slope, '.0001')}x - {_s(weekly_cost)}",
        "slope_after_tax_usd_per_hour": _s(slope, ".0001"),
        "intercept_weekly_cost_usd": _s(intercept),
        "effective_tax_rate": _s(rate, ".000001"),
        "weekly_cost_usd": _s(weekly_cost),
        "weekly_cost_components_usd": dict(offer["weekly_costs_usd"]),
        "hours": dict(offer["hours_range"]),
        "expected_weekly_net_surplus_usd": _s(expected_net),
        "weekly_break_even_hours": _s(break_even_hours),
        "estimated_inputs": sorted(
            key for key, source in offer["cost_sources"].items()
            if source not in {"provided", "provided_rate", "provided_weeks", "user_dates", "offer_dates"}
        ),
        "key_risks": list(offer.get("cautions", {}).values())[:2],
    }


def pairwise_intersections(functions: list[dict[str, Any]], minimum: Decimal, maximum: Decimal) -> list[dict[str, Any]]:
    intersections: list[dict[str, Any]] = []
    for left_index, left in enumerate(functions):
        for right in functions[left_index + 1:]:
            a1, a2 = Decimal(left["slope_after_tax_usd_per_hour"]), Decimal(right["slope_after_tax_usd_per_hour"])
            b1, b2 = Decimal(left["intercept_weekly_cost_usd"]), Decimal(right["intercept_weekly_cost_usd"])
            if abs(a1 - a2) <= EPSILON:
                continue
            hours = (b2 - b1) / (a1 - a2)
            if minimum <= hours <= maximum:
                intersections.append({
                    "offers": [left["id"], right["id"]],
                    "hours_per_week": _s(hours),
                    "weekly_net_surplus_usd": _s(a1 * hours + b1),
                })
    return sorted(intersections, key=lambda item: (Decimal(item["hours_per_week"]), item["offers"]))


def _winners(functions: list[dict[str, Any]], hours: Decimal) -> list[str]:
    values = [(function["id"], _value(function, hours)) for function in functions]
    best = max(value for _, value in values)
    return sorted(identifier for identifier, value in values if abs(value - best) <= EPSILON)


def upper_envelope(functions: list[dict[str, Any]], minimum: Decimal, maximum: Decimal, intersections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    points = sorted({minimum, maximum, *(Decimal(item["hours_per_week"]) for item in intersections)})
    regions: list[dict[str, Any]] = []
    for left, right in zip(points, points[1:]):
        if right - left <= EPSILON:
            continue
        winners = _winners(functions, (left + right) / Decimal("2"))
        if regions and regions[-1]["best_offer_ids"] == winners and Decimal(regions[-1]["max_hours"]) == left:
            regions[-1]["max_hours"] = _s(right)
        else:
            regions.append({"min_hours": _s(left), "max_hours": _s(right), "best_offer_ids": winners})
    if minimum == maximum:
        regions.append({"min_hours": _s(minimum), "max_hours": _s(maximum), "best_offer_ids": _winners(functions, minimum)})
    return regions


def dominated_offers(functions: list[dict[str, Any]], minimum: Decimal, maximum: Decimal) -> list[dict[str, str]]:
    dominated: list[dict[str, str]] = []
    for target in functions:
        for challenger in functions:
            if target is challenger:
                continue
            if all(_value(target, x) < _value(challenger, x) - EPSILON for x in (minimum, maximum)):
                dominated.append({"offer_id": target["id"], "dominated_by": challenger["id"]})
                break
    return dominated


def calculate_offer_return_analysis(offers: list[dict[str, Any]], comparison_hours: dict[str, Any] | None = None) -> dict[str, Any]:
    if not offers:
        raise ValueError("offers: requires at least one offer")
    functions = [build_offer_function(offer) for offer in offers]
    if len(functions) > MAX_CHART_OFFERS:
        ranking = [item["id"] for item in sorted(functions, key=lambda item: Decimal(item["expected_weekly_net_surplus_usd"]), reverse=True)]
        return {
            "schema_version": "1.0",
            "model": "weekly_hours_to_weekly_net_surplus",
            "functions": functions,
            "analysis_status": "selection_required",
            "selection": {"type": "multi_choice", "max_selections": 3, "offer_ids": [item["id"] for item in functions]},
            "ranking_by_expected_weekly_net_surplus": ranking,
            "visualization": {"status": "not_generated", "reason": "more_than_three_offers"},
        }

    if comparison_hours is not None:
        if not isinstance(comparison_hours, dict) or set(comparison_hours) != {"min", "max"}:
            raise ValueError("comparison_hours must contain exactly min and max")
        minimum = _d(comparison_hours["min"], "comparison_hours.min")
        maximum = _d(comparison_hours["max"], "comparison_hours.max")
        range_source = "provided_comparison_range"
    else:
        complete_ranges = [item["hours"] for item in functions if item["hours"].get("min") is not None and item["hours"].get("max") is not None]
        if len(complete_ranges) != len(functions):
            return {
                "schema_version": "1.0", "model": "weekly_hours_to_weekly_net_surplus",
                "functions": functions, "analysis_status": "point_only",
                "hours_range": None, "intersections": [], "optimal_regions": [], "dominated_offers": [],
                "visualization": {"status": "textual_fallback", "reason": "credible_shared_hours_range_missing"},
            }
        minimum = min(_d(item["min"], "hours.min") for item in complete_ranges)
        maximum = max(_d(item["max"], "hours.max") for item in complete_ranges)
        range_source = "offer_ranges"
    if minimum > maximum or maximum > Decimal("168"):
        raise ValueError("hours range must satisfy 0 <= min <= max <= 168")
    intersections = pairwise_intersections(functions, minimum, maximum)
    regions = upper_envelope(functions, minimum, maximum, intersections)
    meaningful_boundaries = {region["max_hours"] for region in regions[:-1]}
    for item in intersections:
        item["meaningful_for_optimum"] = item["hours_per_week"] in meaningful_boundaries
    return {
        "schema_version": "1.0", "model": "weekly_hours_to_weekly_net_surplus",
        "x_axis": "average_weekly_hours", "y_axis": "estimated_weekly_net_surplus_usd",
        "functions": functions, "analysis_status": "complete",
        "hours_range": {"min": _s(minimum), "max": _s(maximum), "source": range_source},
        "intersections": intersections,
        "optimal_regions": regions,
        "dominated_offers": dominated_offers(functions, minimum, maximum),
        "visualization": {
            "status": "structured_chart_ready", "type": "linear_offer_return",
            "x_axis": "Average Weekly Hours", "y_axis": "Estimated Weekly Net Surplus",
            "range_shading": {"min": _s(minimum), "max": _s(maximum)},
            "expected_hours": {item["id"]: item["hours"]["expected"] for item in functions},
        },
    }


def maximum_acceptable_rent(wage: Any, weekly_hours: Any, effective_tax_rate: Any, other_weekly_cost: Any, target_savings: Any) -> dict[str, str]:
    w = _d(wage, "wage", positive=True)
    hours = _d(weekly_hours, "weekly_hours", positive=True)
    rate = _d(effective_tax_rate, "effective_tax_rate")
    if rate >= Decimal("1"):
        raise ValueError("effective_tax_rate must be less than 1")
    other = _d(other_weekly_cost, "other_weekly_cost")
    target = _d(target_savings, "target_savings")
    rent = hours * (Decimal("1") - rate) * w - other - target
    return {"maximum_acceptable_rent_usd_per_week": _s(rent), "formula": "rent = H(1-t)w - other_cost - target_savings"}
