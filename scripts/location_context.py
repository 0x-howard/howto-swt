#!/usr/bin/env python3
"""Combine the existing state-context profiles with SWT market data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import state_context as state_context_api
import swt_market


LIMITATIONS = [
    "missing state_context means unavailable data, not negative evidence",
    "missing swt_market means unavailable map evidence, not zero SWT activity",
    "participant count is BridgeUSA SWT Map participant count",
    "participant count is not verified as deduplicated annual participants",
    "market rankings are dataset-relative",
    "regional support-group evidence does not imply city-level support",
    "state_context is state-level background and does not establish city-level conditions",
]


def _clean_input(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _resolve_state_identity(query: str) -> dict[str, Any] | None:
    """Resolve only an exact state name or code across either data layer."""
    market_result = swt_market.resolve_state(query)
    if market_result["matched"]:
        return {
            "state": market_result["state"],
            "state_code": market_result["state_code"],
            "identity_source": "swt_market_state_index",
        }

    normalized = query.strip().casefold()
    for code, name in state_context_api.CODE_TO_NAME.items():
        if normalized not in {code.casefold(), name.casefold()}:
            continue
        # Reuse the established resolver with its canonical explicit state
        # value. The direct comparison above prevents place-index matches or
        # approximate spellings from being mistaken for a state argument.
        context_result = state_context_api.resolve_state(name)
        if context_result is not None and context_result.code == code:
            return {
                "state": context_result.name,
                "state_code": context_result.code,
                "identity_source": "state_context_state_resolver",
            }
    return None


def _state_index_city(city: str) -> Any | None:
    """Use only an explicit place entry from the existing state index."""
    result = state_context_api.resolve_state(city)
    if result is not None and result.source == "state_index":
        return result
    return None


def _location_result(
    matched: bool,
    match_level: str,
    location: dict[str, Any],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "matched": matched,
        "match_level": match_level,
        "location": location,
        **extra,
    }


def resolve_location(city: str | None = None, state: str | None = None) -> dict[str, Any]:
    """Resolve location identity without guessing or evaluating the location."""
    city = _clean_input(city)
    state = _clean_input(state)

    if state is not None:
        identity = _resolve_state_identity(state)
        if identity is None:
            location = {"requested_state": state}
            if city is not None:
                location["requested_city"] = city
            return _location_result(False, "state_not_found", location)

        state_name = identity["state"]
        state_code = identity["state_code"]
        if city is None:
            return _location_result(
                True,
                "state_exact",
                {"state": state_name, "state_code": state_code},
                state_identity_source=identity["identity_source"],
            )

        market_result = swt_market.resolve_city(city, state_code)
        if market_result["match_level"] == "city_exact":
            return _location_result(
                True,
                "city_exact",
                {
                    "city": market_result["city"],
                    "state": state_name,
                    "state_code": state_code,
                },
                city_found=True,
                state_identity_source=identity["identity_source"],
                city_identity_source="swt_market_city_index",
            )

        # The existing state-context index can identify a small set of
        # explicitly listed locations that may not have a market city row.
        place_result = _state_index_city(city)
        if place_result is not None and place_result.code == state_code:
            return _location_result(
                True,
                "city_exact",
                {"city": city, "state": state_name, "state_code": state_code},
                city_found=True,
                state_identity_source=identity["identity_source"],
                city_identity_source="state_context_index",
            )

        return _location_result(
            True,
            "state_fallback",
            {"requested_city": city, "state": state_name, "state_code": state_code},
            city_found=False,
            state_identity_source=identity["identity_source"],
        )

    if city is None:
        return _location_result(False, "location_not_provided", {})

    market_result = swt_market.resolve_city(city)
    if market_result["match_level"] == "city_exact":
        return _location_result(
            True,
            "city_exact",
            {
                "city": market_result["city"],
                "state": market_result["state"],
                "state_code": market_result["state_code"],
            },
            city_found=True,
            city_identity_source="swt_market_city_index",
        )
    if market_result["match_level"] == "city_ambiguous":
        return _location_result(
            False,
            "city_ambiguous",
            {"requested_city": city},
            candidate_states=market_result["candidate_states"],
        )

    place_result = _state_index_city(city)
    if place_result is not None:
        return _location_result(
            True,
            "city_exact",
            {"city": city, "state": place_result.name, "state_code": place_result.code},
            city_found=True,
            city_identity_source="state_context_index",
        )

    return _location_result(False, "city_not_found", {"requested_city": city})


def _load_state_context(state_code: str) -> dict[str, str] | None:
    profile_file = state_context_api.profile_path(state_code)
    if not profile_file.is_file():
        return None
    return state_context_api.load_state_profile(state_code)


def get_location_context(city: str | None = None, state: str | None = None) -> dict[str, Any]:
    """Resolve identity first, then attach only available state and market data."""
    resolved = resolve_location(city, state)
    result: dict[str, Any] = dict(resolved)
    location = resolved["location"]
    state_code = location.get("state_code")

    state_context = _load_state_context(state_code) if state_code else None
    market_context = None
    if state_code:
        requested_city = location.get("city") or location.get("requested_city")
        market_candidate = swt_market.get_market_context(
            city=requested_city,
            state=state_code,
        ) if requested_city else swt_market.get_market_context(state=state_code)
        if market_candidate.get("state_market") is not None:
            market_context = {
                "city_market": market_candidate.get("city_market"),
                "state_market": market_candidate.get("state_market"),
                "support": market_candidate.get("support"),
                "source": market_candidate.get("source"),
            }

    result.update({
        "availability": {
            "state_context": state_context is not None,
            "swt_market": market_context is not None,
        },
        "state_context": state_context,
        "swt_market": market_context,
        "limitations": list(LIMITATIONS),
    })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve state and SWT market context for a location.")
    parser.add_argument("--city", help="Exact city or indexed location")
    parser.add_argument("--state", help="Exact state name or two-letter code")
    args = parser.parse_args()
    if _clean_input(args.city) is None and _clean_input(args.state) is None:
        parser.error("provide --city and/or --state")
    print(json.dumps(get_location_context(args.city, args.state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
