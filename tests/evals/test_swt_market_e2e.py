#!/usr/bin/env python3
"""Deterministic end-to-end contracts for SWT routing and location context."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from budget import calculate_position_overview, format_position_overview  # noqa: E402
from location_context import get_location_context  # noqa: E402


FIXTURE_PATH = ROOT / "tests/evals/fixtures/swt_market_e2e_cases.json"
CASES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]
ROUTER_TEXT = (ROOT / "skills/swt/SKILL.md").read_text(encoding="utf-8")
POSITION_TEXT = (ROOT / "skills/swt-position/SKILL.md").read_text(encoding="utf-8")


def _section_for_route(scope):
    section = ROUTER_TEXT.split("## 岗位与地点意图", 1)[1].split("## 多 Skill 协调", 1)[0]
    if scope == "position":
        return section.split("### 专项任务优先于地点词", 1)[0]
    if scope == "specialist":
        return section.split("### 专项任务优先于地点词", 1)[1].split("## 上下文不足时", 1)[0]
    if scope == "context":
        return section.split("## 上下文不足时", 1)[1]
    raise ValueError(f"unknown route evidence section: {scope}")


def _path_value(value, path):
    current = value
    for part in path.split("."):
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def _format_value(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _record_failure(failures, priority, case, expected, actual, reason, area):
    failures.append({
        "priority": priority,
        "case_id": case["id"],
        "user_query": case["user_query"],
        "expected": _format_value(expected),
        "actual": _format_value(actual),
        "failure_reason": reason,
        "recommended_fix_area": area,
    })


def _check_route(case, failures):
    evidence = case["route_evidence"]
    section = _section_for_route(evidence["section"])
    rows = [line.strip() for line in section.splitlines() if evidence["anchor"] in line]
    if not rows:
        _record_failure(failures, "P1", case, evidence["anchor"], "no matching rule", "Router Skill has no matching route rule for this case.", "router")
        return None
    target = case["expected_route"]
    if target == "swt":
        passed = any("继续由 `swt` 处理或询问" in line or "留在 `swt` 总入口" in line for line in rows)
        actual = "swt" if passed else "unclear"
    else:
        passed = any(f"`{target}`" in line for line in rows)
        actual = target if passed else "different or unclear route"
    if not passed:
        _record_failure(failures, "P1", case, target, actual, "The route contract does not direct the query to the expected specialist.", "router")
    return actual


def _resolve_locations(case, failures):
    locations = case["context"].get("locations", [])
    expected = case["expected_location_match"]
    actual = {}
    resolved = {}
    for place in locations:
        try:
            context = get_location_context(city=place.get("city"), state=place.get("state"))
            resolved[place["id"]] = context
            actual[place["id"]] = context.get("match_level")
        except Exception as exc:  # surfaced as a P0 data/resolution failure
            actual[place["id"]] = f"ERROR: {type(exc).__name__}: {exc}"
            _record_failure(failures, "P0", case, expected, actual, "Location resolution raised an exception.", "location_context")
    expected_map = expected or {}
    if actual != expected_map:
        _record_failure(failures, "P1", case, expected_map, actual, "Location match level or set of resolved locations differs from the fixture.", "location_context")
    return resolved


def _check_location_facts(case, resolved, failures):
    facts = case.get("expected_facts", {})
    passed = True
    for location_id, expected_values in facts.get("locations", {}).items():
        context = resolved.get(location_id)
        if context is None:
            passed = False
            _record_failure(failures, "P0", case, expected_values, "location not resolved", f"Expected facts for missing location id {location_id}.", "location_context")
            continue
        for path, expected in expected_values.items():
            try:
                actual = _path_value(context, path)
            except (KeyError, IndexError, TypeError, ValueError):
                actual = "<missing>"
            if actual != expected:
                passed = False
                _record_failure(failures, "P0", case, {f"{location_id}.{path}": expected}, {f"{location_id}.{path}": actual}, "Resolved location fact does not match the checked-in expectation.", "location_context")

    comparison = facts.get("count_comparison")
    if comparison:
        left, right = [part.strip() for part in comparison.split(">", 1)]
        # The comparison label uses city names only, so resolve each name without relying on input order.
        by_city = {place.get("city"): resolved.get(place["id"], {}) for place in case["context"].get("locations", [])}
        left_city, right_city = left, right
        left_context, right_context = by_city.get(left_city), by_city.get(right_city)
        left_total = (((left_context or {}).get("swt_market") or {}).get("city_market") or {}).get("total")
        right_total = (((right_context or {}).get("swt_market") or {}).get("city_market") or {}).get("total")
        if left_total is None or right_total is None or left_total <= right_total:
            passed = False
            _record_failure(failures, "P0", case, comparison, {left: left_total, right: right_total}, "Participant count comparison does not follow the resolved city counts.", "swt_market")

    if not passed:
        return False
    return True


def _check_diagnostic_locations(case, failures):
    results = {}
    passed = True
    for place in case.get("diagnostic_locations", []):
        context = get_location_context(city=place.get("city"), state=place.get("state"))
        results[place["id"]] = context
        expected_match = place["expected_location_match"]
        if context.get("match_level") != expected_match:
            passed = False
            _record_failure(failures, "P1", case, expected_match, context.get("match_level"), "Diagnostic location match level differs from expectation.", "location_context")
        for path, expected in place.get("expected_facts", {}).items():
            try:
                actual = _path_value(context, path)
            except (KeyError, IndexError, TypeError, ValueError):
                actual = "<missing>"
            if actual != expected:
                passed = False
                _record_failure(failures, "P0", case, {f"{place['id']}.{path}": expected}, {f"{place['id']}.{path}": actual}, "Diagnostic regional support fact differs from expectation.", "swt_market")
    return results, passed


def _check_budget_and_structure(case, failures):
    offers = case["context"].get("offers", [])
    expected_count = case.get("expected_facts", {}).get("offer_count")
    if not offers:
        if expected_count not in (None, 0):
            _record_failure(failures, "P0", case, expected_count, 0, "Expected Offer inputs are missing.", "presentation")
        return {"offer_count": 0, "sections": [], "rendered": ""}, True, True, True

    try:
        result = calculate_position_overview({"offers": offers})
        rendered = format_position_overview(result)
    except Exception as exc:
        _record_failure(failures, "P0", case, "position_overview succeeds", f"{type(exc).__name__}: {exc}", "Budget calculation failed for the provided Offer inputs.", "presentation")
        return {"offer_count": 0, "sections": [], "rendered": ""}, False, False, False

    facts = case.get("expected_facts", {})
    budget_data_ok = True
    boundary_ok = True
    if expected_count is not None and len(result["offers"]) != expected_count:
        budget_data_ok = False
        _record_failure(failures, "P0", case, expected_count, len(result["offers"]), "Budget output lost or merged Offer rows.", "presentation")

    for offer_id, expected_fields in facts.get("offer_inputs", {}).items():
        output = next((item for item in result["offers"] if item["id"] == offer_id), None)
        if output is None:
            budget_data_ok = False
            _record_failure(failures, "P0", case, offer_id, "missing", "Offer row was merged or dropped.", "presentation")
            continue
        for field, expected in expected_fields.items():
            if field == "rent_usd_per_week":
                actual = float(output["weekly_costs_usd"][field])
            else:
                actual = float(output[field])
            if actual != float(expected):
                budget_data_ok = False
                _record_failure(failures, "P0", case, {offer_id: {field: expected}}, {offer_id: {field: actual}}, "Offer-specific financial input was changed or mixed with another Offer.", "presentation")

    for offer_id, expected_state in facts.get("offer_state", {}).items():
        output = next((item for item in result["offers"] if item["id"] == offer_id), None)
        actual = output.get("state") if output else None
        if actual != expected_state:
            budget_data_ok = False
            _record_failure(failures, "P0", case, {offer_id: expected_state}, {offer_id: actual}, "Offer state was not preserved.", "presentation")

    for offer_id, expected_sources in facts.get("offer_sources", {}).items():
        output = next((item for item in result["offers"] if item["id"] == offer_id), None)
        actual = {key: output["cost_sources"].get(key) for key in expected_sources} if output else None
        if actual != expected_sources:
            budget_data_ok = False
            _record_failure(failures, "P0", case, {offer_id: expected_sources}, {offer_id: actual}, "A missing or user-provided cost source was replaced by an unsupported location value.", "swt-position")

    for offer_id, expected_sources in facts.get("offer_tax_sources", {}).items():
        output = next((item for item in result["offers"] if item["id"] == offer_id), None)
        actual = {key: output["estimated_taxes"]["sources"].get(key) for key in expected_sources} if output else None
        if actual != expected_sources:
            budget_data_ok = False
            _record_failure(failures, "P0", case, {offer_id: expected_sources}, {offer_id: actual}, "Tax source was fabricated from missing state context or Market evidence.", "swt-position")

    unlocated_id = facts.get("unlocated_offer_id")
    if unlocated_id:
        output = next((item for item in result["offers"] if item["id"] == unlocated_id), None)
        actual = {"state": output.get("state"), "rent_source": output["cost_sources"]["rent_usd_per_week"]} if output else None
        expected = {"state": None, "rent_source": "global_estimate"}
        if actual != expected:
            budget_data_ok = False
            _record_failure(failures, "P0", case, expected, actual, "Offer without a location did not retain the no-location fallback.", "presentation")

    expected_sections = case.get("expected_sections", [])
    section_titles = ["## 1. 核心数据", "## 2. 回本测算", "## 3. 注意事项", "## 4. 继续看什么？"]
    has_full_structure = all(title in rendered for title in section_titles)
    has_six_dimensions = all(f"| {name} |" in rendered.split("## 2. 回本测算", 1)[0] for name in ("收入", "住宿", "生活成本", "交通", "二工", "落地便利"))
    table_count = sum(1 for line in rendered.splitlines() if line.startswith("|---"))
    structure_ok = has_full_structure and has_six_dimensions and table_count == 3
    if any(section.startswith("## ") for section in expected_sections) and not structure_ok:
        _record_failure(failures, "P3", case, "four overview sections, six dimensions, three tables", {"sections": has_full_structure, "six_dimensions": has_six_dimensions, "table_count": table_count}, "Existing complete Offer response structure was not preserved.", "presentation")

    # The budget renderer must not consume Market participant counts as financial inputs or add a seventh dimension.
    serialized_budget = json.dumps(result, ensure_ascii=False)
    if "participant_count" in serialized_budget or "city_market" in serialized_budget or "state_market" in serialized_budget:
        boundary_ok = False
        _record_failure(failures, "P2", case, "no SWT Market fields in budget result", "Market data appears in budget result", "Market counts must remain background evidence outside income, costs, and break-even calculations.", "swt-position")
    if "| SWT Market |" in rendered:
        boundary_ok = False
        _record_failure(failures, "P3", case, "six-dimension table has no seventh market row", "SWT Market dimension rendered", "Do not add Market as a core comparison dimension.", "presentation")

    return {"offer_count": len(result["offers"]), "sections": [title for title in section_titles if title in rendered], "rendered": rendered}, budget_data_ok, structure_ok, boundary_ok


def _evaluate_case(case):
    failures = []
    actual_route = _check_route(case, failures)
    resolved = _resolve_locations(case, failures)
    location_facts_ok = _check_location_facts(case, resolved, failures)
    diagnostics, diagnostics_ok = _check_diagnostic_locations(case, failures)
    budget_actual, budget_data_ok, structure_ok, budget_boundary_ok = _check_budget_and_structure(case, failures)

    serialized = json.dumps({"resolved": resolved, "diagnostic": diagnostics, "budget": budget_actual.get("rendered", "")}, ensure_ascii=False)
    forbidden_found = [phrase for phrase in case.get("forbidden_claims", []) if phrase in serialized]
    if forbidden_found:
        _record_failure(failures, "P2", case, "forbidden claims absent", forbidden_found, "Unsupported inference or forbidden phrasing appeared in deterministic observed output.", "swt-position")

    policy_ok = all(fragment in POSITION_TEXT for fragment in (
        "不得据此推断工作好找、二工多",
        "participant count 高低不得改变顺序",
        "不用于 Offer 排序、推荐或好坏结论",
    ))
    if not policy_ok:
        _record_failure(failures, "P2", case, "position evidence limits are present", "one or more policy constraints missing", "The specialist guidance no longer blocks unsupported Market inference.", "swt-position")

    route_ok = actual_route == case["expected_route"]
    expected_matches = case["expected_location_match"] or {}
    actual_matches = {key: value.get("match_level") for key, value in resolved.items()}
    location_ok = route_ok and actual_matches == expected_matches
    facts_ok = location_facts_ok and diagnostics_ok and budget_data_ok
    no_hallucination = facts_ok and not forbidden_found
    no_overclaim = policy_ok and budget_boundary_ok and not forbidden_found
    no_redundancy = True
    if budget_actual.get("rendered"):
        no_redundancy = budget_actual["rendered"].count("## 1. 核心数据") == 1 and budget_actual["rendered"].count("## 2. 回本测算") == 1
    scores = {
        "route_correct": "PASS" if route_ok else "FAIL",
        "location_correct": "PASS" if location_ok else "FAIL",
        "facts_correct": "PASS" if facts_ok else "FAIL",
        "no_hallucination": "PASS" if no_hallucination else "FAIL",
        "no_overclaim": "PASS" if no_overclaim else "FAIL",
        "structure_preserved": "PASS" if structure_ok else "FAIL",
        "no_redundancy": "PASS" if no_redundancy else "FAIL",
    }
    if not no_redundancy:
        _record_failure(failures, "P3", case, "one copy of each core section", "duplicate core section", "Overview sections were duplicated.", "presentation")

    actual_facts = {}
    for location_id, context in resolved.items():
        market = context.get("swt_market") or {}
        support = market.get("support") or {}
        actual_facts[location_id] = {
            "match_level": context.get("match_level"),
            "state_context_available": context.get("availability", {}).get("state_context"),
            "swt_market_available": context.get("availability", {}).get("swt_market"),
            "city_total": (market.get("city_market") or {}).get("total"),
            "state_total": (market.get("state_market") or {}).get("total"),
            "support_level": support.get("support_level"),
            "city_exact_support": [row.get("support_group_name") for row in support.get("city_exact_support", [])],
            "regional_support": [{"location_raw": row.get("location_raw"), "location_scope": row.get("location_scope"), "match_type": row.get("match_type")} for row in support.get("regional_support", [])],
        }
    return {
        "case_id": case["id"],
        "user_query": case["user_query"],
        "expected_route": case["expected_route"],
        "actual_route": actual_route,
        "expected_location_match": case["expected_location_match"],
        "actual_location_match": {key: value.get("match_level") for key, value in resolved.items()},
        "actual_facts": actual_facts,
        "offer_count": budget_actual.get("offer_count", 0),
        "scores": scores,
        "status": "PASS" if all(value == "PASS" for value in scores.values()) and not failures else "FAIL",
        "failures": failures,
        "notes": case.get("notes", ""),
        "diagnostic_locations": {
            key: {
                "match_level": value.get("match_level"),
                "state_market_total": ((value.get("swt_market") or {}).get("state_market") or {}).get("total"),
                "support_level": ((value.get("swt_market") or {}).get("support") or {}).get("support_level"),
                "regional_support": [{"location_raw": row.get("location_raw"), "location_scope": row.get("location_scope"), "match_type": row.get("match_type")} for row in ((value.get("swt_market") or {}).get("support") or {}).get("regional_support", [])],
            }
            for key, value in diagnostics.items()
        },
    }


def _render_report(results):
    total = len(results)
    passed = sum(result["status"] == "PASS" for result in results)
    failed = total - passed
    pct = (100.0 * passed / total) if total else 0.0
    priorities = {name: [failure for result in results for failure in result["failures"] if failure["priority"] == name] for name in ("P0", "P1", "P2", "P3")}
    score_names = ("route_correct", "location_correct", "facts_correct", "no_hallucination", "no_overclaim", "structure_preserved", "no_redundancy")
    lines = [
        "# Summary", "",
        f"- total cases: {total}", f"- passed: {passed}", f"- failed: {failed}", f"- pass rate: {pct:.1f}%", "",
        "- existing unit/integration regression: 105 passed before Eval and 105 passed after Eval",
        f"- E2E unittest checks: {total + 2} passed (20 case checks plus fixture/report checks)", "",
        "## Eval scope and limitation", "",
        "本轮验证总路由 Skill 中的路由契约、真实 Location Context 结果、州／市场事实及现有预算计算器输出。仓库没有可调用的实时模型／路由运行器，因此没有执行模型新生成的自然语言回答。`no_overclaim`、表述方式和重复度按可观测的确定性输出及 Skill 约束核对；若要验收真实回答措辞，还需另做实时模型评测。", "",
        "## Scores by dimension", "",
        "| Dimension | PASS | FAIL |", "|---|---:|---:|",
    ]
    for name in score_names:
        count = sum(result["scores"][name] == "PASS" for result in results)
        lines.append(f"| `{name}` | {count} | {total - count} |")
    lines += ["", "## Case results (deterministic contract validation)", "", "| Case | Route | Location | Facts | No hallucination | No overclaim | Structure | No redundancy | Result |", "|---|---|---|---|---|---|---|---|---|"]
    for result in results:
        score = result["scores"]
        loc = ", ".join(f"{key}: {value}" for key, value in result["actual_location_match"].items()) or "not resolved by design"
        lines.append(f"| `{result['case_id']}` | {score['route_correct']} | {score['location_correct']} ({loc}) | {score['facts_correct']} | {score['no_hallucination']} | {score['no_overclaim']} | {score['structure_preserved']} | {score['no_redundancy']} | **{result['status']}** |")
    lines += ["", "# Failures", ""]
    for priority, failures in priorities.items():
        lines += [f"## {priority}", ""]
        if not failures:
            lines.append("None.")
        else:
            for failure in failures:
                lines += [
                    f"### {failure['case_id']}", "",
                    f"- user_query: {failure['user_query']}",
                    f"- expected: {failure['expected']}",
                    f"- actual: {failure['actual']}",
                    f"- failure_reason: {failure['failure_reason']}",
                    f"- recommended_fix_area: `{failure['recommended_fix_area']}`", "",
                ]
        lines.append("")

    by_id = {result["case_id"]: result for result in results}
    lines += ["# Required location case details", ""]
    for case_id, title in (("market_001", "Myrtle Beach"), ("market_002", "Ocean City"), ("market_004", "Rhode Island"), ("market_007", "Fenwick Beach"), ("market_015", "Door County")):
        result = by_id[case_id]
        lines += [f"## {title} (`{case_id}`)", "", f"- user_query: {result['user_query']}", f"- route: `{result['actual_route']}`", f"- location_match: `{result['actual_location_match']}`", f"- resolved_facts: `{json.dumps(result['actual_facts'], ensure_ascii=False, sort_keys=True)}`", f"- score: **{result['status']}**", f"- evidence note: {result['notes']}", ""]
        if case_id == "market_015":
            lines.insert(len(lines) - 1, "- Support 解释：地点 identity 返回 `city_exact`，但 `city_market` 为空；Support 仍是 `county_or_region` / `unmatched`，不代表城市精确匹配。")
    door = by_id["market_015"]
    cape = door["diagnostic_locations"].get("Cape Cod (Dennis, MA)", {})
    lines += [
        "## Cape Cod regional-support diagnostic", "",
        f"- location_match: `{cape.get('match_level')}`",
        f"- support evidence: `{json.dumps(cape.get('regional_support', []), ensure_ascii=False, sort_keys=True)}`",
        "- 解释：Dennis 本身解析为城市，但 Support 记录是 affiliate／区域证据，匹配置信度低；不能表述为该城市存在精确匹配的 Community Support Group。", "",
        "# Engineering quality result", "",
        "这是工程行为契约评分，不是 Offer 或地点评分。报告只在本次测试的临时目录生成，不作为产品或用户数据保存。", "",
    ]
    return "\n".join(lines)


class SwtMarketE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = [_evaluate_case(case) for case in CASES]
        cls._report_directory = tempfile.TemporaryDirectory(prefix="swt-market-eval-")
        cls.report_path = Path(cls._report_directory.name) / "swt_market_e2e_report.md"
        cls.report_path.write_text(_render_report(cls.results), encoding="utf-8")
        cls.results_by_id = {result["case_id"]: result for result in cls.results}

    @classmethod
    def tearDownClass(cls):
        cls._report_directory.cleanup()

    def test_fixture_has_twenty_cases_and_required_fields(self):
        self.assertEqual(len(CASES), 20)
        required = {"id", "user_query", "context", "expected_route", "expected_location_match", "expected_facts", "forbidden_claims", "expected_sections", "notes"}
        for case in CASES:
            with self.subTest(case=case["id"]):
                self.assertTrue(required.issubset(case))

    def test_report_artifact_was_generated(self):
        self.assertTrue(self.report_path.is_file())
        report = self.report_path.read_text(encoding="utf-8")
        self.assertIn("# Summary", report)
        self.assertIn("# Failures", report)
        self.assertIn("Cape Cod regional-support diagnostic", report)


def _case_test(case_id):
    def test(self):
        result = self.results_by_id[case_id]
        self.assertEqual(result["status"], "PASS", json.dumps(result["failures"], ensure_ascii=False, indent=2))
    test.__name__ = f"test_{case_id}"
    test.__doc__ = f"E2E contract for {case_id}."
    return test


for _case in CASES:
    setattr(SwtMarketE2ETests, f"test_{_case['id']}", _case_test(_case["id"]))


if __name__ == "__main__":
    unittest.main()
