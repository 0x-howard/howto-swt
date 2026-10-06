#!/usr/bin/env python3
"""Deterministically calculate SWT English profile readiness from scored criteria."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROFILE_REFERENCE = ROOT / "references" / "english-profiles.md"
RUBRIC_REFERENCE = ROOT / "references" / "english-rubric.md"
PROFILES = (
    "agency_generic",
    "sponsor_generic",
    "host_generic",
    "visa_interview_generic",
)
MODES = {"voice", "transcript", "text"}
CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}


def _cells(line: str) -> list[str]:
    return [cell.strip().strip("*").strip("`") for cell in line.strip().strip("|").split("|")]


def _table_rows(path: Path, header_match) -> tuple[list[str], list[list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        headers = _cells(line)
        if header_match(headers):
            rows: list[list[str]] = []
            for candidate in lines[index + 2 :]:
                if not candidate.strip().startswith("|"):
                    break
                rows.append(_cells(candidate))
            return headers, rows
    raise ValueError(f"required table not found in {path.name}")


def load_profile_weights() -> dict[str, dict[str, int]]:
    """Read profile weights from their canonical Markdown table."""
    headers, rows = _table_rows(
        PROFILE_REFERENCE,
        lambda cells: len(cells) >= 6 and cells[0] == "Criterion" and cells[1] == "Criterion key",
    )
    profile_columns = {name: headers.index(name) for name in PROFILES if name in headers}
    if set(profile_columns) != set(PROFILES):
        raise ValueError("english-profiles.md must define all four generic profiles")
    weights = {profile: {} for profile in PROFILES}
    for row in rows:
        if len(row) < len(headers):
            continue
        key = row[1]
        if not re.fullmatch(r"[a-z_]+", key):
            continue
        for profile, column in profile_columns.items():
            weights[profile][key] = int(row[column])
    expected_keys = {
        "comprehension_relevance", "fluency_coherence", "vocabulary", "grammar",
        "pronunciation_intelligibility", "interaction_repair", "task_communication",
    }
    for profile, profile_weights in weights.items():
        if set(profile_weights) != expected_keys or sum(profile_weights.values()) != 100:
            raise ValueError(f"invalid weights for {profile} in english-profiles.md")
    return weights


def load_minimum_evidence() -> dict[str, int]:
    """Read evidence thresholds from the rubric's canonical table."""
    _, rows = _table_rows(
        RUBRIC_REFERENCE,
        lambda cells: len(cells) >= 3 and cells[0] == "Criterion key" and cells[1].startswith("Minimum ") and "evidence_count" in cells[1],
    )
    thresholds: dict[str, int] = {}
    for row in rows:
        if len(row) >= 3 and re.fullmatch(r"[a-z_]+", row[0]):
            thresholds[row[0]] = int(row[1])
    if len(thresholds) != 7:
        raise ValueError("english-rubric.md must define minimum evidence for all seven criteria")
    return thresholds


def _parse_criterion(value: Any, key: str) -> tuple[float | None, str, int]:
    if isinstance(value, dict):
        raw_score = value.get("score")
        confidence = value.get("confidence", "low")
        evidence_count = value.get("evidence_count", 0)
    else:
        raw_score = value
        confidence = "low"
        evidence_count = 0

    if raw_score is None or (isinstance(raw_score, str) and raw_score.lower() == "unavailable"):
        score = None
    else:
        if isinstance(raw_score, bool):
            raise ValueError(f"{key}.score must be a number from 1 to 10 or null")
        try:
            score = float(raw_score)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{key}.score must be a number from 1 to 10 or null") from error
        if not math.isfinite(score) or not 1 <= score <= 10:
            raise ValueError(f"{key}.score must be between 1 and 10")

    if not isinstance(confidence, str) or confidence not in CONFIDENCE_ORDER:
        raise ValueError(f"{key}.confidence must be low, medium, or high")
    if isinstance(evidence_count, bool) or not isinstance(evidence_count, int) or evidence_count < 0:
        raise ValueError(f"{key}.evidence_count must be a non-negative integer")
    return score, confidence, evidence_count


def calculate_readiness(
    criteria: dict[str, Any], profile: str, input_mode: str = "text"
) -> dict[str, Any]:
    """Return a one-decimal weighted score plus explicit evidence coverage/status."""
    if profile not in PROFILES:
        raise ValueError(f"profile must be one of: {', '.join(PROFILES)}")
    if input_mode not in MODES:
        raise ValueError(f"input_mode must be one of: {', '.join(sorted(MODES))}")

    weights = load_profile_weights()[profile]
    thresholds = load_minimum_evidence()
    unknown = set(criteria) - set(weights)
    if unknown:
        raise ValueError("unknown criterion key(s): " + ", ".join(sorted(unknown)))

    contribution = Decimal("0")
    covered_weight = 0
    included_confidences: list[str] = []
    reasons: dict[str, str] = {}
    included: list[str] = []
    for key, weight in weights.items():
        if key == "interaction_repair" and input_mode == "text":
            if key in criteria:
                score, _, _ = _parse_criterion(criteria[key], key)
                if score is not None:
                    raise ValueError(f"{key} cannot be scored as spoken interaction from text input")
            reasons[key] = "spoken_interaction_unavailable"
            continue
        if key == "pronunciation_intelligibility" and input_mode != "voice":
            if key in criteria:
                score, _, _ = _parse_criterion(criteria[key], key)
                if score is not None:
                    raise ValueError(f"{key} cannot be scored from {input_mode} input")
            reasons[key] = "audio_required"
            continue
        if key not in criteria:
            reasons[key] = "missing"
            continue
        score, confidence, evidence_count = _parse_criterion(criteria[key], key)
        if score is None:
            reasons[key] = "unavailable"
            continue
        if evidence_count < thresholds[key]:
            reasons[key] = f"undersampled:{evidence_count}/{thresholds[key]}"
            continue
        included.append(key)
        included_confidences.append(confidence)
        covered_weight += weight
        contribution += Decimal(str(score)) * Decimal(weight)

    readiness = None
    if covered_weight:
        readiness = float(
            (contribution / Decimal(covered_weight)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        )
    complete = input_mode == "voice" and not reasons and len(included) == 7
    confidence = "low"
    if included_confidences:
        confidence = min(included_confidences, key=CONFIDENCE_ORDER.__getitem__)

    return {
        "profile": profile,
        "input_mode": input_mode,
        "target_readiness": readiness,
        "readiness_status": "complete" if complete else "partial",
        "weight_coverage_pct": covered_weight,
        "confidence": confidence,
        "included_criteria": included,
        "missing_criteria": reasons,
    }


def calculate_comprehensive(criteria: dict[str, Any], input_mode: str = "text") -> dict[str, Any]:
    """Map one evidence set through all four profiles without retesting."""
    return {
        "profile": "comprehensive",
        "input_mode": input_mode,
        "profiles": {
            profile: calculate_readiness(criteria, profile, input_mode)
            for profile in PROFILES
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, choices=(*PROFILES, "comprehensive"))
    parser.add_argument("--input", default="-", help="JSON file, or - to read JSON from stdin")
    args = parser.parse_args()
    raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("assessment input JSON must be an object")
    criteria = data.get("criteria", {})
    input_mode = data.get("input_mode", "text")
    if not isinstance(criteria, dict):
        raise ValueError("criteria must be an object keyed by criterion")
    if args.profile == "comprehensive":
        result = calculate_comprehensive(criteria, input_mode)
    else:
        result = calculate_readiness(criteria, args.profile, input_mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2) from error
