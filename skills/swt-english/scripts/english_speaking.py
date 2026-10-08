#!/usr/bin/env python3
"""Deterministic state rules for the SWT English Speaking Coach."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PRIMARY_MODES = ("ASSESS", "PRACTICE", "MOCK", "RECORDING", "RETRY", "PROGRESS")
SCENARIOS = ("agency", "sponsor", "host_employer", "visa", "workplace")
MAX_FOLLOW_UPS_PER_MAIN_QUESTION = 3
FOLLOW_UP_REASONS = frozenset({"incomplete", "expandable", "fact_conflict", "off_topic", "clarification", "situation_probe"})


def new_mock_session(scenario: str) -> dict[str, Any]:
    if scenario not in SCENARIOS:
        raise ValueError("unsupported interview scenario")
    return {
        "scenario": scenario,
        "state": "ASK_MAIN",
        "main_question_index": 0,
        "follow_up_count": 0,
        "delayed_feedback": True,
        "completed": False,
    }


def advance_mock(session: dict[str, Any], answer_status: str) -> dict[str, Any]:
    """Advance one answer without ever creating FOLLOW_UP_4."""
    current = deepcopy(session)
    if current.get("completed"):
        raise ValueError("mock is already complete")
    count = current.get("follow_up_count")
    if not isinstance(count, int) or not 0 <= count <= MAX_FOLLOW_UPS_PER_MAIN_QUESTION:
        raise ValueError("invalid follow-up count")
    if answer_status == "mock_complete":
        current.update({"state": "ASSESSMENT", "completed": True})
        return current
    if answer_status in FOLLOW_UP_REASONS and count < MAX_FOLLOW_UPS_PER_MAIN_QUESTION:
        count += 1
        current.update({"follow_up_count": count, "state": f"FOLLOW_UP_{count}"})
        return current
    if answer_status not in FOLLOW_UP_REASONS | {"sufficient"}:
        raise ValueError("unsupported answer status")
    current.update({
        "state": "NEXT_MAIN",
        "main_question_index": current.get("main_question_index", 0) + 1,
        "follow_up_count": 0,
    })
    return current


def evidence_capabilities(input_mode: str) -> dict[str, Any]:
    if input_mode not in {"audio", "video", "transcript", "text"}:
        raise ValueError("unsupported input mode")
    has_media = input_mode in {"audio", "video"}
    return {
        "pronunciation": "assessed" if has_media else "not_assessed",
        "audio_fluency": has_media,
        "timestamp_preservation": input_mode in {"audio", "video", "transcript"},
    }
