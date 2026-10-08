#!/usr/bin/env python3
"""Host-neutral Interaction Request validation, adaptation, and fallback rendering."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


VERSION = "1.0"
TYPES = frozenset({"single_choice", "multi_choice", "free_text", "structured_form", "confirmation"})
CAPABILITIES = (
    "supports_single_choice", "supports_multi_choice", "supports_free_text",
    "supports_structured_form", "supports_confirmation",
)
CAPABILITY_BY_TYPE = {
    "single_choice": "supports_single_choice", "multi_choice": "supports_multi_choice",
    "free_text": "supports_free_text", "structured_form": "supports_structured_form",
    "confirmation": "supports_confirmation",
}


def validate_capabilities(capabilities: dict[str, Any]) -> None:
    required = {"host", "native_interface", *CAPABILITIES}
    if not isinstance(capabilities, dict) or set(capabilities) != required:
        raise ValueError("host capabilities must contain exactly the canonical fields")
    if not isinstance(capabilities["host"], str) or not capabilities["host"]:
        raise ValueError("host capability requires a name")
    if capabilities["native_interface"] is not None and not isinstance(capabilities["native_interface"], str):
        raise ValueError("native_interface must be text or null")
    if any(not isinstance(capabilities[key], bool) for key in CAPABILITIES):
        raise ValueError("host capability flags must be booleans")


def validate_request(request: dict[str, Any]) -> None:
    required = {
        "interaction_version", "type", "id", "question", "options", "fields", "min_selections",
        "max_selections", "allow_other", "recommended_option_id", "recommendation_basis",
        "sensitive_confirmation",
    }
    if not isinstance(request, dict) or set(request) != required:
        raise ValueError("Interaction Request must contain exactly the canonical fields")
    if request["interaction_version"] != VERSION or request["type"] not in TYPES:
        raise ValueError("unsupported interaction version or type")
    if not isinstance(request["id"], str) or not request["id"] or not isinstance(request["question"], str) or not request["question"]:
        raise ValueError("interaction id and question must be nonempty text")
    if not isinstance(request["allow_other"], bool) or not isinstance(request["sensitive_confirmation"], bool):
        raise ValueError("interaction flags must be booleans")
    options = request["options"]
    choice = request["type"] in {"single_choice", "multi_choice", "confirmation"}
    if not isinstance(options, list) or (choice and len(options) < 2):
        raise ValueError("choice interactions require at least two options")
    ids = []
    for option in options:
        if not isinstance(option, dict) or set(option) != {"id", "label", "description"}:
            raise ValueError("options require id, label, and description")
        if any(not isinstance(option[key], str) or not option[key] for key in option):
            raise ValueError("option values must be nonempty text")
        ids.append(option["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("option IDs must be unique")
    fields = request["fields"]
    if not isinstance(fields, list):
        raise ValueError("fields must be a list")
    for field in fields:
        if not isinstance(field, dict) or set(field) != {"id", "label", "required"}:
            raise ValueError("form fields require id, label, and required")
        if not isinstance(field["id"], str) or not field["id"] or not isinstance(field["label"], str) or not field["label"] or not isinstance(field["required"], bool):
            raise ValueError("invalid form field")
    if request["type"] == "structured_form" and not fields:
        raise ValueError("structured form requires at least one field")
    minimum, maximum = request["min_selections"], request["max_selections"]
    if not isinstance(minimum, int) or not isinstance(maximum, int) or minimum < 0 or maximum < minimum:
        raise ValueError("invalid selection bounds")
    if request["type"] in {"single_choice", "confirmation"} and (minimum, maximum) != (1, 1):
        raise ValueError("single choice and confirmation require one selection")
    if choice and maximum > len(options):
        raise ValueError("selection maximum exceeds options")
    if len(options) > 4 and request["id"] != "offer_roi_selection":
        raise ValueError("more than four options require grouping/paging; only Offer ROI selection is exempt")
    recommended = request["recommended_option_id"]
    basis = request["recommendation_basis"]
    if recommended is not None and (recommended not in ids or not isinstance(basis, str) or not basis.strip()):
        raise ValueError("recommended option requires a valid option and evidence basis")
    if recommended is None and basis is not None:
        raise ValueError("recommendation basis requires a recommended option")


def interaction_request(kind: str, identifier: str, question: str, *, options: list[dict[str, str]] | None = None,
                        fields: list[dict[str, Any]] | None = None,
                        min_selections: int = 0, max_selections: int = 0, allow_other: bool = False,
                        recommended_option_id: str | None = None, recommendation_basis: str | None = None,
                        sensitive_confirmation: bool = False) -> dict[str, Any]:
    request = {
        "interaction_version": VERSION, "type": kind, "id": identifier, "question": question,
        "options": options or [], "fields": fields or [], "min_selections": min_selections, "max_selections": max_selections,
        "allow_other": allow_other, "recommended_option_id": recommended_option_id,
        "recommendation_basis": recommendation_basis, "sensitive_confirmation": sensitive_confirmation,
    }
    validate_request(request)
    return request


def plan_interaction(routing_mode: str, missing_kind: str | None, request: dict[str, Any] | None,
                     *, fact_key: str | None = None, confirmed_context_keys: list[str] | None = None) -> dict[str, Any]:
    known = set(confirmed_context_keys or [])
    if routing_mode == "DIRECT" or (fact_key is not None and fact_key in known):
        return {"action": "direct", "request": None}
    if routing_mode == "CONFIRM":
        if request is None or request["type"] not in {"single_choice", "multi_choice", "confirmation"}:
            raise ValueError("CONFIRM requires a finite choice or confirmation request")
    elif routing_mode == "CLARIFY":
        expected = {"enum": {"single_choice", "multi_choice"}, "free_text": {"free_text", "structured_form"}}
        if missing_kind not in expected or request is None or request["type"] not in expected[missing_kind]:
            raise ValueError("CLARIFY request does not match the missing fact type")
    else:
        raise ValueError("routing mode must be DIRECT, CONFIRM, or CLARIFY")
    validate_request(request)
    return {"action": "interact", "request": deepcopy(request)}


def render_fallback(request: dict[str, Any]) -> str:
    validate_request(request)
    lines = [request["question"], ""]
    if request["type"] in {"single_choice", "multi_choice", "confirmation"}:
        for index, option in enumerate(request["options"], 1):
            marker = "（推荐）" if option["id"] == request["recommended_option_id"] else ""
            lines.append(f"{index}. {option['label']}{marker}")
        if request["allow_other"]:
            lines.append(f"{len(request['options']) + 1}. 其他")
        if request["type"] == "multi_choice":
            lines.extend(["", f"最多选择 {request['max_selections']} 个；回复编号并用逗号分隔，例如：1,2,4。"])
        else:
            lines.extend(["", "回复数字即可。"])
    elif request["type"] == "structured_form":
        lines.append("请按字段填写；当前宿主不支持原生表单时，可用一条文本逐项回答。")
    else:
        lines.append("请直接填写这一事实。")
    return "\n".join(lines)


def adapt_request(request: dict[str, Any], capabilities: dict[str, Any]) -> dict[str, Any]:
    validate_request(request)
    validate_capabilities(capabilities)
    capability = CAPABILITY_BY_TYPE[request["type"]]
    if capabilities[capability] and capabilities["native_interface"]:
        return {"delivery": "native", "host": capabilities["host"], "interface": capabilities["native_interface"], "request": deepcopy(request)}
    return {"delivery": "text_fallback", "host": capabilities["host"], "interface": None, "text": render_fallback(request)}


def validate_selection(request: dict[str, Any], selected_ids: list[str] | None = None, *, other_text: str | None = None,
                       cancelled: bool = False) -> dict[str, Any]:
    validate_request(request)
    if cancelled:
        return {"status": "cancelled", "selected_ids": []}
    selected = selected_ids or []
    valid = {option["id"] for option in request["options"]}
    if other_text is not None:
        if not request["allow_other"] or not other_text.strip():
            raise ValueError("other text is not allowed or is empty")
        return {"status": "accepted_other", "selected_ids": [], "other_text": other_text.strip()}
    if any(item not in valid for item in selected) or len(selected) != len(set(selected)):
        raise ValueError("invalid selection")
    if not request["min_selections"] <= len(selected) <= request["max_selections"]:
        raise ValueError("selection count is outside allowed bounds")
    return {"status": "accepted", "selected_ids": selected}


def offer_selection_request(functions: list[dict[str, Any]]) -> dict[str, Any]:
    return interaction_request(
        "multi_choice", "offer_roi_selection", "请选择最多 3 个岗位进一步画收益曲线。",
        options=[{"id": item["id"], "label": item["label"], "description": f"期望周净结余 ${item['expected_weekly_net_surplus_usd']}"} for item in functions],
        min_selections=1, max_selections=min(3, len(functions)), allow_other=False,
    )
