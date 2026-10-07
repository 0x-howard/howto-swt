#!/usr/bin/env python3
"""Routing contracts for SWT position and location questions."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_TEXT = (ROOT / "skills/swt/SKILL.md").read_text(encoding="utf-8")
ROUTING = (ROOT / "shared/routing-policy.md").read_text(encoding="utf-8")
POSITION_INTENTS = ROUTING
SPECIALIST_PRIORITY = ROUTING
CONTEXT_SECTION = SKILL_TEXT.split("## 上下文不足时", 1)[1]


class SwtRouterPositionIntentTests(unittest.TestCase):
    def assert_route_row(self, section, utterance, skill):
        rows = [line for line in section.splitlines() if utterance in line]
        self.assertTrue(rows, f"No routing example for: {utterance}")
        self.assertTrue(any(f"`{skill}`" in line for line in rows),
                        f"{utterance!r} should route to {skill}; rows: {rows}")

    def test_offer_analysis_routes_to_position(self):
        self.assert_route_row(POSITION_INTENTS, "帮我分析这个 Offer", "swt-position")

    def test_city_choice_routes_to_position(self):
        self.assert_route_row(POSITION_INTENTS, "Ocean City 和 Myrtle Beach 怎么选", "swt-position")

    def test_participant_count_question_routes_to_position(self):
        self.assert_route_row(POSITION_INTENTS, "Myrtle Beach 的 participant count 是多少", "swt-position")

    def test_community_support_question_routes_to_position(self):
        self.assert_route_row(POSITION_INTENTS, "Myrtle Beach 有没有 Community Support Group", "swt-position")

    def test_location_word_does_not_override_visa_intent(self):
        self.assert_route_row(SPECIALIST_PRIORITY, "我在 Myrtle Beach 面签要准备什么", "swt-visa")

    def test_location_word_does_not_override_english_intent(self):
        self.assert_route_row(SPECIALIST_PRIORITY, "帮我练 Myrtle Beach 雇主面试英语", "swt-english")

    def test_location_word_does_not_override_arrival_intent(self):
        self.assert_route_row(SPECIALIST_PRIORITY, "到了 Myrtle Beach 第一周要做什么", "swt-arrival")

    def test_location_word_does_not_override_application_intent(self):
        self.assert_route_row(SPECIALIST_PRIORITY, "申请 South Carolina 的岗位要准备什么材料", "swt-application")

    def test_existing_compare_jobs_intent_still_routes_to_position(self):
        self.assert_route_row(POSITION_INTENTS, "对比岗位", "swt-position")

    def test_brand_call_activates_home_but_plain_greeting_does_not(self):
        description = SKILL_TEXT.splitlines()[2]
        self.assertIn("小How", description)
        self.assertIn("howto swt", description)
        self.assertIn("howto-swt", description)
        self.assertIn("你好，我在。你可以直接选一项：", SKILL_TEXT)
        self.assertIn("回复字母，或者直接说你要办的事。", SKILL_TEXT)
        self.assertIn("仅“你好”“hello”“hi”“在吗”不触发", SKILL_TEXT)
        self.assertIn("小How帮我看看这个岗位", SKILL_TEXT)
        self.assertIn("`DIRECT`", SKILL_TEXT)

    def test_general_swt_process_stays_in_the_main_skill(self):
        self.assertIn("SWT 全流程怎么走", CONTEXT_SECTION)
        self.assertIn("导航问题留在 `swt`", CONTEXT_SECTION)

    def test_bare_city_name_does_not_force_position_routing(self):
        bare_place_rule = next(line for line in CONTEXT_SECTION.splitlines() if "单独地名" in line)
        self.assertIn("Myrtle Beach", bare_place_rule)
        self.assertIn("不直接触发 `swt-position`", bare_place_rule)
        self.assertIn("`CLARIFY`", bare_place_rule)

    def test_router_does_not_expose_backend_names_in_user_facing_answers(self):
        for term in ("location_context.py", "swt_market.py", "state_summary.json", "Resolver", "API"):
            self.assertNotIn(term, SKILL_TEXT)
        self.assertIn("不提内部实现、文件名、Executor 或工具接口", SKILL_TEXT)


if __name__ == "__main__":
    unittest.main()
