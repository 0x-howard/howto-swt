#!/usr/bin/env python3
"""Estimate nearby second-job *supply* for SWT position analysis (五档星级).

Does not geocode or call Maps APIs. Host web-searches venue counts near the
Offer housing/job address, then passes counts into `score`. Stars measure
walkable venue density only — not hiring, J-1 acceptance, or Sponsor approval.
Second-job pay never enters default ROI.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

# Type weights for walkable venue hits (within ~15 min walk / ~0.5–1 mi).
TYPE_WEIGHTS = {
    "restaurants": 1.0,   # 快餐／餐饮／咖啡 — 最常见 walk-in
    "hotels": 0.8,        # 酒店家政／洗碗
    "grocery": 0.7,       # 便利店／超市
    "seasonal": 0.9,      # 海边小店／游乐场等旺季岗
}

# Competition multiplier from BridgeUSA city presence (host-supplied band).
COMPETITION_FACTOR = {
    "low": 1.05,
    "mid": 1.0,
    "high": 0.8,
    "unknown": 1.0,
}

# Raw weighted score → stars (after competition factor).
STAR_THRESHOLDS = (
    (2.0, 1),
    (4.0, 2),
    (7.0, 3),
    (12.0, 4),
    (float("inf"), 5),
)

ANALYSIS_BY_STARS = {
    1: "周边可步行到达的餐馆／酒店很少，二工供给偏紧（估）",
    2: "周边有少量餐馆或便利店，二工机会有限（估）",
    3: "周围餐馆／酒店有一些，存在二工机会（估）",
    4: "周围餐馆较多，有二工机会（估）",
    5: "周围餐馆／酒店很密，步行范围内二工供给较足（估）",
}

COMPETITION_NOTE = {
    "high": "同城 SWT 参与者较多，店多也可能更卷，宜尽早 walk-in",
    "mid": "",
    "low": "同城 SWT 密度不高，供给分略上调（估）",
    "unknown": "",
}


def _origin_label(
    *,
    address: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
) -> str:
    if address and address.strip():
        return address.strip()
    city_s = (city or "").strip()
    state_s = (state or "").strip().upper()
    zip5 = None
    if zip_code:
        m = re.search(r"\b(\d{5})\b", str(zip_code))
        zip5 = m.group(1) if m else None
    if city_s and state_s:
        return f"{city_s}, {state_s}" + (f" {zip5}" if zip5 else "")
    if state_s and zip5:
        return f"{state_s} {zip5}"
    return city_s or state_s or zip5 or "Offer 地点"


def plan(
    *,
    address: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
) -> dict[str, Any]:
    """Return search queries + host instructions for venue counts."""
    origin = _origin_label(address=address, city=city, state=state, zip_code=zip_code)
    queries = {
        "restaurants": f"restaurants cafes fast food near {origin}",
        "hotels": f"hotels motels near {origin}",
        "grocery": f"grocery stores convenience stores near {origin}",
        "seasonal": f"ice cream shops amusement parks beach boardwalk shops near {origin}",
    }
    return {
        "mode": "plan",
        "origin_label": origin,
        "radius_note_zh": "只计步行约 15 分钟／约 0.5–1 英里内；更远降权或不计（没车学生用不上）",
        "search_queries": queries,
        "count_fields": list(TYPE_WEIGHTS),
        "type_weights": TYPE_WEIGHTS,
        "host_next": (
            "1) 优先用住宿地址，其次雇主地址；"
            "2) 按 search_queries 联网搜索，目测／摘录步行范围内各类场所大约数量（整数，估）；"
            "3) 再跑 score：python3 scripts/second_job_supply.py score "
            "--restaurants N --hotels N --grocery N --seasonal N "
            "[--competition low|mid|high|unknown]；"
            "4) 把返回的 stars／stars_display／analysis_zh／data_line_zh 写入六维二工；"
            "5) 场所≠在招≠收 J-1≠已过 Sponsor；禁止编造数量；二工收入不计入回本。"
        ),
        "student_hint_zh": (
            "二工星级只描述周边场所疏密（估），不是找到二工的概率；"
            "须 Sponsor 批准后才能上工。"
        ),
    }


def _stars_from_score(score: float) -> int:
    for upper, stars in STAR_THRESHOLDS:
        if score < upper:
            return stars
    return 5


def score(
    *,
    restaurants: int = 0,
    hotels: int = 0,
    grocery: int = 0,
    seasonal: int = 0,
    competition: str = "unknown",
    policy_allowed: bool | None = None,
) -> dict[str, Any]:
    """Map host venue counts → 1–5 stars + Chinese analysis line."""
    for name, value in (
        ("restaurants", restaurants),
        ("hotels", hotels),
        ("grocery", grocery),
        ("seasonal", seasonal),
    ):
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{name}: use a non-negative integer count")
    band = (competition or "unknown").strip().lower()
    if band not in COMPETITION_FACTOR:
        raise ValueError("competition: use low|mid|high|unknown")

    raw = (
        restaurants * TYPE_WEIGHTS["restaurants"]
        + hotels * TYPE_WEIGHTS["hotels"]
        + grocery * TYPE_WEIGHTS["grocery"]
        + seasonal * TYPE_WEIGHTS["seasonal"]
    )
    adjusted = raw * COMPETITION_FACTOR[band]
    stars = _stars_from_score(adjusted) if raw > 0 else 1
    if raw == 0:
        stars = 1

    analysis = ANALYSIS_BY_STARS[stars]
    comp_note = COMPETITION_NOTE.get(band) or ""
    bits = [analysis]
    if comp_note:
        bits.append(comp_note)
    if policy_allowed is False:
        bits.insert(0, "Offer／材料写明不允许二工，星级仅作周边供给参考")
    elif policy_allowed is True:
        bits.append("材料允许二工，仍须 Sponsor 书面批准")
    bits.append("二工收入不计入回本")

    display = "🌟" * stars
    data_line = f"周边二工供给 {display}（{stars}/5，估）"
    return {
        "mode": "score",
        "counts": {
            "restaurants": restaurants,
            "hotels": hotels,
            "grocery": grocery,
            "seasonal": seasonal,
        },
        "competition": band,
        "raw_score": round(raw, 2),
        "adjusted_score": round(adjusted, 2),
        "stars": stars,
        "stars_display": display,
        "data_line_zh": data_line,
        "analysis_zh": "；".join(bits),
        "analysis_short_zh": analysis,
        "disclaimer_zh": "场所密度≠在招≠收 J-1≠已批准；星级为规划估",
        "for_budget_details": {
            "second_job_supply_stars": stars,
            "second_job_supply_display": display,
            "second_job_supply_analysis_zh": "；".join(bits),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    plan_p = sub.add_parser("plan", help="emit Maps-style search queries for an address")
    plan_p.add_argument("--address")
    plan_p.add_argument("--city")
    plan_p.add_argument("--state")
    plan_p.add_argument("--zip", dest="zip_code")

    score_p = sub.add_parser("score", help="score venue counts into 1–5 stars")
    score_p.add_argument("--restaurants", type=int, default=0)
    score_p.add_argument("--hotels", type=int, default=0)
    score_p.add_argument("--grocery", type=int, default=0)
    score_p.add_argument("--seasonal", type=int, default=0)
    score_p.add_argument(
        "--competition",
        default="unknown",
        choices=sorted(COMPETITION_FACTOR),
        help="SWT city density band from swt_market (optional)",
    )
    score_p.add_argument(
        "--allowed",
        dest="policy_allowed",
        choices=("true", "false", "unknown"),
        default="unknown",
        help="Offer second_job_allowed if known",
    )

    args = parser.parse_args()
    try:
        if args.cmd == "plan":
            result = plan(
                address=args.address,
                city=args.city,
                state=args.state,
                zip_code=args.zip_code,
            )
        else:
            allowed = None
            if args.policy_allowed == "true":
                allowed = True
            elif args.policy_allowed == "false":
                allowed = False
            result = score(
                restaurants=args.restaurants,
                hotels=args.hotels,
                grocery=args.grocery,
                seasonal=args.seasonal,
                competition=args.competition,
                policy_allowed=allowed,
            )
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
