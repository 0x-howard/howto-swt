#!/usr/bin/env python3
"""Lookup SSA field offices for SWT position landing convenience.

Rank: same city → same ZIP → same ZIP3 → other offices in state.
Script does not geocode. Host should web-search approximate driving distance
from the Offer job/housing address to the top office, then write 约 X 英里（估）.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from paths import REFERENCES_ROOT

CSV_PATH = REFERENCES_ROOT / "knowledge" / "ssa_offices" / "ssa-offices-clean.csv"
ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b")
STATE_RE = re.compile(r"\b([A-Za-z]{2})\b\s*(?:\d{5})?\s*$")


def _load() -> list[dict[str, str]]:
    text = CSV_PATH.read_text(encoding="utf-8-sig")
    rows: list[dict[str, str]] = []
    for row in csv.DictReader(text.splitlines()):
        rows.append(
            {
                "office_code": (row.get("office_code") or "").strip(),
                "type": (row.get("type") or "").strip(),
                "state": (row.get("state") or "").strip().upper(),
                "city": (row.get("city") or "").strip(),
                "address": (row.get("address") or "").strip().lstrip(",").strip(),
                "zip": (row.get("zip") or "").strip()[:5],
                "phone": (row.get("phone") or "").strip(),
                "hours": (row.get("hours") or "").strip(),
            }
        )
    return rows


def parse_offer_location(
    *,
    state: str | None = None,
    city: str | None = None,
    zip_code: str | None = None,
    address: str | None = None,
) -> dict[str, str | None]:
    """Normalize Offer city/state/ZIP; optionally scrape ZIP/state from a free-text address."""
    state_code = (state or "").strip().upper() or None
    city_name = (city or "").strip() or None
    zip5 = None
    if zip_code:
        m = ZIP_RE.search(str(zip_code))
        zip5 = m.group(1) if m else None
    addr = (address or "").strip() or None
    if addr:
        if not zip5:
            m = ZIP_RE.search(addr)
            if m:
                zip5 = m.group(1)
        if not state_code:
            m = STATE_RE.search(addr)
            if m:
                state_code = m.group(1).upper()
        if not city_name:
            parts = [p.strip() for p in addr.split(",") if p.strip()]
            if len(parts) >= 2:
                candidate = parts[-2]
                candidate = re.sub(r"\s+[A-Za-z]{2}\s*$", "", candidate).strip()
                if candidate and not ZIP_RE.fullmatch(candidate):
                    city_name = candidate
    return {"state": state_code, "city": city_name, "zip": zip5, "address": addr}


def _tier(row: dict[str, str], *, city_q: str | None, zip5: str | None) -> tuple[int, str]:
    city_hit = bool(city_q and city_q in row["city"].lower())
    zip_hit = bool(zip5 and row["zip"] == zip5)
    zip3_hit = bool(zip5 and len(zip5) >= 3 and row["zip"].startswith(zip5[:3]))
    if city_hit and zip_hit:
        return 0, "same_city_zip"
    if city_hit:
        return 1, "same_city"
    if zip_hit:
        return 2, "same_zip"
    if zip3_hit:
        return 3, "same_zip3"
    return 4, "same_state"


def _office_line(office: dict[str, str]) -> str:
    bits = [
        office.get("city") or "",
        office.get("address") or "",
        f"{office.get('state', '')} {office.get('zip', '')}".strip(),
    ]
    where = ", ".join(b for b in bits if b)
    phone = office.get("phone") or ""
    hours = office.get("hours") or ""
    parts = [p for p in (where, hours, phone) if p]
    return "；".join(parts)


def _origin_label(loc: dict[str, str | None]) -> str:
    if loc.get("address"):
        return str(loc["address"])
    city = loc.get("city")
    state = loc.get("state")
    zip5 = loc.get("zip")
    if city and state:
        return f"{city}, {state}" + (f" {zip5}" if zip5 else "")
    if state and zip5:
        return f"{state} {zip5}"
    return city or state or zip5 or "Offer 地点"


def _distance_search_query(origin: str, office: dict[str, str]) -> str:
    dest = ", ".join(
        b for b in (
            office.get("address"),
            office.get("city"),
            f"{office.get('state', '')} {office.get('zip', '')}".strip(),
        ) if b
    )
    return f"driving distance from {origin} to {dest}"


def _landing_line_zh(office: dict[str, str], *, match: str | None, place: str | None) -> str:
    """Lead with office location; match tier is secondary. Distance filled by host web search."""
    line = f"SSA 办公室：{_office_line(office)}"
    if match in {"same_city", "same_city_zip"}:
        return f"{line}（{place or '岗位'}同城）"
    if match == "same_zip":
        return f"{line}（与 Offer 同一 ZIP）"
    if match == "same_zip3":
        return f"{line}（相近 ZIP 区）"
    if match == "same_state":
        return f"{line}（同州候选，须联网比车程后选用最近的）"
    return line


def _hint_zh(best: str | None, city: str | None, state: str | None) -> str:
    place = city or state or "该地"
    if best in {"same_city", "same_city_zip"}:
        return f"{place} 同城有 SSA；请联网估到办公室车程（标估），并用 Locator 核实。"
    if best == "same_zip":
        return "与 Offer 同一 ZIP 有 SSA；请联网估车程（标估），并用 Locator 核实。"
    if best == "same_zip3":
        return f"{place} 同城表未收录，已给相近 ZIP 区办公室；请联网估车程，并用 Locator 核实。"
    if best == "same_state":
        return (
            "同城／同 ZIP 表未直接命中时，先给出同州候选办公室地址，"
            "再对前几个候选联网查 driving distance，选用最近的一个写入落地便利（约 X 英里／Y 分钟，标估）；"
            "表内字母序不是远近。最后用 Locator 或 1-800-772-1213 核实。"
        )
    return "未查到可用办公室；请用 SSA Locator 按 ZIP 检索。"


def lookup(
    *,
    state: str | None = None,
    city: str | None = None,
    zip_code: str | None = None,
    address: str | None = None,
    limit: int = 5,
) -> dict:
    """Return nearby SSA offices for an Offer location."""
    loc = parse_offer_location(state=state, city=city, zip_code=zip_code, address=address)
    state_code = loc["state"]
    city_q = (loc["city"] or "").lower() or None
    zip5 = loc["zip"]
    if not state_code and not city_q and not zip5:
        raise ValueError("provide --state / --city / --zip, or --address with city/state/ZIP")

    all_rows = _load()
    scoped = [r for r in all_rows if (not state_code or r["state"] == state_code)]
    if not scoped and city_q:
        scoped = [r for r in all_rows if city_q in r["city"].lower()]

    ranked: list[tuple[tuple[int, str], dict[str, str]]] = []
    for row in scoped:
        tier_n, tier_name = _tier(row, city_q=city_q, zip5=zip5)
        ranked.append(((tier_n, tier_name), row))
    # FO before RS within the same tier; city alpha is only a stable tie-break, NOT distance.
    ranked.sort(key=lambda item: (
        item[0][0],
        0 if item[1].get("type") == "FO" else 1,
        item[1]["city"],
        item[1]["address"],
    ))

    # City-only same_state lookups need more candidates for the host to distance-rank.
    fetch = max(limit, 5) if (city_q and not zip5) else max(1, limit)
    offices = []
    for (tier_n, tier_name), row in ranked[:fetch]:
        offices.append({**row, "match": tier_name, "match_rank": tier_n})

    best = offices[0]["match"] if offices else None
    top = offices[0] if offices else None
    origin = _origin_label(loc)
    landing = _landing_line_zh(top, match=best, place=loc["city"]) if top else None
    distance_queries = [_distance_search_query(origin, office) for office in offices[:5]]
    nearest_search = (
        f"nearest Social Security Administration office to {origin} driving distance"
        if origin else None
    )

    return {
        "source": "ssa-offices-clean.csv",
        "snapshot": "2026-03-09",
        "query": {
            "state": state_code,
            "city": loc["city"],
            "zip": zip5,
            "address": loc["address"],
            "limit": limit,
        },
        "best_match": best,
        "same_city": best in {"same_city", "same_city_zip"} if best else False,
        "count": len(offices),
        "total_in_scope": len(scoped),
        "offices": offices,
        "origin_label": origin,
        "landing_line_zh": landing,
        "distance_search_query": distance_queries[0] if distance_queries else None,
        "distance_search_queries": distance_queries,
        "nearest_office_search_query": nearest_search,
        "host_next": (
            "1) 数据列先写 SSA 办公室地址（不要先写「未命中」）；"
            "2) 若 best_match 为 same_state／same_zip3：对 offices 前几个用 distance_search_queries "
            "或 nearest_office_search_query 联网查车程，选用最近的一个重写 landing，并写约 X 英里／Y 分钟（估）；"
            "3) 同城命中也建议搜一次车程；搜不到就省略距离，禁止编造；"
            "4) 分析列：快照日期 + Locator／1-800-772-1213 核实。"
        ),
        "student_hint_zh": _hint_zh(best, loc["city"], state_code),
        "verify": {
            "locator": "https://www.ssa.gov/locator",
            "phone": "1-800-772-1213",
            "note": "snapshot may be stale; pick nearest via host web distance, not CSV row order",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", help="two-letter state / territory code, e.g. SC")
    parser.add_argument("--city", help="city name, e.g. Myrtle Beach")
    parser.add_argument("--zip", dest="zip_code", help="5-digit ZIP from Offer / housing")
    parser.add_argument("--address", help="free-text Offer / housing address")
    parser.add_argument("--limit", type=int, default=5, help="max offices to return")
    args = parser.parse_args()
    try:
        result = lookup(
            state=args.state,
            city=args.city,
            zip_code=args.zip_code,
            address=args.address,
            limit=args.limit,
        )
    except Exception as exc:  # noqa: BLE001 — CLI surface
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
