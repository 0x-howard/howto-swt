#!/usr/bin/env python3

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class RouterEnglishUpgradeBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = (ROOT / "skills/swt/SKILL.md").read_text(encoding="utf-8")
        cls.english = (ROOT / "skills/swt-english/SKILL.md").read_text(encoding="utf-8")
        cls.contract = (ROOT / "references/english-speaking-coach.md").read_text(encoding="utf-8")

    def test_greeting_has_menu_but_no_subtask_execution(self):
        self.assertIn("你好，我在。你可以直接选一项", self.router)
        self.assertIn("生成 Prompt 后无条件 STOP", self.router)

    def test_task_bearing_sponsor_request_generates_mock_handoff_then_stops(self):
        self.assertIn("mode = MOCK", self.router)
        self.assertIn("scenario = Sponsor Interview", self.router)
        self.assertIn("不得在同一轮调用 Executor、提出第一道题", self.router)

    def test_resume_and_offer_are_reused_in_employer_profile(self):
        for fact in ("Resume", "Offer", "Employer", "Position"):
            self.assertIn(fact, self.english + self.contract)
        self.assertIn("Interview Profile", self.english + self.contract)

    def test_confirmed_handoff_starts_executor_without_router_ad(self):
        self.assertIn("用户确认／修改／重新发送", self.english)
        self.assertNotIn("加入 HowTo SWT Pro", self.english)

    def test_practice_teaches_but_mock_delays_feedback(self):
        self.assertIn("Immediate Feedback", self.contract)
        self.assertIn("Feedback is delayed until completion", self.contract)

    def test_transcript_recording_marks_pronunciation_not_assessed(self):
        self.assertIn("Pronunciation = Not Assessed", self.contract)


if __name__ == "__main__":
    unittest.main()
