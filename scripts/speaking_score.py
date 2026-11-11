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


SCENES = {
    "agency_generic": "机构面试",
    "sponsor_generic": "Sponsor 面试",
    "host_generic": "雇主面试",
    "visa_interview_generic": "签证面试",
    "comprehensive": "综合",
}
CRITERION_NAMES = {
    "comprehension_relevance": "理解与切题",
    "fluency_coherence": "流利与连贯",
    "vocabulary": "词汇表达",
    "grammar": "语法控制",
    "pronunciation_intelligibility": "发音可理解度",
    "interaction_repair": "互动与修复",
    "task_communication": "任务沟通",
}
MODE_INTRO = {
    "transcript": "你用的是语音输入，我按转写文字评估，发音不打分；",
    "text": "当前为文字模拟，不能代表完整口语表现；",
    "voice": "",
}
MODE_LIMIT = {
    "transcript": "按语音转写评估，发音未测；语音识别错误不计入。",
    "text": "当前为文字模拟，不能代表完整口语表现；发音和口头互动未测。",
    "voice": "",
}
NEXT_CHOICES = "接下来想看什么？A. 逐题评分　B. 七维详情　C. 错误示例　D. 再测一次"


def opening_question() -> str:
    return "\n".join([
        "这次想按哪种面试来测？", "",
        "A. 机构面试", "B. Sponsor 面试", "C. 雇主面试", "D. 签证面试", "E. 综合测评（一次覆盖以上四种）", "",
        "回复字母即可。",
    ])


def start_line(profile: str, input_mode: str) -> str:
    if profile not in SCENES or input_mode not in MODES:
        raise ValueError("unknown profile or input_mode")
    scene = "综合口语测评" if profile == "comprehensive" else f"{SCENES[profile]}口语测试"
    return f"好的，我们做一次{_gap(scene)}{scene}。{MODE_INTRO[input_mode]}中间不纠错，结束后统一反馈。"


def _gap(text: str) -> str:
    return " " if text[:1].isascii() else ""


def _readiness_label(profile: str, position: str | None) -> str:
    label = f"{SCENES[profile]}准备度"
    return f"{label}（{position}）" if profile == "host_generic" and position else label


def _scores(criteria: dict[str, Any], included: list[str]) -> dict[str, float]:
    return {key: _parse_criterion(criteria[key], key)[0] for key in included}


def _join(names: list[str]) -> str:
    return names[0] if len(names) == 1 else "、".join(names[:-1]) + "和" + names[-1]


def _weakness_lines(scores: dict[str, float], weights: dict[str, int], notes: dict[str, str]) -> tuple[list[str], list[str]]:
    if not scores:
        return [], []
    top = max(scores.values())
    weak = sorted((key for key, value in scores.items() if value < top), key=lambda key: (scores[key], -weights[key]))[:3]
    lines = [f"- **{CRITERION_NAMES[key]}**：{notes.get(key) or f'{_number(scores[key])} / 10'}" for key in weak]
    return weak, lines


def _number(value: float) -> str:
    return f"{Decimal(str(value)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}"


def _limitations(result: dict[str, Any], input_mode: str) -> list[str]:
    lines = [MODE_LIMIT[input_mode]] if MODE_LIMIT[input_mode] else []
    thin = [CRITERION_NAMES[key] for key, reason in result["missing_criteria"].items()
            if reason == "missing" or reason == "unavailable" or reason.startswith("undersampled")]
    if thin:
        lines.append(f"{'、'.join(thin)}样本不足，未计入准备度。")
    return lines


def _ielts_row(data: dict[str, Any], complete: bool) -> list[str]:
    value = data.get("ielts_style")
    if value is None:
        return []
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 1 <= value <= 9:
        raise ValueError("ielts_style must be a number from 1 to 9")
    return [f"| IELTS 风格估计 | ≈ {value:.1f} / 9 |" if complete else f"| IELTS 风格部分估计 | ≈ {value:.1f} / 9（不含发音） |"]


def format_result(data: dict[str, Any]) -> str:
    """Student-facing first result: conclusion, score table, up to three weaknesses, limits, choices."""
    profile = data.get("profile")
    input_mode = data.get("input_mode", "text")
    criteria = data.get("criteria", {})
    notes = data.get("notes", {})
    position = data.get("target_position")
    if not isinstance(criteria, dict) or not isinstance(notes, dict):
        raise ValueError("criteria and notes must be objects keyed by criterion")
    if set(notes) - set(CRITERION_NAMES):
        raise ValueError("unknown criterion key(s) in notes")
    weights_all = load_profile_weights()
    if profile == "comprehensive":
        results = calculate_comprehensive(criteria, input_mode)["profiles"]
        scored = {name: result for name, result in results.items() if result["target_readiness"] is not None}
        if not scored:
            return "**样本不足，暂时无法给出准备度。**\n\n" + NEXT_CHOICES
        best = max(scored, key=lambda name: scored[name]["target_readiness"])
        worst = min(scored, key=lambda name: scored[name]["target_readiness"])
        partial = any(result["readiness_status"] == "partial" for result in scored.values())
        lines = [f"**综合测评{'（部分测评）' if partial else ''}：{SCENES[best]}准备度最高（{_number(scored[best]['target_readiness'])} / 10），"
                 f"{SCENES[worst]}最低（{_number(scored[worst]['target_readiness'])} / 10）。**", "",
                 "| 场景 | 准备度 |", "|---|---:|"]
        lines += [f"| {_readiness_label(name, position)} | "
                  + (f"{_number(result['target_readiness'])} / 10" if result["target_readiness"] is not None else "样本不足") + " |"
                  for name, result in results.items()]
        lines += _ielts_row(data, not partial and input_mode == "voice")
        included = scored[best]["included_criteria"]
        scores = _scores(criteria, included)
        if best != worst and scores:
            gap = max(included, key=lambda key: (weights_all[worst][key] - weights_all[best][key]) * (10 - scores[key]))
            if weights_all[worst][gap] > weights_all[best][gap]:
                lines += ["", f"{SCENES[worst]}更看重{CRITERION_NAMES[gap]}，这是两者相差最大的原因。"]
        _, weak = _weakness_lines(scores, weights_all[best], notes)
        reference = scored[best]
    else:
        if profile not in PROFILES:
            raise ValueError(f"profile must be one of: {', '.join((*PROFILES, 'comprehensive'))}")
        reference = calculate_readiness(criteria, profile, input_mode)
        scores = _scores(criteria, reference["included_criteria"])
        if reference["target_readiness"] is None:
            return "**样本不足，暂时无法给出准备度。**\n\n" + NEXT_CHOICES
        weak_keys, weak = _weakness_lines(scores, weights_all[profile], notes)
        partial = reference["readiness_status"] == "partial"
        strong = [CRITERION_NAMES[key] for key, value in scores.items() if value == max(scores.values())]
        tail = f"：{_join(strong)}较好" + (f"，主要短板是{_join([CRITERION_NAMES[key] for key in weak_keys[:2]])}" if weak_keys else "")
        lines = [f"**按{_gap(SCENES[profile])}{SCENES[profile]}的要求，你目前的准备度约 {_number(reference['target_readiness'])} / 10"
                 f"{'（部分测评）' if partial else ''}{tail}。**", "",
                 "| 结果 | 分数 |", "|---|---:|",
                 f"| {_readiness_label(profile, position)} | {_number(reference['target_readiness'])} / 10{'（部分测评）' if partial else ''} |"]
        lines += _ielts_row(data, not partial)
    if weak:
        lines += ["", *weak]
    limits = _limitations(reference, input_mode)
    if limits:
        lines += ["", *limits]
    lines += ["", NEXT_CHOICES]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=(*PROFILES, "comprehensive"))
    parser.add_argument("--input", default="-", help="JSON file, or - to read JSON from stdin")
    parser.add_argument("--format", action="store_true", help="print the student-facing first result")
    parser.add_argument("--opening", action="store_true", help="print the fixed scene question")
    parser.add_argument("--start", choices=sorted(MODES), help="print the opening line for this input mode")
    args = parser.parse_args()
    if args.opening:
        print(opening_question())
        return 0
    if args.profile is None:
        raise ValueError("--profile is required")
    if args.start:
        print(start_line(args.profile, args.start))
        return 0
    raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("assessment input JSON must be an object")
    criteria = data.get("criteria", {})
    input_mode = data.get("input_mode", "text")
    if not isinstance(criteria, dict):
        raise ValueError("criteria must be an object keyed by criterion")
    if args.format:
        print(format_result({**data, "profile": args.profile}))
        return 0
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
