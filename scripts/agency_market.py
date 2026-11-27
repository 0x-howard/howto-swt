#!/usr/bin/env python3
"""Lookup domestic SWT agency public price / red-flag notes for swt-application."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paths import REFERENCES_ROOT

DATA_PATH = REFERENCES_ROOT / "knowledge" / "agencies" / "agencies-market-2026.json"


def _load() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def lookup(*, name: str | None = None, list_all: bool = False) -> dict:
    data = _load()
    agencies = data.get("agencies") or []
    if list_all or not name:
        return {
            "source": data.get("source"),
            "researched_at": data.get("researched_at"),
            "disclaimer": data.get("disclaimer"),
            "count": len(agencies),
            "agencies": [
                {"name": a["name"], "price": a.get("price"), "verify": a.get("verify")}
                for a in agencies
            ],
        }

    q = name.strip().lower()
    hits = []
    for a in agencies:
        blob = f"{a.get('name','')} {a.get('aliases','')}".lower()
        if q in blob:
            hits.append(a)
    return {
        "source": data.get("source"),
        "researched_at": data.get("researched_at"),
        "disclaimer": data.get("disclaimer"),
        "query": name,
        "count": len(hits),
        "agencies": hits,
        "student_hint_zh": (
            "以上为公开价／口碑摘要，带年份；冲突原样保留。"
            "付款前以合同、正式报价和 BridgeUSA Sponsor 英文法定名为准。"
            if hits
            else "资料里没有这家的可核验条目；按选机构清单问清 Sponsor、退款与合同，勿凭品牌大小判断。"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", help="agency name or alias substring, e.g. 西米")
    parser.add_argument("--list", action="store_true", help="list all agency names")
    args = parser.parse_args()
    try:
        result = lookup(name=args.name, list_all=args.list or not args.name)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
