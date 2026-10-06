#!/usr/bin/env python3
"""Read-only resolver for the SWT market knowledge layer."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
MARKET_ROOT = SKILL_ROOT / "references" / "knowledge" / "swt_market"

LIMITATIONS = [
    "participant count is BridgeUSA SWT Map participant count",
    "not verified as deduplicated annual participants",
    "rankings are based only on current dataset participant count",
    "support group regional records do not imply city-level coverage",
]

CITY_MARKET_FIELDS = (
    "active",
    "initial",
    "total",
    "point_count",
    "representative_latitude",
    "representative_longitude",
    "active_share",
    "national_rank_by_total",
    "state_rank_by_total",
)

STATE_MARKET_FIELDS = (
    "active",
    "initial",
    "total",
    "city_count",
    "point_count",
    "top_city_record",
    "top_city_record_total",
    "active_share",
    "national_rank_by_total",
    "support_group_record_count",
)

REGIONAL_MATCH_TYPES = {"multi_city", "regional", "county_or_region", "affiliate", "unmatched"}
REGIONAL_SCOPES = {"multi_city", "county_or_region", "affiliate", "regional"}


def load_market_data() -> dict[str, Any]:
    """Load the four fixed SWT market reference files, independent of cwd."""
    return {
        "states": _read_json("state_summary.json"),
        "cities": _read_json("city_summary.json"),
        "support_groups": _read_json("support_groups.json"),
        "source_metadata": _read_json("source_metadata.json"),
    }


def _read_json(filename: str) -> Any:
    with (MARKET_ROOT / filename).open(encoding="utf-8") as handle:
        return json.load(handle)


def _key(value: Any) -> str:
    return str(value).strip().casefold()


def _resolve_state(query: str | None, data: dict[str, Any]) -> dict[str, Any]:
    if query is not None:
        normalized = _key(query)
        for row in data["states"]:
            if normalized in (_key(row["state"]), _key(row["state_code"])):
                return {
                    "matched": True,
                    "match_level": "state_exact",
                    "state": row["state"],
                    "state_code": row["state_code"],
                    "state_market": row,
                }
    return {
        "matched": False,
        "match_level": "state_not_found",
        "requested_state": query,
    }


def resolve_state(query: str) -> dict[str, Any]:
    """Resolve an exact state name or code (case and outer spaces ignored)."""
    return _resolve_state(query, load_market_data())


def _resolve_city(
    city: str,
    state: str | None,
    data: dict[str, Any],
) -> dict[str, Any]:
    requested_city = city
    normalized_city = _key(city)

    if state is not None:
        state_result = _resolve_state(state, data)
        if not state_result["matched"]:
            return {
                "matched": False,
                "match_level": "state_not_found",
                "requested_city": requested_city,
                "requested_state": state,
            }
        state_row = state_result["state_market"]
        for row in data["cities"]:
            if (
                row["state_code"] == state_row["state_code"]
                and _key(row["city"]) == normalized_city
            ):
                return {
                    "matched": True,
                    "match_level": "city_exact",
                    "state": row["state"],
                    "state_code": row["state_code"],
                    "city": row["city"],
                    "city_market": row,
                    "state_market": state_row,
                }
        return {
            "matched": True,
            "match_level": "state_fallback",
            "requested_city": requested_city,
            "city_found": False,
            "state": state_row["state"],
            "state_code": state_row["state_code"],
            "state_market": state_row,
        }

    matches = [row for row in data["cities"] if _key(row["city"]) == normalized_city]
    if len(matches) == 1:
        row = matches[0]
        state_row = next(item for item in data["states"] if item["state_code"] == row["state_code"])
        return {
            "matched": True,
            "match_level": "city_exact",
            "state": row["state"],
            "state_code": row["state_code"],
            "city": row["city"],
            "city_market": row,
            "state_market": state_row,
        }
    if len(matches) > 1:
        candidates = sorted(
            {row["state_code"]: {"state": row["state"], "state_code": row["state_code"]} for row in matches}.values(),
            key=lambda row: row["state"].casefold(),
        )
        return {
            "matched": False,
            "match_level": "city_ambiguous",
            "requested_city": requested_city,
            "candidate_states": candidates,
        }
    return {
        "matched": False,
        "match_level": "city_not_found",
        "requested_city": requested_city,
    }


def resolve_city(city: str, state: str | None = None) -> dict[str, Any]:
    """Resolve a city by exact name, optionally scoped to an exact state."""
    return _resolve_city(city, state, load_market_data())


def get_state_market(state: str) -> dict[str, Any]:
    """Return the state resolver result, including the full state market row."""
    return _resolve_state(state, load_market_data())


def get_city_market(city: str, state: str) -> dict[str, Any]:
    """Return the city resolver result, including exact or state fallback data."""
    return _resolve_city(city, state, load_market_data())


def _truthy(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.strip().casefold() == "true")


def _is_exact_city_group(group: dict[str, Any]) -> bool:
    return (
        _key(group.get("match_type")) == "exact"
        and _key(group.get("location_scope")) == "city"
    )


def _is_regional_group(group: dict[str, Any]) -> bool:
    return (
        _key(group.get("match_type")) in REGIONAL_MATCH_TYPES
        or _key(group.get("location_scope")) in REGIONAL_SCOPES
    )


def _city_is_named_in_record(city: str, group: dict[str, Any]) -> bool:
    target = _key(city)
    explicit_names = [part.strip() for part in (group.get("matched_city") or "").split(";")]
    if target and any(_key(name) == target for name in explicit_names):
        return True

    # Some partial multi-city records retain their locations in the original
    # normalized string even when only one location was matched. Treat those
    # as regional evidence only, never as a city-level match.
    normalized_location = group.get("location_normalized") or ""
    phrases = re.split(r"\s+and\s+|\s*/\s*", normalized_location, flags=re.IGNORECASE)
    return target != "" and any(_key(phrase) == target for phrase in phrases)


def _get_support_context(
    city: str | None,
    state: str | None,
    data: dict[str, Any],
    city_result: dict[str, Any] | None = None,
    state_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if city_result is None and city is not None:
        city_result = _resolve_city(city, state, data)
    if state_result is None and state is not None:
        state_result = _resolve_state(state, data)

    resolved_state_code: str | None = None
    if city_result and city_result.get("matched"):
        resolved_state_code = city_result.get("state_code")
    elif state_result and state_result.get("matched"):
        resolved_state_code = state_result.get("state_code")

    if state is not None and state_result and not state_result["matched"]:
        return {
            "matched": False,
            "match_level": "state_not_found",
            "support_level": "none",
            "has_support_group": False,
            "city_exact_support": [],
            "regional_support": [],
        }

    if city is not None and city_result and city_result.get("match_level") == "city_ambiguous":
        return {
            "matched": False,
            "match_level": "city_ambiguous",
            "candidate_states": city_result["candidate_states"],
            "support_level": "unresolved",
            "has_support_group": False,
            "city_exact_support": [],
            "regional_support": [],
        }

    if city is not None and city_result and not city_result.get("matched"):
        return {
            "matched": False,
            "match_level": city_result.get("match_level"),
            "support_level": "none",
            "has_support_group": False,
            "city_exact_support": [],
            "regional_support": [],
        }

    city_row = city_result.get("city_market") if city_result else None
    exact_city_match = bool(
        city_row
        and _truthy(city_row.get("has_support_group"))
        and _key(city_row.get("support_group_match_type")) == "exact"
    )
    groups = data["support_groups"]
    scoped_groups = [
        row for row in groups
        if resolved_state_code is None or row["state_code"] == resolved_state_code
    ]

    exact_support: list[dict[str, Any]] = []
    if city is not None and city_row and exact_city_match:
        exact_support = [
            row for row in scoped_groups
            if _is_exact_city_group(row)
            and _key(row.get("matched_city")) == _key(city_row["city"])
        ]
        if not exact_support:
            exact_support = [{
                "state": city_row["state"],
                "state_code": city_row["state_code"],
                "matched_city": city_row["city"],
                "support_group_name": city_row.get("support_group_name", ""),
                "website": city_row.get("support_group_url", ""),
                "match_type": "exact",
                "match_confidence": "high",
            }]
    elif city is None:
        exact_support = [row for row in scoped_groups if _is_exact_city_group(row)]

    regional_support = []
    for row in scoped_groups:
        if not _is_regional_group(row):
            continue
        if city is None or _city_is_named_in_record(city, row):
            regional_support.append(row)

    if city is not None and city_result:
        matched = bool(city_result.get("matched"))
        match_level = city_result.get("match_level")
    elif state is not None and state_result:
        matched = bool(state_result.get("matched"))
        match_level = state_result.get("match_level")
    else:
        matched = True
        match_level = "all_support_context"

    if city is not None:
        support_level = "city_exact" if exact_city_match else (
            "regional_evidence" if regional_support else "none"
        )
    elif state is not None:
        support_level = "state_context" if exact_support or regional_support else "none"
    else:
        support_level = "all_support_context"

    return {
        "matched": matched,
        "match_level": match_level,
        "support_level": support_level,
        "has_support_group": exact_city_match if city is not None else None,
        "city_exact_support": exact_support,
        "regional_support": regional_support,
    }


def get_support_context(city: str | None = None, state: str | None = None) -> dict[str, Any]:
    """Return exact city support separately from scoped regional evidence."""
    data = load_market_data()
    return _get_support_context(city, state, data)


def _source_context(data: dict[str, Any], market_row: dict[str, Any] | None) -> dict[str, Any]:
    metadata = data["source_metadata"]
    return {
        "source_name": (market_row or {}).get("source_name", metadata.get("dataset")),
        "dataset_last_refresh": (market_row or {}).get(
            "dataset_last_refresh", metadata.get("dataset_last_refresh")
        ),
        "retrieved_at": (market_row or {}).get("retrieved_at", metadata.get("retrieved_at")),
        "publisher": metadata.get("publisher"),
        "source_url": metadata.get("source_url"),
    }


def _select_fields(row: dict[str, Any] | None, fields: tuple[str, ...]) -> dict[str, Any] | None:
    if row is None:
        return None
    return {field: row[field] for field in fields}


def get_market_context(city: str | None = None, state: str | None = None) -> dict[str, Any]:
    """Return a single source-aware market context for a city or state query."""
    data = load_market_data()
    if city is not None:
        city_result = _resolve_city(city, state, data)
        state_row = city_result.get("state_market")
        support = _get_support_context(city, state, data, city_result=city_result)
        location: dict[str, Any] = {}
        if city_result.get("match_level") == "city_exact":
            location = {
                "city": city_result["city"],
                "state": city_result["state"],
                "state_code": city_result["state_code"],
            }
        elif city_result.get("match_level") == "state_fallback":
            location = {
                "requested_city": city,
                "state": city_result["state"],
                "state_code": city_result["state_code"],
            }
        elif city_result.get("match_level") == "city_ambiguous":
            location = {"requested_city": city, "candidate_states": city_result["candidate_states"]}
        else:
            location = {"requested_city": city}
        return {
            "matched": city_result["matched"],
            "match_level": city_result["match_level"],
            "location": location,
            "city_market": _select_fields(city_result.get("city_market"), CITY_MARKET_FIELDS),
            "state_market": _select_fields(state_row, STATE_MARKET_FIELDS),
            "support": support,
            "source": _source_context(data, state_row or city_result.get("city_market")),
            "limitations": list(LIMITATIONS),
        }

    if state is not None:
        state_result = _resolve_state(state, data)
        state_row = state_result.get("state_market")
        support = _get_support_context(None, state, data, state_result=state_result)
        return {
            "matched": state_result["matched"],
            "match_level": state_result["match_level"],
            "location": (
                {"state": state_result["state"], "state_code": state_result["state_code"]}
                if state_result["matched"] else {"requested_state": state}
            ),
            "city_market": None,
            "state_market": _select_fields(state_row, STATE_MARKET_FIELDS),
            "support": support,
            "source": _source_context(data, state_row),
            "limitations": list(LIMITATIONS),
        }

    return {
        "matched": False,
        "match_level": "location_not_provided",
        "location": {},
        "city_market": None,
        "state_market": None,
        "support": _get_support_context(None, None, data),
        "source": _source_context(data, None),
        "limitations": list(LIMITATIONS),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the read-only SWT market knowledge layer.")
    parser.add_argument("--city", help="Exact city name; case and outer spaces are ignored")
    parser.add_argument("--state", help="Exact state name or two-letter code")
    args = parser.parse_args()
    if args.city is None and args.state is None:
        parser.error("provide --city and/or --state")
    print(json.dumps(get_market_context(args.city, args.state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
