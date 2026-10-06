#!/usr/bin/env python3
"""Validate optional internal decision records against the canonical finite model."""

from __future__ import annotations

from typing import Any

INTENTS = frozenset({
    "NAVIGATION", "DOCUMENT_CHECK", "DECISION", "INTERVIEW", "ENGLISH_PRACTICE",
    "GENERAL_ENGLISH", "ENGLISH_ASSESSMENT", "FORM_FILLING", "CONFLICT",
    "CALCULATION", "EMERGENCY", "GENERAL_QA",
})
SKILLS = frozenset({"swt", "swt-application", "swt-position", "swt-english", "swt-visa", "swt-arrival"})
INTENT_ROUTES = {
    "NAVIGATION": frozenset({"swt"}),
    "DOCUMENT_CHECK": SKILLS,
    "DECISION": frozenset({"swt", "swt-application", "swt-position"}),
    "INTERVIEW": frozenset({"swt-english"}),
    "ENGLISH_PRACTICE": frozenset({"swt-english"}),
    "GENERAL_ENGLISH": frozenset({"swt-english"}),
    "ENGLISH_ASSESSMENT": frozenset({"swt-english"}),
    "FORM_FILLING": frozenset({"swt-application", "swt-visa", "swt-arrival"}),
    "CONFLICT": SKILLS,
    "CALCULATION": frozenset({"swt-position"}),
    "EMERGENCY": frozenset({"swt", "swt-arrival"}),
    "GENERAL_QA": frozenset({"swt"}),
}
STAGES = frozenset(f"{i:02d}" for i in range(12))
CONFIDENCE = frozenset({"high", "medium", "low"})
RISK = frozenset({"green", "yellow", "red", "emergency"})
EVIDENCE = frozenset({"confirmed", "conditional", "pending_verification", "conflicting", "historical"})
MATERIALITY = frozenset({"non_material", "material", "critical"})
MISSING = frozenset({"none", "low_impact", "conclusion_changes", "safety_blocking"})
NEXT = frozenset({
    "answer", "ask_one_question", "calculate", "load_known_context", "route_specialist",
    "verify_fact", "pause_action", "start_assessment", "start_practice", "start_interview", "finish",
})
REASONS = frozenset({
    "direct_answer", "context_needed", "route_by_object", "risk_pause", "fact_conflict",
    "calculation_needed", "assessment_requested", "practice_requested", "roleplay_requested",
    "stage_unknown", "other",
})
FIELDS = frozenset({
    "intent", "route", "supporting_route", "stage", "confidence", "risk", "evidence_status",
    "materiality", "missing_information", "clarification_level", "known_context_keys", "next_action", "reason_code",
    "missing_information_keys",
})

CLARIFICATION_LEVELS = {"none": 1, "low_impact": 2, "conclusion_changes": 3, "safety_blocking": 4}


def clarification_level_for(missing_information: str) -> int:
    """Map the new decision classification onto the existing protocol Levels 1–4."""
    try:
        return CLARIFICATION_LEVELS[missing_information]
    except KeyError as error:
        raise ValueError(f"invalid missing_information: {missing_information!r}") from error


def validate_decision(record: dict[str, Any]) -> None:
    """Raise ValueError for unknown values or inconsistent safety decisions."""
    if not isinstance(record, dict) or set(record) - FIELDS:
        raise ValueError("decision must be an object with only canonical fields")
    required = {"intent", "route", "confidence", "risk", "evidence_status", "materiality", "missing_information", "next_action", "reason_code"}
    if not required.issubset(record):
        raise ValueError(f"missing required decision fields: {sorted(required - set(record))}")
    choices = {
        "intent": INTENTS, "route": SKILLS, "confidence": CONFIDENCE, "risk": RISK,
        "evidence_status": EVIDENCE, "materiality": MATERIALITY,
        "missing_information": MISSING, "next_action": NEXT, "reason_code": REASONS,
    }
    for field, accepted in choices.items():
        if record[field] not in accepted:
            raise ValueError(f"invalid {field}: {record[field]!r}")
    if record["route"] not in INTENT_ROUTES[record["intent"]]:
        raise ValueError(f"route {record['route']!r} is inconsistent with intent {record['intent']!r}")
    supporting = record.get("supporting_route")
    if supporting is not None and supporting not in SKILLS:
        raise ValueError(f"invalid supporting_route: {supporting!r}")
    stage = record.get("stage")
    if stage is not None and stage not in STAGES:
        raise ValueError(f"invalid stage: {stage!r}")
    clarification = record.get("clarification_level")
    if clarification is not None and clarification not in {1, 2, 3, 4}:
        raise ValueError("clarification_level must be null or 1 through 4")
    expected_level = clarification_level_for(record["missing_information"])
    if clarification is not None and clarification != expected_level:
        raise ValueError("clarification_level conflicts with missing_information mapping")
    known = record.get("known_context_keys", [])
    if not isinstance(known, list) or any(not isinstance(item, str) or len(item) > 80 for item in known):
        raise ValueError("known_context_keys must be a short string list")
    missing_keys = record.get("missing_information_keys", [])
    if not isinstance(missing_keys, list) or any(not isinstance(item, str) or len(item) > 80 for item in missing_keys):
        raise ValueError("missing_information_keys must be a short string list")
    if set(known) & set(missing_keys):
        raise ValueError("known context cannot be requested again as missing information")
    if record["next_action"] == "ask_one_question" and record["missing_information"] == "none":
        raise ValueError("do not ask when no material information is missing")
    if record["missing_information"] == "safety_blocking" and record["next_action"] not in {"verify_fact", "pause_action", "route_specialist"}:
        raise ValueError("safety-blocking missing information requires verification, pause, or specialist routing")
    if record["evidence_status"] == "conflicting" and record["materiality"] == "critical":
        if record["next_action"] not in {"verify_fact", "pause_action"}:
            raise ValueError("critical fact conflict must be verified or paused")
    if record["risk"] in {"red", "emergency"} and record["materiality"] == "critical":
        if record["next_action"] not in {"verify_fact", "pause_action", "route_specialist"}:
            raise ValueError("critical red/emergency decision cannot continue as an ordinary answer")
    if record["intent"] == "ENGLISH_ASSESSMENT" and record["next_action"] not in {"start_assessment", "ask_one_question", "route_specialist", "pause_action"}:
        raise ValueError("assessment intent must stay on the assessment path")
    if record["intent"] == "ENGLISH_PRACTICE" and record["next_action"] not in {"start_practice", "ask_one_question", "route_specialist", "verify_fact", "pause_action"}:
        raise ValueError("practice intent must stay on the practice path")
