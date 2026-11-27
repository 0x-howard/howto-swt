#!/usr/bin/env python3
"""Lookup SSA field offices for SWT position landing convenience.

Rank for an Offer location: same city → same ZIP → same ZIP3 → other offices in state.
Does not compute GPS miles (no geocoder); say “同城／同 ZIP／同州邻近列表”, not exact distance.
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
            # "123 Main St, Myrtle Beach, SC 29577" → take token before state/zip
            parts = [p.strip() for p in addr.split(",") if p.strip()]
            if len(parts) >= 2:
                candidate = parts[-2]
                # drop trailing state if glued
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
    ranked.sort(key=lambda item: (item[0][0], item[1]["city"], item[1]["address"]))

    offices = []
    for (tier_n, tier_name), row in ranked[: max(1, limit)]:
        offices.append({**row, "match": tier_name, "match_rank": tier_n})

    best = offices[0]["match"] if offices else None
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
        "student_hint_zh": _hint_zh(best, loc["city"], state_code),
        "verify": {
            "locator": "https://www.ssa.gov/locator",
            "phone": "1-800-772-1213",
            "note": "snapshot may be stale; verify before travel; not GPS miles",
        },
    }


def _hint_zh(best: str | None, city: str | None, state: str | None) -> str:
    place = city or state or "该地"
    if best in {"same_city", "same_city_zip"}:
        return f"{place} 同城有 SSA 办公室可办 SSN；出发前用 Locator 核实是否仍开放。"
    if best == "same_zip":
        return f"与 Offer 同一 ZIP 有 SSA 办公室；同城名称可能不同，出发前核实。"
    if best == "same_zip3":
        return f"{place} 同城未收录办公室，下列为相近 ZIP 区的 SSA；可能需跨城，出发前用 Locator 核实。"
    if best == "same_state":
        return f"{place} 同城／同 ZIP 未命中，下列为同州办公室列表（非精确距离）；请用 Locator 按住址找最近点。"
    return "未查到可用办公室；请用 SSA Locator 按 ZIP 检索。"


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
