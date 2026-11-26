#!/usr/bin/env python3
"""China↔US travel estimate: base × advance curve × season (not live fares)."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_CANDIDATES = (
    ROOT / "references" / "travel-estimate.json",
    ROOT / "skills" / "swt-arrival" / "references" / "travel-estimate.json",
)


def _load() -> dict[str, Any]:
    for path in DATA_CANDIDATES:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    raise FileNotFoundError("travel-estimate.json not found next to plugin or swt-arrival skill")


def _resolve_city(data: dict[str, Any], raw: str) -> tuple[str, dict[str, Any]]:
    key = raw.strip()
    cities = data["cities"]
    if key in cities:
        return key, cities[key]
    folded = key.casefold()
    for name, meta in cities.items():
        aliases = [name, *meta.get("aliases", [])]
        if any(str(a).casefold() == folded for a in aliases):
            return name, meta
    raise ValueError(f"未收录地点：{raw}。可用城市见 travel-estimate.json 的 cities。")


def _band_text(lo_hi: list[int], currency: str) -> str:
    lo, hi = lo_hi
    if currency == "CNY":
        return f"约 ¥{lo:,}–{hi:,}"
    return f"约 ${lo}–{hi}"


def _advance_factor(algo: dict[str, Any], days: int) -> float:
    days = max(0, int(days))
    for row in algo["advance_curve"]:
        if row["min_days"] <= days <= row["max_days"]:
            return float(row["factor"])
    return 1.0


def _season_factor(algo: dict[str, Any], month: int | None) -> tuple[float, str]:
    if month is None:
        return 1.0, "未指定月份（按肩季中性）"
    month = int(month)
    if month < 1 or month > 12:
        raise ValueError("--month 须为 1–12")
    season = algo["season"]
    if month in season["peak_months"]:
        return float(season["peak_factor"]), f"{month} 月旺季"
    if month in season["shoulder_months"]:
        return float(season["shoulder_factor"]), f"{month} 月肩季"
    return float(season["off_factor"]), f"{month} 月淡季"


def _routing_factor(algo: dict[str, Any], prefer_direct: bool) -> float:
    routing = algo["routing"]
    return float(routing["prefer_direct_factor"] if prefer_direct else routing["connection_ok_factor"])


def _haversine_miles(a: dict[str, Any], b: dict[str, Any]) -> float | None:
    if "lat" not in a or "lon" not in a or "lat" not in b or "lon" not in b:
        return None
    lat1, lon1 = math.radians(float(a["lat"])), math.radians(float(a["lon"]))
    lat2, lon2 = math.radians(float(b["lat"])), math.radians(float(b["lon"]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def _bands_from_center(center: float, algo: dict[str, Any]) -> dict[str, list[int]]:
    width = algo["band_width"]
    half = float(width["half_spread"])
    deal_r = float(width["deal_ratio"])
    stretch_r = float(width["stretch_ratio"])
    plan_lo = int(round(center * (1 - half)))
    plan_hi = int(round(center * (1 + half)))
    deal_center = center * deal_r
    stretch_center = center * stretch_r
    return {
        "low": [max(1, int(round(deal_center * (1 - half)))), max(1, int(round(deal_center * (1 + half))))],
        "mid": [max(1, plan_lo), max(1, plan_hi)],
        "high": [max(1, int(round(stretch_center * (1 - half)))), max(1, int(round(stretch_center * (1 + half))))],
    }


def _scale_point(base: float, *, advance: float, season: float, routing: float, ref_advance: float) -> float:
    # base is calibrated at reference_advance_days; renormalize if curve ref ≠ 1.0 at that point
    return base * (advance / ref_advance) * season * routing


def _international_base(data: dict[str, Any], cn_hub: str, gateway: str) -> float:
    table = data["international_base_cny_round_trip"]
    return float(table.get(f"{cn_hub}|{gateway}") or table["default"])


def _domestic_base(
    data: dict[str, Any],
    gateway_meta: dict[str, Any],
    dest_meta: dict[str, Any],
    dest_name: str,
    gateway_side: str,
) -> tuple[float, str]:
    table = data.get("domestic_base_usd_one_way") or {}
    key = f"{gateway_side}|{dest_name}"
    if key in table and not isinstance(table[key], str):
        return float(table[key]), f"城市对底价 {key}"
    miles = _haversine_miles(gateway_meta, dest_meta)
    fb = data["algorithm"]["domestic_distance_fallback"]
    if miles is None:
        # coarse regional fallback
        base = 190.0 if gateway_side == "west" else 85.0
        return base, "区域默认底价（缺坐标）"
    raw = float(fb["fixed_usd"]) + float(fb["per_mile_usd"]) * miles
    clipped = min(float(fb["max_usd"]), max(float(fb["min_usd"]), raw))
    return clipped, f"距离模型约 {miles:.0f} mi"


def _cny_from_leg(leg: dict[str, Any], fx: float, band: str) -> tuple[int, int]:
    lo, hi = leg["bands"][band]
    if leg["currency"] == "CNY":
        return int(lo), int(hi)
    return int(round(lo * fx)), int(round(hi * fx))


def estimate(
    origin: str,
    gateway: str,
    destination: str | None = None,
    *,
    round_trip: bool = True,
    advance_days: int | None = None,
    travel_month: int | None = None,
    prefer_direct: bool = False,
) -> dict[str, Any]:
    data = _load()
    algo = data["algorithm"]
    days = int(algo["default_advance_days"] if advance_days is None else advance_days)
    if days < 0:
        raise ValueError("--advance-days 不能为负")
    month = travel_month if travel_month is not None else algo.get("default_travel_month")

    o_name, o_meta = _resolve_city(data, origin)
    g_name, g_meta = _resolve_city(data, gateway)
    if "cn_hub" not in o_meta:
        raise ValueError(f"起点须为中国城市，收到：{o_name}")
    if "us_gateway" not in g_meta:
        raise ValueError(f"第一段终点须为美国入境门户城市，收到：{g_name}")

    adv = _advance_factor(algo, days)
    sea, season_label = _season_factor(algo, month)
    route = _routing_factor(algo, prefer_direct)
    ref_adv = _advance_factor(algo, int(algo["reference_advance_days"]))

    intl_base = _international_base(data, o_meta["cn_hub"], g_meta["us_gateway"])
    intl_center = _scale_point(intl_base, advance=adv, season=sea, routing=route, ref_advance=ref_adv)
    if not round_trip:
        intl_center *= 0.55  # open-jaw / OW not exactly half RT
    intl_bands = _bands_from_center(intl_center, algo)

    extras: list[str] = []
    if o_meta.get("via_note"):
        extras.append(f"{o_name}：{o_meta['via_note']}")
    extras.append(f"模型：提前 {days} 天订票 × {season_label} × {'偏直飞' if prefer_direct else '可转机'}")

    legs: list[dict[str, Any]] = [
        {
            "leg": 1,
            "label": f"{o_name} → {g_name}",
            "kind": "international",
            "trip": "round_trip" if round_trip else "one_way",
            "currency": "CNY",
            "bands": intl_bands,
            "center": int(round(intl_center)),
            "pet_note": (
                f"国际段较常见可讨论宠物帮带；规划抵扣约 ${_usd_range(data['pet']['offset_usd_per_trip'])}/趟。"
                f"细则与红线见 {data['pet']['detail_skill']}，先保证本人合法入境。"
            ),
        }
    ]

    if destination:
        d_name, d_meta = _resolve_city(data, destination)
        if d_name == g_name:
            raise ValueError("第二段终点与门户相同，可省略 --to")
        dom_base, dom_src = _domestic_base(data, g_meta, d_meta, d_name, g_meta["us_gateway"])
        # domestic: season + advance apply; prefer_direct milder (ULCC often nonstop-ish)
        dom_route = 1.08 if prefer_direct else 1.0
        dom_center = _scale_point(dom_base, advance=adv, season=sea, routing=dom_route, ref_advance=ref_adv)
        multiplier = 2 if round_trip else 1
        dom_center_trip = dom_center * multiplier
        dom_bands = _bands_from_center(dom_center_trip, algo)
        legs.append(
            {
                "leg": 2,
                "label": f"{g_name} → {d_name}",
                "kind": "us_domestic",
                "trip": "round_trip" if round_trip else "one_way",
                "currency": "USD",
                "bands": dom_bands,
                "center": int(round(dom_center_trip)),
                "source": dom_src,
                "pet_note": data["pet"]["domestic_us_note"],
            }
        )
        extras.append(f"国内段底价来源：{dom_src}")
        summary = f"行程：{o_name} → {g_name} → {d_name}" + ("（来回）" if round_trip else "（单程）")
    else:
        summary = f"行程：{o_name} → {g_name}" + ("（国际来回）" if round_trip else "（国际单程）")

    fx = float(data.get("fx_cny_per_usd_default", 7.2))
    plan_lo = plan_hi = deal_lo = deal_hi = stretch_lo = stretch_hi = 0
    for leg in legs:
        a, b = _cny_from_leg(leg, fx, "mid")
        plan_lo += a
        plan_hi += b
        a, b = _cny_from_leg(leg, fx, "low")
        deal_lo += a
        deal_hi += b
        a, b = _cny_from_leg(leg, fx, "high")
        stretch_lo += a
        stretch_hi += b

    return {
        "version": data["version"],
        "purpose": data["purpose"],
        "disclaimer": data["disclaimer"],
        "algorithm": data["algorithm"]["name"],
        "inputs": {
            "advance_days": days,
            "travel_month": month,
            "prefer_direct": prefer_direct,
            "advance_factor": round(adv / ref_adv, 3),
            "season_factor": sea,
            "routing_factor": route,
        },
        "summary": summary,
        "extras": extras,
        "fx_cny_per_usd": fx,
        "total_cny": {
            "deal": [deal_lo, deal_hi],
            "plan": [plan_lo, plan_hi],
            "stretch": [stretch_lo, stretch_hi],
        },
        "legs": legs,
    }


def _usd_range(pair: list[int]) -> str:
    return f"{pair[0]}–{pair[1]}"


def render_text(result: dict[str, Any]) -> str:
    total = result["total_cny"]
    inputs = result.get("inputs") or {}
    days = inputs.get("advance_days", 30)
    lines = [
        f"**中美交通估算（底价×提前订票×旺季）**：{result['summary']}",
        f"**优惠规划可先按**：约 ¥{total['plan'][0]:,}–{total['plan'][1]:,}"
        f"（人票估，不含宠物；按提前 {days} 天；国内段约 {result['fx_cny_per_usd']} 折合）",
        f"更早／促销下沿：约 ¥{total['deal'][0]:,}–{total['deal'][1]:,}；"
        f"临近／直飞上沿：约 ¥{total['stretch'][0]:,}–{total['stretch'][1]:,}",
        "",
    ]
    for note in result.get("extras") or []:
        lines.append(f"- {note}")
    if result.get("extras"):
        lines.append("")
    for leg in result["legs"]:
        bands = leg["bands"]
        cur = leg["currency"]
        mid = _band_text(bands["mid"], cur)
        low = _band_text(bands["low"], cur)
        high = _band_text(bands["high"], cur)
        trip = "来回" if leg["trip"] == "round_trip" else "单程"
        kind = "国际段" if leg["kind"] == "international" else "美国国内段"
        lines.append(f"{leg['leg']}. **{kind}** {leg['label']}（{trip}）")
        lines.append(f"   - 规划：{mid}；下沿：{low}；上沿：{high}")
        lines.append(f"   - {leg['pet_note']}")
        lines.append("")
    lines.append(f"说明：{result['disclaimer']} 标「估」。口径见 travel-estimate-sources.md。")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SWT 中美机票估算（底价×提前订票×旺季）")
    parser.add_argument("--from", dest="origin", required=True, help="中国出发城市，如 上海")
    parser.add_argument("--gateway", required=True, help="美国入境门户，如 纽约")
    parser.add_argument("--to", dest="destination", help="美国最终城市，如 Myrtle Beach")
    parser.add_argument("--advance-days", type=int, default=None, help="提前订票天数，默认 30")
    parser.add_argument("--month", type=int, default=None, help="主要出发月份 1–12（影响旺季系数）")
    parser.add_argument("--direct", action="store_true", help="偏直飞（国际段加价）")
    parser.add_argument("--one-way", action="store_true", help="只估单程（默认来回）")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args(argv)
    try:
        result = estimate(
            args.origin,
            args.gateway,
            args.destination,
            round_trip=not args.one_way,
            advance_days=args.advance_days,
            travel_month=args.month,
            prefer_direct=args.direct,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        sys.stdout.write(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
