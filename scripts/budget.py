#!/usr/bin/env python3
"""Deterministic SWT estimated-net-income calculator.

This script estimates one first-job SWT work period from explicit offer inputs. It
does not fetch tax rates, file taxes, or treat payroll withholding as final tax
liability. It is deliberately usable for one or multiple offers.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from paths import DEFAULT_ASSUMPTIONS_PATH


ZERO = Decimal("0")
WEEK = Decimal("7")


def round_searched_fx(value: Any) -> Decimal:
    """Round a searched quote up to one decimal; never apply to user rates."""
    rate = _number(value, "searched_fx", positive=True)
    return ((rate * 10).to_integral_value(rounding=ROUND_CEILING) / 10).quantize(Decimal(".1"))


STATE_ALIASES = {
    "alabama": "AL", "al": "AL", "alaska": "AK", "ak": "AK",
    "arizona": "AZ", "az": "AZ", "arkansas": "AR", "ar": "AR",
    "california": "CA", "ca": "CA", "colorado": "CO", "co": "CO",
    "connecticut": "CT", "ct": "CT", "delaware": "DE", "de": "DE",
    "florida": "FL", "fl": "FL", "georgia": "GA", "ga": "GA",
    "hawaii": "HI", "hi": "HI", "idaho": "ID", "id": "ID",
    "illinois": "IL", "il": "IL", "indiana": "IN", "in": "IN",
    "iowa": "IA", "ia": "IA", "kansas": "KS", "ks": "KS",
    "kentucky": "KY", "ky": "KY", "louisiana": "LA", "la": "LA",
    "maine": "ME", "me": "ME", "maryland": "MD", "md": "MD",
    "massachusetts": "MA", "ma": "MA", "michigan": "MI", "mi": "MI",
    "minnesota": "MN", "mn": "MN", "mississippi": "MS", "ms": "MS",
    "missouri": "MO", "mo": "MO", "montana": "MT", "mt": "MT",
    "nebraska": "NE", "ne": "NE", "nevada": "NV", "nv": "NV",
    "new hampshire": "NH", "nh": "NH", "new jersey": "NJ", "nj": "NJ",
    "new mexico": "NM", "nm": "NM", "new york": "NY", "ny": "NY",
    "north carolina": "NC", "nc": "NC", "north dakota": "ND", "nd": "ND",
    "ohio": "OH", "oh": "OH", "oklahoma": "OK", "ok": "OK",
    "oregon": "OR", "or": "OR", "pennsylvania": "PA", "pa": "PA",
    "rhode island": "RI", "ri": "RI", "south carolina": "SC", "sc": "SC",
    "south dakota": "SD", "sd": "SD", "tennessee": "TN", "tn": "TN",
    "texas": "TX", "tx": "TX", "utah": "UT", "ut": "UT",
    "vermont": "VT", "vt": "VT", "virginia": "VA", "va": "VA",
    "washington": "WA", "wa": "WA", "west virginia": "WV", "wv": "WV",
    "wisconsin": "WI", "wi": "WI", "wyoming": "WY", "wy": "WY",
}

# Only states whose zero wage personal-income-tax status is documented in
# references/state-income-tax.md. More states may be added only with a dated
# primary source, not by guessing a rate.
ASSISTED_ZERO_STATE_INCOME_TAX = {
    "TX": {"state": "Texas", "source": "Texas Comptroller, A Field Guide to the Taxes of Texas (FY 2025): no state or local income tax."},
    "AK": {"state": "Alaska", "source": "Alaska Department of Revenue/Treasury: no personal income tax."},
    "FL": {"state": "Florida", "source": "Florida Department of Revenue GT-800025: no personal income tax."},
    "NV": {"state": "Nevada", "source": "Nevada Department of Taxation: no state tax on salaries or wages."},
    "SD": {"state": "South Dakota", "source": "South Dakota Department of Revenue: no state income tax."},
    "TN": {"state": "Tennessee", "source": "Tennessee Department of Revenue GEN-34: no state income tax on earned income."},
    "WA": {"state": "Washington", "source": "Washington Department of Revenue: no individual income tax before 2028."},
    "WY": {"state": "Wyoming", "source": "Wyoming Legislature tax structure (June 2025): individual income tax 0%."},
    "NH": {"state": "New Hampshire", "source": "New Hampshire DRA: no income tax on W-2 wages."},
}


def _money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value.quantize(Decimal(".01"), rounding=ROUND_HALF_UP))


def _number(value: Any, path: str, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{path}: requires an explicit number")
    result = Decimal(str(value))
    if not result.is_finite() or result < ZERO or (positive and result == ZERO):
        qualifier = "positive finite" if positive else "finite nonnegative"
        raise ValueError(f"{path}: requires a {qualifier} number")
    return result


def _optional_number(data: dict[str, Any], key: str, path: str) -> Decimal | None:
    if key not in data:
        return None
    return _number(data[key], f"{path}.{key}")


def _exact_keys(data: dict[str, Any], allowed: set[str], required: set[str], path: str) -> None:
    unknown = set(data) - allowed
    missing = required - set(data)
    if unknown or missing:
        raise ValueError(f"{path}: missing={sorted(missing)}, unexpected={sorted(unknown)}")


def _state_code(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: requires a U.S. state name or abbreviation")
    normalized = " ".join(value.lower().replace(".", "").split())
    if normalized not in STATE_ALIASES:
        raise ValueError(f"{path}: unsupported or unrecognized U.S. state")
    return STATE_ALIASES[normalized]


def _period(raw: dict[str, Any], path: str) -> dict[str, Any]:
    has_start, has_end, has_weeks = "start_date" in raw, "end_date" in raw, "work_weeks" in raw
    if has_start != has_end:
        raise ValueError(f"{path}: start_date and end_date must be provided together")
    if not has_start and not has_weeks:
        raise ValueError(f"{path}: provide start_date/end_date or work_weeks")

    date_weeks: Decimal | None = None
    calendar_days: int | None = None
    if has_start:
        if not isinstance(raw["start_date"], str) or not isinstance(raw["end_date"], str):
            raise ValueError(f"{path}: dates must use YYYY-MM-DD")
        start, end = date.fromisoformat(raw["start_date"]), date.fromisoformat(raw["end_date"])
        if end < start:
            raise ValueError(f"{path}: end_date must be on or after start_date")
        # A supplied end date is treated as the expected last paid work day.
        calendar_days = (end - start).days + 1
        date_weeks = Decimal(calendar_days) / WEEK

    supplied_weeks = _number(raw["work_weeks"], f"{path}.work_weeks", positive=True) if has_weeks else None
    if date_weeks is not None and supplied_weeks is not None and abs(date_weeks - supplied_weeks) > Decimal("0.01"):
        return {
            "status": "needs_confirmation",
            "calendar_days": calendar_days,
            "date_calculated_weeks": str(date_weeks),
            "provided_work_weeks": str(supplied_weeks),
            "message": "日期换算的工作周数与直接输入周数冲突；请确认以哪个口径计算。",
        }

    weeks = supplied_weeks if supplied_weeks is not None else date_weeks
    assert weeks is not None
    return {
        "status": "ready",
        "calendar_days": calendar_days,
        "work_weeks": str(weeks),
        "period_basis": "dates_inclusive" if date_weeks is not None else "provided_work_weeks",
    }


def _tax(raw: dict[str, Any], gross: Decimal, state: str, mode: str, path: str) -> dict[str, Any]:
    allowed = {
        "federal_income_tax_percent", "state_income_tax_percent",
        "known_federal_income_tax_withheld_usd", "known_state_income_tax_withheld_usd",
        "known_other_payroll_withheld_usd",
    }
    _exact_keys(raw, allowed, set(), path)
    if mode == "manual_rates":
        required = ("federal_income_tax_percent", "state_income_tax_percent")
        if any(key not in raw for key in required):
            return {
                "status": "needs_rates",
                "total_usd": None,
                "message": "简易估算模式需要用户明确提供联邦税率和州所得税率；不会默认 10%。",
            }
        federal_rate = _number(raw["federal_income_tax_percent"], f"{path}.federal_income_tax_percent")
        state_rate = _number(raw["state_income_tax_percent"], f"{path}.state_income_tax_percent")
        if federal_rate > 100 or state_rate > 100:
            raise ValueError(f"{path}: tax percentages cannot exceed 100")
        other = _optional_number(raw, "known_other_payroll_withheld_usd", path) or ZERO
        federal = gross * federal_rate / Decimal("100")
        state_tax = gross * state_rate / Decimal("100")
        total = federal + state_tax + other
        return {
            "status": "manual_rate_estimate",
            "federal_income_tax_usd": _money(federal),
            "state_income_tax_usd": _money(state_tax),
            "other_known_payroll_withheld_usd": _money(other),
            "total_usd": _money(total),
            "message": "这是用户设定的估算税率，不代表最终实际税额、工资单扣缴或退税。",
        }

    federal = _optional_number(raw, "known_federal_income_tax_withheld_usd", path)
    state_tax = _optional_number(raw, "known_state_income_tax_withheld_usd", path)
    other = _optional_number(raw, "known_other_payroll_withheld_usd", path) or ZERO
    bases: list[str] = []
    if federal is not None:
        bases.append("联邦金额来自用户提供的工资单／雇主扣缴信息，不等于最终联邦税负。")
    if state_tax is not None:
        bases.append("州金额来自用户提供的工资单／雇主扣缴信息，不等于最终州税负。")
    elif state in ASSISTED_ZERO_STATE_INCOME_TAX:
        state_tax = ZERO
        bases.append(f"{ASSISTED_ZERO_STATE_INCOME_TAX[state]['state']} 的工资州个人所得税按本地已核验来源暂估为 0。")

    missing: list[str] = []
    if federal is None:
        missing.append("联邦所得税")
    if state_tax is None:
        missing.append("州所得税")
    if missing:
        return {
            "status": "needs_verification",
            "federal_income_tax_usd": _money(federal),
            "state_income_tax_usd": _money(state_tax),
            "other_known_payroll_withheld_usd": _money(other),
            "total_usd": None,
            "pending_components": missing,
            "message": "数据辅助模式不会根据时薪自行猜测税率；请提供工资单扣缴、适用税率或当前官方核验结果。",
            "basis": bases,
        }

    total = federal + state_tax + other
    return {
        "status": "known_withholding",
        "federal_income_tax_usd": _money(federal),
        "state_income_tax_usd": _money(state_tax),
        "other_known_payroll_withheld_usd": _money(other),
        "total_usd": _money(total),
        "message": "这是已知／辅助的工资单扣缴估算，不等于最终税负或退税。",
        "basis": bases,
    }


def _offer(raw: dict[str, Any], tax_mode: str, fx: Decimal | None, path: str) -> dict[str, Any]:
    allowed = {
        "id", "label", "state", "wage_usd_per_hour", "hours_per_week", "rent_usd_per_week",
        "start_date", "end_date", "work_weeks", "overtime_hours_per_week",
        "overtime_wage_usd_per_hour", "transport_usd_per_week", "food_usd_per_week",
        "other_weekly_usd", "other_fixed_usd", "tax",
    }
    required = {"id", "label", "state", "wage_usd_per_hour", "hours_per_week", "rent_usd_per_week", "tax"}
    _exact_keys(raw, allowed, required, path)
    if not isinstance(raw["id"], str) or not raw["id"].strip() or not isinstance(raw["label"], str) or not raw["label"].strip():
        raise ValueError(f"{path}: id and label require nonempty strings")
    if not isinstance(raw["tax"], dict):
        raise ValueError(f"{path}.tax: requires an object")

    period = _period(raw, path)
    state = _state_code(raw["state"], f"{path}.state")
    output: dict[str, Any] = {"id": raw["id"], "label": raw["label"], "state": state, "period": period}
    if period["status"] != "ready":
        output["calculation_status"] = "needs_confirmation"
        return output

    weeks = Decimal(period["work_weeks"])
    wage = _number(raw["wage_usd_per_hour"], f"{path}.wage_usd_per_hour", positive=True)
    hours = _number(raw["hours_per_week"], f"{path}.hours_per_week", positive=True)
    rent = _number(raw["rent_usd_per_week"], f"{path}.rent_usd_per_week")
    overtime_hours = _optional_number(raw, "overtime_hours_per_week", path) or ZERO
    overtime_wage = _optional_number(raw, "overtime_wage_usd_per_hour", path) or ZERO
    if overtime_hours and not overtime_wage:
        raise ValueError(f"{path}: overtime needs an explicit hourly rate; the calculator never assumes 1.5x")
    if hours + overtime_hours > Decimal("168"):
        raise ValueError(f"{path}: weekly hours cannot exceed 168")
    transport = _optional_number(raw, "transport_usd_per_week", path) or ZERO
    food = _optional_number(raw, "food_usd_per_week", path) or ZERO
    other_weekly = _optional_number(raw, "other_weekly_usd", path) or ZERO
    other_fixed = _optional_number(raw, "other_fixed_usd", path) or ZERO

    gross = weeks * (wage * hours + overtime_wage * overtime_hours)
    housing = weeks * rent
    other = weeks * (transport + food + other_weekly) + other_fixed
    tax = _tax(raw["tax"], gross, state, tax_mode, f"{path}.tax")
    total_tax = Decimal(tax["total_usd"]) if tax["total_usd"] is not None else None
    net_before_tax = gross - housing - other
    net = net_before_tax - total_tax if total_tax is not None else None
    output.update({
        "calculation_status": "complete" if net is not None else "tax_pending",
        "inputs": {
            "wage_usd_per_hour": _money(wage), "hours_per_week": str(hours),
            "rent_usd_per_week": _money(rent), "overtime_hours_per_week": str(overtime_hours),
        },
        "gross_income_usd": _money(gross),
        "estimated_taxes": tax,
        "housing_cost_usd": _money(housing),
        "other_known_costs_usd": _money(other),
        "net_before_unverified_income_taxes_usd": _money(net_before_tax),
        "estimated_net_income_usd": _money(net),
        "estimated_net_income_cny": _money(net * fx) if net is not None and fx is not None else None,
        "fx_cny_per_usd": _money(fx),
    })
    if fx is None:
        output["fx_status"] = "needs_current_or_user_provided_rate"
    return output


def calculate_net_income(data: dict[str, Any]) -> dict[str, Any]:
    """Calculate net-income estimates. Raises ValueError for malformed input."""
    _exact_keys(data, {"tax_mode", "fx_cny_per_usd", "offers"}, {"tax_mode", "offers"}, "input")
    if data["tax_mode"] not in {"manual_rates", "data_assisted"}:
        raise ValueError("input.tax_mode: use manual_rates or data_assisted")
    if not isinstance(data["offers"], list) or not data["offers"]:
        raise ValueError("input.offers: requires at least one offer")
    fx = _optional_number(data, "fx_cny_per_usd", "input")
    if fx == ZERO:
        raise ValueError("input.fx_cny_per_usd: requires a positive number")

    ids: set[str] = set()
    offers = []
    for index, offer in enumerate(data["offers"]):
        if not isinstance(offer, dict):
            raise ValueError(f"input.offers[{index}]: requires an object")
        result = _offer(offer, data["tax_mode"], fx, f"input.offers[{index}]")
        if result["id"] in ids:
            raise ValueError("input.offers: duplicate id")
        ids.add(result["id"])
        offers.append(result)

    comparable = [item for item in offers if item.get("estimated_net_income_usd") is not None]
    comparison: dict[str, Any] = {"status": "not_requested" if len(offers) == 1 else "partial"}
    if len(offers) > 1:
        comparison["offers_with_net_estimate"] = [item["id"] for item in sorted(
            comparable, key=lambda item: Decimal(item["estimated_net_income_usd"]), reverse=True
        )]
        comparison["offers_pending_tax_or_period_confirmation"] = [
            item["id"] for item in offers if item not in comparable
        ]
        if len(comparable) == len(offers):
            comparison["status"] = "complete"
            comparison["message"] = "排序仅比较本次输入下的预计净结余，不代表岗位整体更适合。"
        else:
            comparison["message"] = "部分 Offer 的税或工作期未确认；暂不能做完整净结余排序。"

    return {
        "scope": "SWT 一工预计净收入；不含二工、未来退税、奖励或未明确成本。",
        "tax_mode": data["tax_mode"],
        "offers": offers,
        "comparison": comparison,
    }


def format_calculation(result: dict[str, Any]) -> str:
    """Render the compact user-facing Chinese format requested by this feature."""
    lines: list[str] = []
    for item in result["offers"]:
        if lines:
            lines.append("")
        lines.append(f"{item['label']}（{item['state']}）")
        period = item["period"]
        if period["status"] != "ready":
            lines.extend([
                "工作期：数据冲突，暂不计算", 
                f"日期换算：{period['date_calculated_weeks']} 周；直接输入：{period['provided_work_weeks']} 周",
                "请确认以日期还是直接输入周数为准。",
            ])
            continue
        days = f"（{period['calendar_days']} 天）" if period["calendar_days"] is not None else ""
        fields = item["inputs"]
        lines.extend([
            f"预计工作期：{item['period']['work_weeks']} 周{days}",
            f"时薪：${fields['wage_usd_per_hour']}；每周工时：{fields['hours_per_week']} h",
            f"税前收入：${item['gross_income_usd']}",
        ])
        tax = item["estimated_taxes"]
        if tax["total_usd"] is None:
            lines.append("预计税费：待核验（不会按固定比例猜测）")
        else:
            lines.append(f"预计税费：-${tax['total_usd']}")
        lines.extend([
            f"住宿：-${item['housing_cost_usd']}",
            f"其他已知成本：-${item['other_known_costs_usd']}",
        ])
        if item["estimated_net_income_usd"] is None:
            lines.append(f"税前待核验净结余：${item['net_before_unverified_income_taxes_usd']}")
        else:
            lines.append(f"预计美元净结余：${item['estimated_net_income_usd']}")
            if item["estimated_net_income_cny"] is not None:
                lines.append(f"按 ¥{item['fx_cny_per_usd']} / $：≈ ¥{item['estimated_net_income_cny']}")
            else:
                lines.append("人民币折算：待提供或核验当前汇率")
        lines.append(f"税务说明：{tax['message']}")
    if result["comparison"]["status"] != "not_requested":
        lines.extend(["", f"Offer 比较：{result['comparison']['message']}"])
        if result["comparison"].get("offers_with_net_estimate"):
            lines.append("按本次预计净结余：" + " > ".join(result["comparison"]["offers_with_net_estimate"]))
    return "\n".join(lines)


def _overview_defaults() -> dict[str, Any]:
    return json.loads(DEFAULT_ASSUMPTIONS_PATH.read_text(encoding="utf-8"), parse_float=Decimal)


def _state_reference(state: str | None) -> dict[str, str]:
    if state is None:
        return {}
    from state_context import load_state_profile, profile_path

    return load_state_profile(state) if profile_path(state).is_file() else {}


def _reference_midpoint(value: str | None) -> Decimal | None:
    """Treat a state range as a planning proxy, never as a city or Offer price."""
    if not value or "暂无可靠数据" in value:
        return None
    # State sheets commonly write "$100–150/week" with the currency sign only once.
    amounts = [Decimal(number) for number in re.findall(r"\d+(?:\.\d+)?", value)]
    if len(amounts) >= 2:
        return (amounts[0] + amounts[1]) / Decimal("2")
    if len(amounts) == 1:
        return amounts[0]
    return None


def _overview_period(raw: dict[str, Any], defaults: dict[str, Any], path: str) -> tuple[Decimal, str]:
    for start_key, end_key, source in (
        ("start_date", "end_date", "user_dates"),
        ("offer_start_date", "offer_end_date", "offer_dates"),
    ):
        if (start_key in raw) != (end_key in raw):
            raise ValueError(f"{path}: {start_key} and {end_key} must be provided together")
        if start_key in raw:
            if not isinstance(raw[start_key], str) or not isinstance(raw[end_key], str):
                raise ValueError(f"{path}: dates must use YYYY-MM-DD")
            first, last = date.fromisoformat(raw[start_key]), date.fromisoformat(raw[end_key])
            if last < first:
                raise ValueError(f"{path}: end date precedes start date")
            return Decimal((last - first).days + 1) / WEEK, source
    if "work_weeks" in raw:
        return _number(raw["work_weeks"], f"{path}.work_weeks", positive=True), "provided_weeks"
    return _number(defaults["global"]["work_weeks"], "defaults.global.work_weeks", positive=True), "global_estimate"


def _overview_cost(
    raw: dict[str, Any], city_defaults: dict[str, Any], profile: dict[str, str],
    defaults: dict[str, Any], key: str, state_field: str | None, path: str,
) -> tuple[Decimal, str]:
    if key in raw:
        return _number(raw[key], f"{path}.{key}"), "provided"
    if key in city_defaults:
        return _number(city_defaults[key], f"defaults.city.{key}"), "city_estimate"
    if state_field:
        reference = _reference_midpoint(profile.get(state_field))
        if reference is not None:
            return reference, "state_estimate"
    return _number(defaults["global"][key], f"defaults.global.{key}"), "global_estimate"


def _bracket_tax(income: Decimal, brackets: list[dict[str, Any]]) -> Decimal:
    lower = ZERO
    total = ZERO
    for index, bracket in enumerate(brackets):
        upper_raw = bracket["up_to_usd"]
        upper = _number(upper_raw, f"tax.brackets[{index}].up_to_usd") if upper_raw is not None else None
        rate = _number(bracket["rate_percent"], f"tax.brackets[{index}].rate_percent") / Decimal("100")
        if upper is not None and upper <= lower:
            raise ValueError("tax brackets must increase")
        taxable = max(ZERO, min(income, upper) - lower) if upper is not None else max(ZERO, income - lower)
        total += taxable * rate
        if upper is None or income <= upper:
            break
        lower = upper
    return total


def _overview_tax(raw: dict[str, Any], gross: Decimal, state: str | None, defaults: dict[str, Any], path: str) -> dict[str, Any]:
    allowed = {
        "federal_income_tax_usd", "state_income_tax_usd", "fica_usd",
        "federal_income_tax_percent", "state_income_tax_percent", "fica_percent",
    }
    _exact_keys(raw, allowed, set(), path)
    for amount_key, percent_key in (
        ("federal_income_tax_usd", "federal_income_tax_percent"),
        ("state_income_tax_usd", "state_income_tax_percent"),
        ("fica_usd", "fica_percent"),
    ):
        if amount_key in raw and percent_key in raw:
            raise ValueError(f"{path}: do not provide both {amount_key} and {percent_key}")

    def chosen(amount_key: str, percent_key: str, fallback: Decimal, source: str) -> tuple[Decimal, str]:
        if amount_key in raw:
            return _number(raw[amount_key], f"{path}.{amount_key}"), "provided"
        if percent_key in raw:
            rate = _number(raw[percent_key], f"{path}.{percent_key}")
            if rate > 100:
                raise ValueError(f"{path}.{percent_key}: cannot exceed 100")
            return gross * rate / Decimal("100"), "provided_rate"
        return fallback, source

    tax_cfg = defaults["tax_planning"]
    federal_basis = max(ZERO, gross - _number(tax_cfg["standard_deduction_usd"], "defaults.tax.standard_deduction_usd"))
    federal_default = _bracket_tax(federal_basis, tax_cfg["federal_brackets_single"])
    federal, federal_source = chosen("federal_income_tax_usd", "federal_income_tax_percent", federal_default, "federal_model_estimate")
    if state in defaults["zero_wage_income_tax_states"]:
        state_default, state_default_source = ZERO, "verified_zero_state_rule"
    else:
        reserve_rate = _number(tax_cfg["state_tax_unknown_reserve_percent"], "defaults.tax.state_tax_unknown_reserve_percent")
        state_default, state_default_source = gross * reserve_rate / Decimal("100"), "state_planning_reserve"
    state_tax, state_source = chosen("state_income_tax_usd", "state_income_tax_percent", state_default, state_default_source)
    fica_default = gross * _number(tax_cfg["fica_if_assumed_qualified_percent"], "defaults.tax.fica_if_assumed_qualified_percent") / Decimal("100")
    fica, fica_source = chosen("fica_usd", "fica_percent", fica_default, "assumed_qualified_j1")
    return {
        "federal_income_tax_usd": _money(federal),
        "state_income_tax_usd": _money(state_tax),
        "fica_usd": _money(fica),
        "total_usd": _money(federal + state_tax + fica),
        "sources": {"federal": federal_source, "state": state_source, "fica": fica_source},
        "assumed_profile": tax_cfg["assumed_profile"],
        "federal_tax_year": tax_cfg["federal_tax_year"],
    }


def _overview_offer(raw: dict[str, Any], top: dict[str, Any], defaults: dict[str, Any], index: int) -> dict[str, Any]:
    path = f"input.offers[{index}]"
    allowed = {
        "id", "label", "state", "city", "wage_usd_per_hour", "hours_per_week", "expected_hours",
        "min_hours", "max_hours", "hours_guaranteed", "hours_range_estimated", "hours_range_basis", "start_date", "end_date",
        "offer_start_date", "offer_end_date", "work_weeks", "stay_weeks", "rent_usd_per_week",
        "food_usd_per_week", "transport_usd_per_week", "other_weekly_usd", "other_fixed_usd",
        "project_cost_cny", "project_cost_usd", "tax", "second_job_note", "landing_note", "cautions",
    }
    _exact_keys(raw, allowed, {"wage_usd_per_hour"}, path)
    if "hours_per_week" not in raw and "expected_hours" not in raw:
        raise ValueError(f"{path}: provide hours_per_week or expected_hours")
    if "hours_per_week" in raw and "expected_hours" in raw and Decimal(str(raw["hours_per_week"])) != Decimal(str(raw["expected_hours"])):
        raise ValueError(f"{path}: hours_per_week and expected_hours disagree")
    label = raw.get("label", f"岗位 {index + 1}")
    identifier = raw.get("id", f"offer-{index + 1}")
    if not isinstance(label, str) or not label.strip() or not isinstance(identifier, str) or not identifier.strip():
        raise ValueError(f"{path}: id and label must be nonempty strings")
    wage = _number(raw["wage_usd_per_hour"], f"{path}.wage_usd_per_hour", positive=True)
    hours_key = "expected_hours" if "expected_hours" in raw else "hours_per_week"
    hours = _number(raw[hours_key], f"{path}.{hours_key}", positive=True)
    if hours > Decimal("168"):
        raise ValueError(f"{path}.{hours_key}: cannot exceed 168")
    has_min, has_max = "min_hours" in raw, "max_hours" in raw
    if has_min != has_max:
        raise ValueError(f"{path}: min_hours and max_hours must be provided together")
    minimum = _number(raw["min_hours"], f"{path}.min_hours") if has_min else None
    maximum = _number(raw["max_hours"], f"{path}.max_hours") if has_max else None
    if minimum is not None and (minimum > hours or hours > maximum or maximum > Decimal("168")):
        raise ValueError(f"{path}: require 0 <= min_hours <= expected_hours <= max_hours <= 168")
    guaranteed = raw.get("hours_guaranteed", False)
    if not isinstance(guaranteed, bool):
        raise ValueError(f"{path}.hours_guaranteed: requires true or false")
    if guaranteed:
        if minimum is not None and not (minimum == hours == maximum):
            raise ValueError(f"{path}: guaranteed hours cannot also have a different min/max range")
        minimum = maximum = hours
    estimated_range = raw.get("hours_range_estimated", False)
    if not isinstance(estimated_range, bool):
        raise ValueError(f"{path}.hours_range_estimated: requires true or false")
    if guaranteed and estimated_range:
        raise ValueError(f"{path}: guaranteed hours cannot be an estimated range")
    basis = raw.get("hours_range_basis")
    if basis is not None and (not isinstance(basis, str) or not basis.strip()):
        raise ValueError(f"{path}.hours_range_basis: requires nonempty text")
    if estimated_range and (minimum is None or basis is None):
        raise ValueError(f"{path}: an estimated hours range requires min/max and hours_range_basis")
    state = _state_code(raw["state"], f"{path}.state") if "state" in raw else None
    city = raw.get("city")
    if city is not None and (not isinstance(city, str) or not city.strip()):
        raise ValueError(f"{path}.city: requires a nonempty string")
    if state is None and city:
        from state_context import resolve_state

        resolution = resolve_state(city)
        state = resolution.code if resolution is not None else None
    city_key = f"{state or ''}|{city.strip().casefold()}" if city else ""
    city_defaults = defaults["city_cost_overrides"].get(city_key, {})
    profile = _state_reference(state)
    weeks, weeks_source = _overview_period(raw, defaults, path)
    stay_weeks = _number(raw["stay_weeks"], f"{path}.stay_weeks", positive=True) if "stay_weeks" in raw else weeks
    if stay_weeks < weeks:
        raise ValueError(f"{path}.stay_weeks: cannot be less than work weeks")
    costs: dict[str, Decimal] = {}
    sources: dict[str, str] = {"work_weeks": weeks_source}
    for key, state_field in (
        ("rent_usd_per_week", "常见周租"),
        ("food_usd_per_week", "每周基础开销"),
        ("transport_usd_per_week", None),
        ("other_weekly_usd", None),
    ):
        costs[key], sources[key] = _overview_cost(raw, city_defaults, profile, defaults, key, state_field, path)
    other_fixed = _number(raw["other_fixed_usd"], f"{path}.other_fixed_usd") if "other_fixed_usd" in raw else ZERO
    fx = _optional_number(top, "fx_cny_per_usd", "input")
    if fx is not None and fx <= ZERO:
        raise ValueError("input.fx_cny_per_usd: requires a positive number")
    project_keys = [key for key in ("project_cost_cny", "project_cost_usd") if key in raw or key in top]
    if len(project_keys) > 1 or any(key in raw and key in top for key in project_keys):
        raise ValueError(f"{path}: provide one project cost and one scope only")
    if "project_cost_usd" in raw or "project_cost_usd" in top:
        project = _number(raw.get("project_cost_usd", top.get("project_cost_usd")), f"{path}.project_cost_usd")
        project_source = "provided"
        project_cny = project * fx if fx is not None else None
    elif "project_cost_cny" in raw or "project_cost_cny" in top:
        project_cny = _number(raw.get("project_cost_cny", top.get("project_cost_cny")), f"{path}.project_cost_cny")
        project = project_cny / fx if fx is not None else None
        project_source = "provided_converted"
    else:
        project_cny = _number(defaults["global"]["project_cost_cny"], "defaults.global.project_cost_cny")
        project = project_cny / fx if fx is not None else None
        project_source = "global_estimate"
    if project is not None:
        project = project.quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    sources["project_cost"] = project_source
    sources["fx"] = "provided" if fx is not None else "unavailable"

    gross = (wage * hours * weeks).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    tax_input = raw.get("tax", top.get("tax", {}))
    if not isinstance(tax_input, dict):
        raise ValueError(f"{path}.tax: requires an object")
    taxes = _overview_tax(tax_input, gross, state, defaults, f"{path}.tax")
    total_tax = Decimal(taxes["total_usd"])
    housing = (costs["rent_usd_per_week"] * stay_weeks).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    food = (costs["food_usd_per_week"] * stay_weeks).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    transport = (costs["transport_usd_per_week"] * stay_weeks).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    other = (costs["other_weekly_usd"] * stay_weeks + other_fixed).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    living = housing + food + transport + other
    net_us = gross - total_tax - living
    final = net_us - project if project is not None else None
    weekly_living = sum(costs.values())
    weekly_after_tax_and_living = wage * hours - total_tax / weeks - weekly_living
    fixed_living = (stay_weeks - weeks) * weekly_living + other_fixed
    break_even = None
    if project is not None and weekly_after_tax_and_living > ZERO:
        break_even = ((project + fixed_living) / weekly_after_tax_and_living * Decimal("10")).to_integral_value(rounding=ROUND_CEILING) / Decimal("10")

    cautions = raw.get("cautions", {})
    if not isinstance(cautions, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in cautions.items()):
        raise ValueError(f"{path}.cautions: requires an object of topic-to-text strings")
    for key in ("second_job_note", "landing_note"):
        if key in raw and not isinstance(raw[key], str):
            raise ValueError(f"{path}.{key}: requires text")
    second_job = raw.get("second_job_note") or (
        f"州级：{profile['好不好找']}（估）" if profile.get("好不好找") not in (None, "暂无可靠数据") else "不计入收益（估）"
    )
    landing = raw.get("landing_note") or (
        f"州级 SSN：{profile['SSN']}（估）" if profile.get("SSN") not in (None, "暂无可靠数据") else "办理时间待核验（估）"
    )
    return {
        "id": identifier, "label": label, "state": state, "city": city,
        "work_weeks": _money(weeks) if weeks == weeks.quantize(Decimal(".01")) else str(weeks),
        "stay_weeks": _money(stay_weeks) if stay_weeks == stay_weeks.quantize(Decimal(".01")) else str(stay_weeks),
        "wage_usd_per_hour": _money(wage), "hours_per_week": _money(hours),
        "hours_range": {
            "min": _money(minimum), "expected": _money(hours), "max": _money(maximum),
            "status": ("guaranteed" if guaranteed else "estimated_range" if estimated_range
                       else "provided_range" if minimum is not None else "point_only"),
            "basis": basis,
        },
        "weekly_costs_usd": {key: _money(value) for key, value in costs.items()},
        "cost_sources": sources, "second_job": second_job, "landing": landing,
        "gross_income_usd": _money(gross), "estimated_taxes": taxes,
        "housing_usd": _money(housing), "food_usd": _money(food),
        "transport_usd": _money(transport), "other_living_usd": _money(other),
        "estimated_us_net_usd": _money(net_us), "project_cost_usd": _money(project),
        "project_cost_cny": _money(project_cny), "final_project_surplus_usd": _money(final),
        "break_even_work_weeks": _money(break_even),
        "can_break_even_in_period": final >= ZERO if final is not None else None,
        "fx_cny_per_usd": str(fx) if fx is not None else None, "cautions": cautions,
        "start_date": raw.get("start_date") or raw.get("offer_start_date"),
        "end_date": raw.get("end_date") or raw.get("offer_end_date"),
    }


def calculate_position_overview(data: dict[str, Any]) -> dict[str, Any]:
    """Calculate a one-result SWT comparison with explicit provenance for every fallback."""
    _exact_keys(
        data, {"mode", "offers", "fx_cny_per_usd", "fx_source", "fx_quote_date", "project_cost_cny", "project_cost_usd", "tax", "comparison_hours"},
        {"offers"}, "input",
    )
    if data.get("mode", "position_overview") != "position_overview":
        raise ValueError("input.mode: use position_overview")
    if not isinstance(data["offers"], list) or not data["offers"]:
        raise ValueError("input.offers: requires at least one offer")
    for key in ("fx_source", "fx_quote_date"):
        if key in data and (not isinstance(data[key], str) or not data[key].strip()):
            raise ValueError(f"input.{key}: requires nonempty text")
    if "fx_quote_date" in data:
        try:
            date.fromisoformat(data["fx_quote_date"])
        except ValueError as error:
            raise ValueError("input.fx_quote_date: use YYYY-MM-DD") from error
    if any(key in data for key in ("fx_source", "fx_quote_date")) and "fx_cny_per_usd" not in data:
        raise ValueError("exchange rate metadata requires fx_cny_per_usd")
    defaults = _overview_defaults()
    offers = [_overview_offer(raw, data, defaults, index) for index, raw in enumerate(data["offers"])]
    ids = [item["id"] for item in offers]
    if len(ids) != len(set(ids)):
        raise ValueError("input.offers: duplicate id")
    from offer_return import calculate_offer_return_analysis

    return {
        "mode": "position_overview", "assumptions_version": defaults["version"],
        "offers": offers,
        "comparison_order": [item["id"] for item in (sorted(offers, key=lambda item: Decimal(item["final_project_surplus_usd"]), reverse=True) if all(item["final_project_surplus_usd"] is not None for item in offers) else offers)],
        "comparison_complete": all(item["final_project_surplus_usd"] is not None for item in offers),
        "fx_source": data.get("fx_source"), "fx_quote_date": data.get("fx_quote_date"),
        "offer_return_analysis": calculate_offer_return_analysis(offers, data.get("comparison_hours")),
    }


def _usd_display(value: str | Decimal, *, estimate: bool = False) -> str:
    number = Decimal(value).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    display = f"{'-' if number < ZERO else ''}${abs(number):,.2f}"
    return display + ("（估）" if estimate else "")


def _short_decimal(value: str | Decimal) -> str:
    rounded = Decimal(value).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    return format(rounded.normalize(), "f")


def _hour_display(value: str | Decimal) -> str:
    return f"{Decimal(value).quantize(Decimal('.1'), rounding=ROUND_HALF_UP).normalize():f}"


def _format_return_analysis(analysis: dict[str, Any], labels: dict[str, str]) -> list[str]:
    """Compact comparison for 2–3 offers; chart rendering is the host's choice."""
    lines = ["## 4. 岗位收益对比", ""]
    if analysis["analysis_status"] != "complete":
        lines.append("如需深入比较工时变化，可以挑两到三份岗位。")
        return lines

    chart = analysis["chart"]
    final = chart["y_basis"] == "final_project_surplus"
    y_title = "最终预计结余（美元）" if final else "在美预计结余（美元）"
    values = [int(value) for series in chart["series"] for value in series["values"]]
    low = min(min(values), 0) // 500 * 500
    high = -(-max(max(values), 0) // 500) * 500
    lines.extend([
        "```mermaid", "xychart-beta",
        f'    title "每周工时与{y_title}"',
        f'    x-axis "每周平均工时" [{", ".join(chart["hours"])}]',
        f'    y-axis "{y_title}" {low} --> {high}',
        *(f'    line [{", ".join(series["values"])}]' for series in chart["series"]),
        "```", "",
    ])
    lines.extend(f"- 第 {index} 条线：{series['label']}，{_hours_text(analysis, series['id'])}"
                 for index, series in enumerate(chart["series"], 1))

    meaningful = [item for item in analysis["intersections"] if item["meaningful_for_optimum"]]
    if meaningful:
        lines.append("")
        lines.extend(
            f"- 每周平均工时约 {_hour_display(item['hours_per_week'])} 小时时，"
            f"{labels[item['offers'][0]]} 和 {labels[item['offers'][1]]} 结余持平。"
            for item in meaningful
        )
    elif analysis["optimal_regions"]:
        region = analysis["optimal_regions"][0]
        winner = " / ".join(labels[item] for item in region["best_offer_ids"])
        lines.extend(["", f"每周 {_hour_display(region['min_hours'])}–{_hour_display(region['max_hours'])} 小时之间，{winner} 都更划算。"])
    if analysis["optimal_regions"] and meaningful:
        for region in analysis["optimal_regions"]:
            winner = " / ".join(labels[item] for item in region["best_offer_ids"])
            lines.append(f"- {_hour_display(region['min_hours'])}–{_hour_display(region['max_hours'])} 小时/周：{winner} 更划算。")
    return lines


def _hours_text(analysis: dict[str, Any], offer_id: str) -> str:
    hours = next(item["hours"] for item in analysis["functions"] if item["id"] == offer_id)
    if hours.get("status") == "guaranteed":
        return f"保证 {_short_decimal(hours['expected'])} 小时"
    if hours.get("min") is not None and hours["min"] != hours["max"]:
        return f"{_short_decimal(hours['min'])}–{_short_decimal(hours['max'])} 小时"
    return f"平均 {_short_decimal(hours['expected'])} 小时"


def _whole_usd(value: str | Decimal, *, estimate: bool = False) -> str:
    amount = Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    text = f"{'−' if amount < ZERO else ''}${abs(amount):,.0f}"
    return text + ("（估）" if estimate else "")


def _cents_usd(value: str | Decimal) -> str:
    amount = Decimal(value).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    text = f"${abs(amount):,.2f}"
    return ("−" if amount < ZERO else "") + (text[:-3] if text.endswith(".00") else text)


def _whole_cny(value: str | Decimal) -> str:
    amount = Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"{'−' if amount < ZERO else ''}¥{abs(amount):,.0f}"


def _estimated(item: dict[str, Any], key: str) -> bool:
    return item["cost_sources"].get(key) not in {"provided", "provided_rate", "provided_weeks", "user_dates", "offer_dates"}


def _hours_cell(item: dict[str, Any]) -> str:
    hours = item["hours_range"]
    if hours["status"] == "guaranteed":
        return f"{_short_decimal(hours['expected'])}h/周，保证"
    if hours.get("min") is not None and hours["min"] != hours["max"]:
        return f"{_short_decimal(hours['min'])}–{_short_decimal(hours['max'])}h/周，不保证"
    return f"平均 {_short_decimal(hours['expected'])}h/周，不保证"


def _period_cell(item: dict[str, Any]) -> str:
    weeks = Decimal(item["work_weeks"]).quantize(Decimal(".1"), rounding=ROUND_HALF_UP).normalize()
    if item.get("start_date") and item.get("end_date"):
        start, end = date.fromisoformat(item["start_date"]), date.fromisoformat(item["end_date"])
        return f"{start.month}/{start.day}–{end.month}/{end.day}，约 {weeks:f} 周"
    return f"约 {weeks:f} 周" + ("（估）" if _estimated(item, "work_weeks") else "")


def _final_at_hours(analysis: dict[str, Any], item: dict[str, Any], hours: Decimal) -> Decimal | None:
    function = next((f for f in analysis.get("functions", []) if f["id"] == item["id"]), None)
    if function is None or function.get("season_slope_usd_per_hour") is None or item["project_cost_usd"] is None:
        return None
    season = Decimal(function["season_slope_usd_per_hour"]) * hours + Decimal(function["season_intercept_usd"])
    return season - Decimal(item["project_cost_usd"])


def _break_even_hours(analysis: dict[str, Any], item: dict[str, Any]) -> Decimal | None:
    function = next((f for f in analysis.get("functions", []) if f["id"] == item["id"]), None)
    if function is None or function.get("season_slope_usd_per_hour") is None or item["project_cost_usd"] is None:
        return None
    slope = Decimal(function["season_slope_usd_per_hour"])
    if slope <= ZERO:
        return None
    return (Decimal(item["project_cost_usd"]) - Decimal(function["season_intercept_usd"])) / slope


def _key_factors(result: dict[str, Any]) -> list[str]:
    analysis = result.get("offer_return_analysis", {})
    offers = result["offers"]
    many = len(offers) > 1
    factors: list[str] = []
    for item in offers:
        hours = item["hours_range"]
        prefix = f"{item['label']} " if many else ""
        if hours["status"] != "guaranteed" and hours.get("min") is not None and hours["min"] != hours["max"]:
            low = _final_at_hours(analysis, item, Decimal(hours["min"]))
            high = _final_at_hours(analysis, item, Decimal(hours["max"]))
            if low is not None and high is not None:
                factors.append(f"**{prefix}工时不保证**：{_short_decimal(hours['min'])} 小时约 {_whole_usd(low)}，"
                               f"{_short_decimal(hours['max'])} 小时约 {_whole_usd(high)}。")
    if not many and offers and offers[0]["final_project_surplus_usd"] is not None and not offers[0]["can_break_even_in_period"]:
        needed = _break_even_hours(analysis, offers[0])
        if needed is not None and needed <= Decimal("80"):
            factors.append(f"**回本所需工时**：每周平均约 {needed.quantize(Decimal('1'), rounding=ROUND_CEILING)} 小时。")
    estimated_project = [item for item in offers if item["cost_sources"]["project_cost"] == "global_estimate"]
    if estimated_project and estimated_project[0]["project_cost_cny"] is not None:
        factors.append(f"**项目费**：按 ¥{Decimal(estimated_project[0]['project_cost_cny']):,.0f} 估算，提供实际金额后可重新测算。")
    if many:
        factors.append("**二工**：均需经 Sponsor 批准，不计入上述结余。")
    else:
        factors.append("**二工**：需经 Sponsor 批准；一工排班优先，不计入上述结余。")
    return factors[:3]


def _conclusion(result: dict[str, Any]) -> str:
    offers = result["offers"]
    best = next(item for item in offers if item["id"] == result["comparison_order"][0])
    if len(offers) == 1:
        item = best
        basis = (f"按 {_cents_usd(item['wage_usd_per_hour'])}/h、"
                 f"{'每周保证' if item['hours_range']['status'] == 'guaranteed' else '平均每周'} "
                 f"{_short_decimal(item['hours_per_week'])} 小时计算，在美预计结余约 {_whole_usd(item['estimated_us_net_usd'])}")
        if item["final_project_surplus_usd"] is None:
            return f"**{basis}；缺少汇率，最终结余暂无法计算。**"
        final = Decimal(item["final_project_surplus_usd"])
        cny = f"（约 {_whole_cny(final * Decimal(item['fx_cny_per_usd']))}）" if item["fx_cny_per_usd"] is not None else ""
        project = f"¥{Decimal(item['project_cost_cny']):,.0f}" if item["project_cost_cny"] is not None else _whole_usd(item["project_cost_usd"])
        head = "本岗位预计可以回本" if final >= ZERO else "单靠本岗位无法回本"
        return f"**{head}：{basis}，扣除项目费 {project} 后，最终预计结余约 {_whole_usd(final)}{cny}。**"
    if not result["comparison_complete"]:
        return f"**按在美预计结余，{best['label']} 最高（约 {_whole_usd(best['estimated_us_net_usd'])}）；缺少汇率，最终结余暂无法计算。**"
    others = "，".join(f"{item['label']} 约 {_whole_usd(item['final_project_surplus_usd'])}"
                      for item in offers if item is not best)
    text = f"仅从收益看，{best['label']} 更高：{best['label']} 最终预计结余约 {_whole_usd(best['final_project_surplus_usd'])}，{others}"
    analysis = result.get("offer_return_analysis", {})
    labels = {item["id"]: item["label"] for item in offers}
    crossings = [item for item in analysis.get("intersections", []) if item.get("meaningful_for_optimum")]
    regions = analysis.get("optimal_regions", [])
    if len(offers) == 2 and len(crossings) == 1 and regions:
        later = regions[-1]["best_offer_ids"]
        if len(later) == 1 and later[0] != best["id"]:
            text += (f"；{labels[later[0]]} 每周平均工时达到 "
                     f"{_hour_display(crossings[0]['hours_per_week'])} 小时以上，才会超过 {best['label']}")
    return f"**{text}。**"


def _fx_line(result: dict[str, Any]) -> list[str]:
    fx = result["offers"][0]["fx_cny_per_usd"]
    if fx is None:
        return []
    if result.get("fx_source"):
        quoted = result.get("fx_quote_date")
        day = f"{date.fromisoformat(quoted).month} 月 {date.fromisoformat(quoted).day} 日" if quoted else ""
        source = result["fx_source"]
        gap = " " if day and source[:1].isascii() else ""
        return ["", f"汇率 {fx}：{day}{gap}{source}，向上取一位小数。"]
    return ["", f"汇率 {fx}：用户提供。"]


def format_position_overview(result: dict[str, Any]) -> str:
    """Student-facing answer: conclusion, key factors, overview table, payback table, chart, options."""
    offers = result["offers"]
    many = len(offers) > 1
    lines = [_conclusion(result), ""]
    factors = _key_factors(result)
    if factors:
        lines.append("影响选择的关键因素：" if many else "影响回本的关键因素：")
        lines.extend(f"{index}. {factor}" for index, factor in enumerate(factors, 1))
        lines.append("")

    def caution_for(item: dict[str, Any], words: tuple[str, ...]) -> str:
        return "；".join(detail for topic, detail in item["cautions"].items()
                        if detail and any(word in topic for word in words))

    def cost_cell(item: dict[str, Any], key: str) -> str:
        return f"{_cents_usd(item['weekly_costs_usd'][key])}/周" + ("（估）" if _estimated(item, key) else "")

    if many:
        lines.extend(["**岗位对比**", "",
                      "| 要素 | " + " | ".join(item["label"] for item in offers) + " |",
                      "|---|" + "---|" * len(offers)])
        rows = [
            ("时薪", [_cents_usd(item["wage_usd_per_hour"]) for item in offers]),
            ("工时", [_hours_cell(item) for item in offers]),
            ("工期", [_period_cell(item) for item in offers]),
            ("住宿", [cost_cell(item, "rent_usd_per_week") for item in offers]),
            ("餐饮", [cost_cell(item, "food_usd_per_week") for item in offers]),
            ("通勤", [cost_cell(item, "transport_usd_per_week") for item in offers]),
            ("在美预计结余", [_whole_usd(item["estimated_us_net_usd"]) for item in offers]),
        ]
        if result["comparison_complete"]:
            rows.append(("**最终预计结余**", [f"**{_whole_usd(item['final_project_surplus_usd'])}**" for item in offers]))
        lines.extend(f"| {name} | " + " | ".join(values) + " |" for name, values in rows)
        lines.extend(_fx_line(result))
        if 2 <= len(offers) <= 3:
            labels = {item["id"]: item["label"] for item in offers}
            lines.extend(["", "**岗位收益对比**", "", *_format_return_analysis(result["offer_return_analysis"], labels)[2:]])
        else:
            lines.extend(["", "如需看收益对比图，可再挑 2–3 份深入比较。"])
        notes = [f"{item['label']}：{topic}：{detail}" for item in offers
                 for topic, detail in item["cautions"].items() if detail]
        if notes:
            lines.extend(["", "**注意事项**", "", *(f"- {note}" for note in notes)])
        options = ["A. 修改工时、餐费或项目费，重新测算", "B. 加入二工，测算回本所需工时",
                   "C. 查看各地住宿、工作内容与当地生活", "D. 判断选择哪个岗位"]
    else:
        item = offers[0]
        hours_note = "工时保证" if item["hours_range"]["status"] == "guaranteed" else "工时不保证"
        lines.extend(["**岗位概况**", "", "| 要素 | 内容 | 注意事项 |", "|---|---|---|"])
        rows = [
            ("工资", f"{_cents_usd(item['wage_usd_per_hour'])}/h，{_hours_cell(item).split('，')[0]}，{_period_cell(item)}",
             "；".join(x for x in (hours_note, caution_for(item, ("工资", "时薪", "收入", "工时", "小费", "加班"))) if x)),
            ("住宿", cost_cell(item, "rent_usd_per_week"), caution_for(item, ("住宿", "房租", "押金"))),
            ("餐饮", cost_cell(item, "food_usd_per_week"), caution_for(item, ("餐", "伙食"))),
            ("通勤", cost_cell(item, "transport_usd_per_week"), caution_for(item, ("交通", "通勤", "接机"))),
            ("落地", item["landing"], caution_for(item, ("落地", "SSN", "培训", "到岗"))),
        ]
        lines.extend(f"| {name} | {content} | {note} |" for name, content, note in rows)
        other_notes = [f"{topic}：{detail}" for topic, detail in item["cautions"].items() if detail and not any(
            word in topic for word in ("工资", "时薪", "收入", "工时", "小费", "加班", "住宿", "房租", "押金", "餐", "伙食",
                                       "交通", "通勤", "接机", "落地", "SSN", "培训", "到岗"))]
        tax = item["estimated_taxes"]
        living = sum(Decimal(item[key]) for key in ("housing_usd", "food_usd", "transport_usd", "other_living_usd"))
        lines.extend(["", "**回本测算**", "", "| 项目 | 金额 |", "|---|---|",
                      f"| 税前工资（{_cents_usd(item['wage_usd_per_hour'])} × {_short_decimal(item['hours_per_week'])}h × "
                      f"{Decimal(item['work_weeks']).quantize(Decimal('.1'), rounding=ROUND_HALF_UP).normalize():f} 周） | {_whole_usd(item['gross_income_usd'])} |",
                      f"| 预计税费 | {_whole_usd(-Decimal(tax['total_usd']))} |",
                      f"| 住宿、餐饮、交通及其他 | {_whole_usd(-living)} |",
                      f"| **在美预计结余** | **{_whole_usd(item['estimated_us_net_usd'])}** |"])
        if item["project_cost_usd"] is not None:
            source = (f"（¥{Decimal(item['project_cost_cny']):,.0f} ÷ {item['fx_cny_per_usd']}）" if item["project_cost_cny"] is not None
                      else "")
            lines.extend([f"| 项目费{source} | {_whole_usd(-Decimal(item['project_cost_usd']))} |",
                          f"| **最终预计结余** | **{_whole_usd(item['final_project_surplus_usd'])}** |"])
        lines.extend(_fx_line(result))
        if other_notes:
            lines.extend(["", "**注意事项**", "", *(f"- {note}" for note in other_notes)])
        options = ["A. 填入实际项目费或小费，重新测算", "B. 与其他岗位对比",
                   "C. 查看住宿、工作内容与当地生活", "D. 判断是否值得选择"]
    lines.extend(["", "**后续选项**", *options, "", "回复字母或直接提问。"])
    return "\n".join(lines)


def format_position_detail(result: dict[str, Any], topic: str) -> str:
    """Expand only the requested field; do not repeat the three-table overview."""
    topics = {
        "housing": ("rent_usd_per_week", "housing_usd", "住宿"),
        "food": ("food_usd_per_week", "food_usd", "餐饮"),
        "transport": ("transport_usd_per_week", "transport_usd", "交通"),
    }
    if topic not in topics:
        raise ValueError(f"unsupported detail topic: {topic}")
    weekly_key, total_key, label = topics[topic]
    source_names = {
        "provided": "你提供的岗位／个人数据",
        "city_estimate": "当前配置的精确城市规划值",
        "state_estimate": "州级参考范围的中值（只作估算，不是该城市报价）",
        "global_estimate": "插件通用规划值",
    }
    lines = []
    for item in result["offers"]:
        source = item["cost_sources"][weekly_key]
        extra = "；州级“每周基础开销”仅作餐饮代理" if topic == "food" and source == "state_estimate" else ""
        lines.append(
            f"{item['label']}的{label}按 ${item['weekly_costs_usd'][weekly_key]}/周 × "
            f"{_short_decimal(item['stay_weeks'])} 个停留周＝${item[total_key]}。"
            f"来源：{source_names[source]}{extra}。"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--round-fx":
        try:
            print(round_searched_fx(Decimal(argv[2])))
            return 0
        except (ValueError, TypeError, InvalidOperation) as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 2
    if len(argv) == 4 and argv[1] == "--chart":
        try:
            from offer_chart import render_offer_chart
            from paths import PLUGIN_ROOT

            data = json.loads(Path(argv[3]).read_text(encoding="utf-8"), parse_float=Decimal)
            output = Path(argv[2]).expanduser().resolve()
            if PLUGIN_ROOT in output.parents:
                raise ValueError("chart output must be outside the Skill folder")
            output.write_text(render_offer_chart(calculate_position_overview(data)), encoding="utf-8")
            print(output)
            return 0
        except (ValueError, TypeError, OSError, KeyError) as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 2
    detail_topic = argv[2] if len(argv) == 4 and argv[1] == "--detail" else None
    if not (len(argv) == 2 or (len(argv) == 3 and argv[1] == "--json") or detail_topic):
        print("Usage: python3 scripts/budget.py [--json | --detail housing|food|transport | --chart OUT.svg] INPUT.json", file=sys.stderr)
        return 2
    json_output = argv[1] == "--json"
    input_path = argv[3] if detail_topic else argv[2] if json_output else argv[1]
    try:
        data = json.loads(Path(input_path).read_text(encoding="utf-8"), parse_float=Decimal)
        overview = data.get("mode") == "position_overview" or ("tax_mode" not in data and "offers" in data)
        result = calculate_position_overview(data) if overview else calculate_net_income(data)
        if json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif detail_topic:
            if not overview:
                raise ValueError("--detail requires position_overview input")
            print(format_position_detail(result, detail_topic))
        else:
            print(format_position_overview(result) if overview else format_calculation(result))
        return 0
    except (ValueError, TypeError, OSError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
