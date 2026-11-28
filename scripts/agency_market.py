#!/usr/bin/env python3
"""Lookup domestic SWT agency public price / red-flag notes for swt-application.

Also exposes planning_default_cny for swt-position project-fee AskQuestion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from paths import REFERENCES_ROOT

DATA_PATH = REFERENCES_ROOT / "knowledge" / "agencies" / "agencies-market-2026.json"

# Sentinels accepted by budget.py when the student skips naming an agency.
AGENCY_UNKNOWN = "unknown"
AGENCY_OTHER = "other"


def _load() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def _match(agencies: list[dict], name: str) -> list[dict]:
    q = name.strip().lower()
    if not q:
        return []
    hits = []
    for a in agencies:
        blob = f"{a.get('name', '')} {a.get('aliases', '')}".lower()
        if q in blob:
            hits.append(a)
    return hits


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
                {
                    "name": a["name"],
                    "price": a.get("price"),
                    "planning_default_cny": a.get("planning_default_cny"),
                    "verify": a.get("verify"),
                }
                for a in agencies
            ],
        }

    hits = _match(agencies, name)
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


def planning_fee_for(name: str | None) -> dict | None:
    """Resolve one agency's planning_default_cny for position budget confirm."""
    if not name or not str(name).strip():
        return None
    raw = str(name).strip()
    if raw.casefold() in {AGENCY_UNKNOWN, AGENCY_OTHER, "不确定", "其他"}:
        return None
    data = _load()
    hits = _match(data.get("agencies") or [], raw)
    if not hits:
        return None
    # Prefer exact name match, else first substring hit.
    chosen = next((a for a in hits if a.get("name", "").casefold() == raw.casefold()), hits[0])
    fee = chosen.get("planning_default_cny")
    if fee is None:
        return {
            "name": chosen.get("name"),
            "planning_default_cny": None,
            "planning_note": chosen.get("planning_note") or "表内无单一人民币默认",
            "price": chosen.get("price"),
        }
    return {
        "name": chosen.get("name"),
        "planning_default_cny": int(fee),
        "planning_note": chosen.get("planning_note") or "",
        "price": chosen.get("price"),
    }


def agency_ask_options(*, global_default_cny: float) -> list[dict]:
    """AskQuestion options: named agencies with table fee + other + unknown."""
    data = _load()
    options: list[dict] = []
    for a in data.get("agencies") or []:
        fee = a.get("planning_default_cny")
        if fee is None:
            continue
        name = a["name"]
        options.append({
            "id": f"agency:{name}",
            "label": f"{name}（表内约¥{int(fee):,}）",
            "agency": name,
            "proposed_project_cost_cny": int(fee),
        })
    options.append({
        "id": "agency_other",
        "label": "其他机构／我自己填项目费",
        "agency": AGENCY_OTHER,
    })
    display = f"¥{float(global_default_cny):,.0f}"
    options.append({
        "id": "agency_unknown",
        "label": f"不确定，用通用默认 {display}",
        "agency": AGENCY_UNKNOWN,
        "proposed_project_cost_cny": float(global_default_cny),
    })
    return options


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", help="agency name or alias substring, e.g. 西米")
    parser.add_argument("--list", action="store_true", help="list all agency names")
    parser.add_argument(
        "--planning-fee",
        metavar="NAME",
        help="print planning_default_cny for one agency (position fee confirm)",
    )
    args = parser.parse_args()
    try:
        if args.planning_fee:
            result = planning_fee_for(args.planning_fee) or {
                "query": args.planning_fee,
                "planning_default_cny": None,
                "error": "not_found",
            }
        else:
            result = lookup(name=args.name, list_all=args.list or not args.name)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
