#!/usr/bin/env python3
"""Dependency-free SVG line chart for a 2–3 offer comparison."""

from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import Any


WIDTH, HEIGHT = 760, 460
LEFT, RIGHT, TOP, BOTTOM = 90, 40, 70, 110
COLORS = ("#2563eb", "#ea580c", "#16a34a")
DASHES = ("", "8 6", "2 5")
FONT = "PingFang SC, Hiragino Sans GB, Microsoft YaHei, Noto Sans CJK SC, sans-serif"


def _nice_bounds(values: list[float]) -> tuple[int, int, int]:
    low, high = min(min(values), 0), max(max(values), 0)
    span = max(high - low, 1)
    step = next(s for s in (100, 250, 500, 1000, 2000, 5000, 10000) if span / s <= 8)
    return int(low // step * step), int(-(-high // step) * step) + step, step


def _money(value: float) -> str:
    return f"−${abs(value):,.0f}" if value < 0 else f"${value:,.0f}"


def render_offer_chart(result: dict[str, Any]) -> str:
    analysis = result["offer_return_analysis"]
    if analysis.get("analysis_status") != "complete" or "chart" not in analysis:
        raise ValueError("chart requires a complete 2–3 offer comparison")
    chart = analysis["chart"]
    hours = [float(h) for h in chart["hours"]]
    series = chart["series"]
    values = [float(v) for item in series for v in item["values"]]
    y_low, y_high, y_step = _nice_bounds(values)
    x_low, x_high = hours[0], hours[-1]
    final = chart["y_basis"] == "final_project_surplus"
    y_title = "最终预计结余" if final else "在美预计结余"

    def px(x: float) -> float:
        return LEFT + (x - x_low) / ((x_high - x_low) or 1) * (WIDTH - LEFT - RIGHT)

    def py(y: float) -> float:
        return TOP + (y_high - y) / ((y_high - y_low) or 1) * (HEIGHT - TOP - BOTTOM)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{FONT}">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
        f'<text x="{LEFT}" y="34" font-size="20" font-weight="600" fill="#111">每周工时与{y_title}</text>',
    ]
    if result.get("offers") and result["offers"][0].get("fx_cny_per_usd"):
        out.append(f'<text x="{LEFT}" y="56" font-size="13" fill="#666">汇率 {result["offers"][0]["fx_cny_per_usd"]}</text>')
    for y in range(y_low, y_high + 1, y_step):
        out.append(f'<line x1="{LEFT}" x2="{WIDTH - RIGHT}" y1="{py(y):.1f}" y2="{py(y):.1f}" stroke="#eeeeee"/>')
        out.append(f'<text x="{LEFT - 10}" y="{py(y) + 4:.1f}" font-size="12" fill="#888" text-anchor="end">{_money(y)}</text>')
    out.append(f'<line x1="{LEFT}" x2="{WIDTH - RIGHT}" y1="{py(0):.1f}" y2="{py(0):.1f}" stroke="#333" stroke-width="1.2"/>')
    if final:
        out.append(f'<text x="{WIDTH - RIGHT}" y="{py(0) - 6:.1f}" font-size="12" fill="#333" text-anchor="end">回本线</text>')
    for h, label in zip(hours, chart["hours"]):
        out.append(f'<text x="{px(h):.1f}" y="{HEIGHT - BOTTOM + 20}" font-size="12" fill="#888" text-anchor="middle">{label}h</text>')
    out.append(f'<text x="{(LEFT + WIDTH - RIGHT) / 2:.1f}" y="{HEIGHT - BOTTOM + 42}" font-size="13" fill="#555" '
               f'text-anchor="middle">每周平均工时</text>')

    for index, item in enumerate(series):
        points = " ".join(f"{px(h):.1f},{py(float(v)):.1f}" for h, v in zip(hours, item["values"]))
        dash = f' stroke-dasharray="{DASHES[index]}"' if DASHES[index] else ""
        out.append(f'<polyline points="{points}" fill="none" stroke="{COLORS[index]}" stroke-width="3"{dash}/>')

    costs = {offer["id"]: float(offer["project_cost_usd"]) for offer in result.get("offers", [])
             if final and offer.get("project_cost_usd") is not None}
    for crossing in analysis.get("intersections", []):
        if not crossing.get("meaningful_for_optimum"):
            continue
        x = float(crossing["hours_per_week"])
        y = float(crossing["season_net_surplus_usd"]) - costs.get(crossing["offers"][0], 0.0)
        out.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="5" fill="#111"/>')
        out.append(f'<text x="{px(x) - 8:.1f}" y="{py(y) - 12:.1f}" font-size="12" fill="#111" '
                   f'text-anchor="end">{Decimal(crossing["hours_per_week"]).normalize():f}h 持平</text>')

    legend_y = HEIGHT - 30
    x = LEFT
    for index, item in enumerate(series):
        dash = f' stroke-dasharray="{DASHES[index]}"' if DASHES[index] else ""
        out.append(f'<line x1="{x}" x2="{x + 28}" y1="{legend_y}" y2="{legend_y}" stroke="{COLORS[index]}" stroke-width="3"{dash}/>')
        label = escape(item["label"])
        out.append(f'<text x="{x + 34}" y="{legend_y + 4}" font-size="12" fill="#333">{label}</text>')
        x += 50 + 13 * len(item["label"])
    out.append("</svg>")
    return "\n".join(out)
