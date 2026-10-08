#!/usr/bin/env python3
"""Routing contracts for the v0.7 English Assessment intents."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTING = (ROOT / "shared/routing-policy.md").read_text(encoding="utf-8")
ORCHESTRATOR = (ROOT / "skills/swt/SKILL.md").read_text(encoding="utf-8")
ENGLISH = (ROOT / "skills/swt-english/SKILL.md").read_text(encoding="utf-8")


class EnglishAssessmentRoutingTests(unittest.TestCase):
    def test_all_five_assessment_examples_route_to_assess(self):
        examples = (
            ("测一下机构口语", "agency_generic"),
            ("帮我模拟 Sponsor 并评分", "sponsor_generic"),
            ("我要面试 cashier，测一下", "host_generic"),
            ("测一下美签英语", "visa_interview_generic"),
            ("综合 SWT 英语测评", "Comprehensive"),
        )
        for utterance, profile in examples:
            with self.subTest(utterance=utterance):
                row = next(line for line in ROUTING.splitlines() if utterance in line)
                self.assertIn("swt-english", row)
                self.assertIn("ASSESS", row)
                self.assertIn(profile, row)

    def test_known_host_context_is_reused(self):
        self.assertIn("复用已知 Position Context", ROUTING)
        self.assertIn("不重复询问", ORCHESTRATOR)
        self.assertIn("恢复当前会话已知上下文", ENGLISH)

    def test_visa_documents_and_visa_roleplay_have_distinct_routes(self):
        self.assertRegex(ROUTING, r"签证需要什么材料.*`swt-visa`.*不因出现“英语”路由到 English")
        self.assertRegex(ROUTING, r"模拟签证官问问题.*`swt-visa`.*`swt-english` / MOCK")
        self.assertIn("事实与材料由 `swt-visa` 提供", ENGLISH)

    def test_six_modes_and_general_english_fallback(self):
        for mode in ("ASSESS", "PRACTICE", "MOCK", "RECORDING", "RETRY", "PROGRESS"):
            self.assertIn(mode, ENGLISH)
        self.assertIn("GENERAL ENGLISH", ENGLISH)
        self.assertIn("fallback", ENGLISH)

    def test_reassessment_weakness_practice_and_retake_are_distinct(self):
        row = next(line for line in ROUTING.splitlines() if "按刚才测评里最弱的两项陪我练" in line)
        self.assertIn("PRACTICE", row)
        self.assertIn("不改其正式分数", row)
        self.assertIn("“重新测一下”", ENGLISH)
        self.assertIn("正式进入 `ASSESS`", ENGLISH)


if __name__ == "__main__":
    unittest.main()
