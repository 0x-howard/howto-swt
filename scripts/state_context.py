#!/usr/bin/env python3
"""Resolve SWT Offer locations to the shared state-context knowledge layer.

This module deliberately resolves a location only when the user supplied a
state or when a place has an explicit entry in STATE_INDEX.md.  It is not a
geocoder and must never infer a state from a similar-looking city name.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Mapping

from paths import PLUGIN_ROOT

ROOT = PLUGIN_ROOT
STATE_CONTEXT_ROOT = ROOT / "references" / "knowledge" / "state_context"
STATE_INDEX_PATH = STATE_CONTEXT_ROOT / "STATE_INDEX.md"
STATES_DIR = STATE_CONTEXT_ROOT / "states"
MISSING_VALUE = "暂无可靠数据"

CODE_TO_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}
NAME_TO_CODE = {name.casefold(): code for code, name in CODE_TO_NAME.items()}

SECTIONS = ("收入", "住宿", "生活", "交通", "二工", "落地便利")
REQUIRED_FIELDS = (
    "州", "州缩写",
    "常见时薪", "常见工时", "最低工资", "州所得税",
    "常见周租", "雇主住宿",
    "每周基础开销", "销售税",
    "公共交通", "自行车", "通勤",
    "好不好找", "常见工资", "竞争程度",
    "SSN", "银行", "DMV/州ID", "超市", "医疗", "健身房",
)


@dataclass(frozen=True)
class StateResolution:
    code: str
    name: str
    source: str


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", value.casefold())).strip()


def _index_entries(index_path: Path = STATE_INDEX_PATH) -> Mapping[str, str]:
    entries: dict[str, str] = {}
    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 2 or cells[0] in {"地点", "---"}:
            continue
        code = cells[1].upper()
        if code not in CODE_TO_NAME:
            raise ValueError(f"STATE_INDEX.md has an invalid state code: {code}")
        key = _normalise(cells[0])
        if key in entries and entries[key] != code:
            raise ValueError(f"STATE_INDEX.md maps {cells[0]!r} to two states")
        entries[key] = code
    return entries


def resolve_state(location: str, index_path: Path = STATE_INDEX_PATH) -> StateResolution | None:
    """Resolve an explicit state first, then an exact place in STATE_INDEX.md."""
    if not location or not location.strip():
        return None
    supplied = location.strip()
    folded = supplied.casefold()

    # A field containing only a state is unambiguously explicit.  Check it
    # before the index, while letting a city such as "Wisconsin Dells" reach
    # its exact STATE_INDEX.md entry rather than matching the word Wisconsin.
    normalised = _normalise(supplied)
    for name, code in NAME_TO_CODE.items():
        if normalised == _normalise(name):
            return StateResolution(code, CODE_TO_NAME[code], "explicit_state_name")

    # State abbreviations must remain uppercase in user input.  This avoids
    # treating ordinary words such as "in" as the code for Indiana.
    for token in re.findall(r"(?<![A-Za-z])[A-Z]{2}(?![A-Za-z])", supplied):
        if token in CODE_TO_NAME:
            return StateResolution(token, CODE_TO_NAME[token], "explicit_state_code")

    code = _index_entries(index_path).get(normalised)
    if code is not None:
        return StateResolution(code, CODE_TO_NAME[code], "state_index")

    # This captures full Offer phrasing such as "Myrtle Beach, South
    # Carolina" after exact indexed places have had priority.
    for name, code in NAME_TO_CODE.items():
        if re.search(rf"(?<![a-z]){re.escape(name)}(?![a-z])", folded):
            return StateResolution(code, CODE_TO_NAME[code], "explicit_state_name")
    return None


def profile_path(code: str, states_dir: Path = STATES_DIR) -> Path:
    code = code.upper()
    if code not in CODE_TO_NAME:
        raise ValueError(f"Unknown state code: {code}")
    return states_dir / f"{code}.md"


def load_state_profile(code: str, states_dir: Path = STATES_DIR) -> dict[str, str]:
    """Load the fixed product schema, falling back for blank field values."""
    path = profile_path(code, states_dir)
    content = path.read_text(encoding="utf-8")
    profile: dict[str, str] = {}
    for field in REQUIRED_FIELDS:
        match = re.search(rf"^{re.escape(field)}:\s*(.*)$", content, re.MULTILINE)
        if match is None:
            profile[field] = MISSING_VALUE
        else:
            value = match.group(1).strip()
            profile[field] = value or MISSING_VALUE
    return profile


def compare_offer_wage(offer_wage: float, state_range: str) -> str:
    """Return a conservative comparison without overwriting the Offer value."""
    values = [float(value) for value in re.findall(r"\d+(?:\.\d+)?", state_range)]
    if not values:
        return "unavailable"
    lower, upper = values[0], values[1] if len(values) > 1 else values[0]
    if offer_wage > upper:
        return "higher"
    if offer_wage < lower:
        return "lower"
    return "within"


def render_state_reference(profile: Mapping[str, str], fields: tuple[str, ...]) -> str:
    """Render only caller-selected relevant state fields, never a full default card."""
    if not fields:
        raise ValueError("Select fields relevant to the user's decision")
    invalid = set(fields) - set(REQUIRED_FIELDS)
    if invalid or any(field in {"州", "州缩写"} for field in fields):
        raise ValueError(f"Invalid reference fields: {sorted(invalid)}")
    return f"{profile['州']} 州级参考：" + "；".join(
        f"{field} {profile[field]}" for field in fields
    ) + "。"


def _main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] != "resolve":
        print("Usage: python3 scripts/state_context.py resolve <location>", file=sys.stderr)
        return 2
    resolution = resolve_state(argv[2])
    if resolution is None:
        print(json.dumps({"state": None, "status": "unknown"}, ensure_ascii=False))
        return 0
    payload = {
        "state": resolution.code,
        "state_name": resolution.name,
        "source": resolution.source,
        "profile_exists": profile_path(resolution.code).is_file(),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
