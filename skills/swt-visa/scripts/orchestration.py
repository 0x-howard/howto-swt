#!/usr/bin/env python3
"""Deterministic contracts for HowTo SWT handoffs and executor state transitions."""

from __future__ import annotations

from typing import Any, Iterable


HANDOFF_VERSION = "1.1"
ROUTER = "swt"
EXECUTOR_STATES = {
    "swt-application": ("INTAKE", "SUBJECT_RESOLVE", "REQUIREMENTS", "MATERIAL_CHECK", "SUBMISSION_STATUS", "BLOCKER", "NEXT_ACTION"),
    "swt-position": ("INTAKE", "NORMALIZE", "LOCATION_RESOLVE", "ANALYZE", "BUDGET", "RISK", "DECISION", "NEXT_ACTION"),
    "swt-english": ("PROFILE", "ASSESS", "PRACTICE", "MOCK", "RECORDING", "RETRY", "PROGRESS", "RESULT", "NEXT_PLAN"),
    "swt-visa": ("INTAKE", "FACT_EXTRACTION", "CONSISTENCY_CHECK", "CONFLICT_OR_MISSING", "RISK", "NEXT_ACTION"),
    "swt-arrival": ("SAFETY_CHECK", "INTAKE", "DEPENDENCY_ORDER", "ACTION", "CONFIRMATION", "NEXT_ACTION"),
}
ROUTING_MODES = frozenset({"DIRECT", "CONFIRM", "CLARIFY"})
REQUIRED_FIELDS = frozenset({
    "handoff_version", "router", "executor", "intent", "user_goal", "known_facts",
    "changed_facts", "missing_critical_facts", "constraints", "execution_cadence",
    "requested_output", "state",
})


def choose_routing_mode(candidate_executors: Iterable[str], missing_route_facts: Iterable[str] = ()) -> str:
    """Return the user interaction mode without trying to classify natural language."""
    candidates = tuple(dict.fromkeys(candidate_executors))
    missing = tuple(dict.fromkeys(missing_route_facts))
    if missing:
        return "CLARIFY"
    if len(candidates) == 1:
        return "DIRECT"
    if 2 <= len(candidates) <= 4:
        return "CONFIRM"
    raise ValueError("routing requires one clear executor or two to four confirmation choices")


def effective_facts(handoff: dict[str, Any]) -> dict[str, Any]:
    """Overlay explicit corrections without mutating the handoff."""
    known = handoff.get("known_facts")
    changed = handoff.get("changed_facts")
    if not isinstance(known, dict) or not isinstance(changed, dict):
        raise ValueError("known_facts and changed_facts must be objects")
    return {**known, **changed}


def validate_handoff(handoff: dict[str, Any]) -> None:
    if not isinstance(handoff, dict) or set(handoff) != REQUIRED_FIELDS:
        raise ValueError("handoff must contain exactly the canonical fields")
    if handoff["handoff_version"] != HANDOFF_VERSION or handoff["router"] != ROUTER:
        raise ValueError("unsupported handoff version or router")
    executor = handoff["executor"]
    if executor not in EXECUTOR_STATES:
        raise ValueError("handoff executor must be one of the five Domain Executors")
    if handoff["state"] not in EXECUTOR_STATES[executor]:
        raise ValueError("state does not belong to the selected executor")
    for field in ("intent", "user_goal", "execution_cadence", "requested_output"):
        if not isinstance(handoff[field], str) or not handoff[field].strip():
            raise ValueError(f"{field} must be a non-empty string")
    facts = effective_facts(handoff)
    for field in ("missing_critical_facts", "constraints"):
        if not isinstance(handoff[field], list) or any(not isinstance(item, str) or not item for item in handoff[field]):
            raise ValueError(f"{field} must be a string list")
    if set(handoff["missing_critical_facts"]) & set(facts):
        raise ValueError("an effective known fact cannot also be requested as missing")


def render_handoff_prompt(handoff: dict[str, Any]) -> str:
    """Render the complete contract without edition-specific promotion."""
    validate_handoff(handoff)
    facts = effective_facts(handoff)
    lines = [
        "HOWTO_SWT_HANDOFF_V1",
        f"使用 Skill：{handoff['executor']}",
        f"模式／意图：{handoff['intent']}",
        f"当前任务：{handoff['user_goal']}",
        "已知事实：" + ("；".join(f"{key}={value}" for key, value in facts.items()) or "无"),
        "本轮修改：" + ("；".join(f"{key}={value}" for key, value in handoff["changed_facts"].items()) or "无"),
        "必要边界：" + ("；".join(handoff["constraints"]) or "无额外边界"),
        f"执行节奏：{handoff['execution_cadence']}",
        f"输出要求：{handoff['requested_output']}",
        f"起始状态：{handoff['state']}",
        f"请使用 {handoff['executor']} 执行。",
        "END_HOWTO_SWT_HANDOFF_V1",
    ]
    return "\n".join(lines)


def validate_transition(executor: str, current: str, next_state: str, *, facts_changed: bool = False) -> None:
    try:
        states = EXECUTOR_STATES[executor]
        current_index = states.index(current)
        next_index = states.index(next_state)
    except (KeyError, ValueError) as error:
        raise ValueError("state transition must stay inside one Executor") from error
    if next_index < current_index and not facts_changed:
        raise ValueError("backward transitions require changed facts that invalidate prior work")
