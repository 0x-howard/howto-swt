#!/usr/bin/env python3
"""Lookup SSA field offices for SWT position landing convenience."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from paths import REFERENCES_ROOT

CSV_PATH = REFERENCES_ROOT / "knowledge" / "ssa_offices" / "ssa-offices-clean.csv"


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
                "zip": (row.get("zip") or "").strip(),
                "phone": (row.get("phone") or "").strip(),
                "hours": (row.get("hours") or "").strip(),
            }
        )
    return rows


def lookup(*, state: str | None = None, city: str | None = None, limit: int = 8) -> dict:
    """Return offices filtered by state and optional city (case-insensitive contains)."""
    state_code = (state or "").strip().upper() or None
    city_q = (city or "").strip().lower() or None
    if not state_code and not city_q:
        raise ValueError("provide --state and/or --city")

    all_rows = _load()
    matched = []
    for row in all_rows:
        if state_code and row["state"] != state_code:
            continue
        if city_q and city_q not in row["city"].lower():
            continue
        matched.append(row)

    # If city filter empty under state, keep all state offices but mark city_miss.
    city_miss = bool(city_q and state_code and not matched)
    if city_miss:
        matched = [r for r in all_rows if r["state"] == state_code]

    matched.sort(key=lambda r: (0 if city_q and city_q in r["city"].lower() else 1, r["city"], r["address"]))
    capped = matched[: max(1, limit)]
    return {
        "source": "ssa-offices-clean.csv",
        "snapshot": "2026-03-09",
        "query": {"state": state_code, "city": city, "limit": limit},
        "city_exact_miss": city_miss,
        "count": len(capped),
        "total_in_scope": len(matched),
        "offices": capped,
        "verify": {
            "locator": "https://www.ssa.gov/locator",
            "phone": "1-800-772-1213",
            "note": "snapshot may be stale; verify before travel",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", help="two-letter state / territory code, e.g. SC")
    parser.add_argument("--city", help="city name substring, e.g. Myrtle Beach")
    parser.add_argument("--limit", type=int, default=8, help="max offices to return")
    args = parser.parse_args()
    try:
        result = lookup(state=args.state, city=args.city, limit=args.limit)
    except Exception as exc:  # noqa: BLE001 — CLI surface
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
