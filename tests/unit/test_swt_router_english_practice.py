#!/usr/bin/env python3
"""Contracts for SWT English Practice v0.8 routing and session boundaries."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = (ROOT / "skills/swt-english/SKILL.md").read_text(encoding="utf-8")
PRACTICE = (ROOT / "references/english-practice.md").read_text(encoding="utf-8")
ROUTING = (ROOT / "shared/routing-policy.md").read_text(encoding="utf-8")
STATE = (ROOT / "shared/state-schema.md").read_text(encoding="utf-8")
PROFILES = (ROOT / "references/english-profiles.md").read_text(encoding="utf-8")


class EnglishPracticeTests(unittest.TestCase):
    def test_recent_assessment_routes_to_one_or_two_weaknesses(self):
        for field in ("profile", "criteria", "confidence", "top_weaknesses", "target_position"):
            self.assertIn(field, SKILL + PRACTICE)
        self.assertIn("最低且重要的 1–2 个", SKILL + PRACTICE)
        self.assertIn("confidence 低", PRACTICE)
        self.assertIn("weakness_drill", PRACTICE)

    def test_four_practice_profiles_map_to_existing_assessment_profiles(self):
        mappings = {
            "agency_practice": "agency_generic",
            "sponsor_practice": "sponsor_generic",
            "host_practice": "host_generic",
            "visa_interview_practice": "visa_interview_generic",
        }
        for practice_profile, assessment_profile in mappings.items():
            with self.subTest(profile=practice_profile):
                self.assertIn(f"`{practice_profile}` → `{assessment_profile}`", PRACTICE)
                self.assertIn(f"`{assessment_profile}`", PROFILES)

    def test_host_and_visa_context_boundaries_are_explicit(self):
        self.assertIn("只问一次“你准备练哪个岗位？", PRACTICE)
        self.assertIn("暂停语言优化", PRACTICE)
        self.assertIn("`swt-visa` 负责事实正确性", PRACTICE)
        self.assertIn("沟通质量", PRACTICE)

    def test_retry_and_feedback_order_preserve_one_question_loop(self):
        loop = "Question → User Answer → Short Feedback → Retry → Follow-up / Next Question"
        self.assertIn(loop, PRACTICE)
        self.assertIn("每题最多再给必要的第二次 Retry", PRACTICE)
        priorities = (
            "没听懂问题或答非所问",
            "当前表达无法完成题目要求的任务",
            "互动、澄清、修复或追问应对失败",
            "流利度明显受阻",
            "影响理解的语法错误",
            "影响任务的词汇表达",
            "小语法或措辞问题",
        )
        feedback_section = PRACTICE.split("### 短反馈与示范答案", 1)[1].split("### 练习目标复用", 1)[0]
        offsets = [feedback_section.index(item) for item in priorities]
        self.assertEqual(offsets, sorted(offsets))
        self.assertIn("默认只修 1–2 个", PRACTICE)

    def test_modes_and_compressed_session_end_are_complete(self):
        for mode in ("full_mock", "weakness_drill", "follow_up_drill", "question_drill", "scenario_drill"):
            self.assertIn(f"`{mode}`", PRACTICE)
        for choice in ("A. 再练一轮", "B. 换一个弱项", "C. 做完整 v0.7 复测", "D. 结束"):
            self.assertIn(choice, PRACTICE)
        self.assertIn("Before / After 最明显的 1–3 个变化", PRACTICE)

    def test_practice_state_is_separate_and_minimal(self):
        section = STATE.split("## SWT English Practice State", 1)[1]
        for field in (
            "profile:", "target_position:", "focus_dimensions:", "mode:",
            "question_count:", "retry_count:", "session_improvements:", "completed:",
        ):
            self.assertIn(field, section)
        self.assertIn("Practice State 与正式结果分别维护", section)
        self.assertIn("不能修改／覆盖 `english_assessment`", PRACTICE)
        self.assertIn("用户选择“重新测一下”时", PRACTICE)
        self.assertIn("转入 `ASSESS`", PRACTICE)

    def test_eval_cases_cover_all_twenty_requested_practice_behaviors(self):
        cases = json.loads((ROOT / "tests/evals/cases/evals.json").read_text(encoding="utf-8"))["cases"]
        ids = {case["id"] for case in cases}
        self.assertEqual(sum(cid.startswith("english-practice-") for cid in ids), 20)
        for number in range(1, 21):
            self.assertEqual(sum(cid.startswith(f"english-practice-{number:02d}-") for cid in ids), 1)
        self.assertIn("按刚才测评里最弱的两项陪我练", ROUTING)
        self.assertIn("`swt-english` / PRACTICE", ROUTING)


if __name__ == "__main__":
    unittest.main()
