#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from english_speaking import (  # noqa: E402
    MAX_FOLLOW_UPS_PER_MAIN_QUESTION,
    PRIMARY_MODES,
    advance_mock,
    evidence_capabilities,
    new_mock_session,
)


class EnglishSpeakingCoachTests(unittest.TestCase):
    def test_exactly_six_primary_modes(self):
        self.assertEqual(PRIMARY_MODES, ("ASSESS", "PRACTICE", "MOCK", "RECORDING", "RETRY", "PROGRESS"))

    def test_mock_never_creates_fourth_follow_up(self):
        session = new_mock_session("sponsor")
        for index in range(1, 4):
            session = advance_mock(session, "clarification")
            self.assertEqual(session["state"], f"FOLLOW_UP_{index}")
        session = advance_mock(session, "incomplete")
        self.assertEqual(session["state"], "NEXT_MAIN")
        self.assertEqual(session["follow_up_count"], 0)
        self.assertEqual(MAX_FOLLOW_UPS_PER_MAIN_QUESTION, 3)

    def test_sufficient_answer_can_skip_follow_ups(self):
        session = advance_mock(new_mock_session("host_employer"), "sufficient")
        self.assertEqual(session["state"], "NEXT_MAIN")
        self.assertEqual(session["main_question_index"], 1)

    def test_mock_feedback_is_delayed_until_completion(self):
        session = new_mock_session("agency")
        self.assertTrue(session["delayed_feedback"])
        session = advance_mock(session, "mock_complete")
        self.assertEqual(session["state"], "ASSESSMENT")
        self.assertTrue(session["completed"])

    def test_transcript_cannot_support_pronunciation(self):
        transcript = evidence_capabilities("transcript")
        self.assertEqual(transcript["pronunciation"], "not_assessed")
        self.assertFalse(transcript["audio_fluency"])
        self.assertEqual(evidence_capabilities("audio")["pronunciation"], "assessed")

    def test_practice_and_mock_contracts_are_separate(self):
        contract = (ROOT / "references/english-speaking-coach.md").read_text(encoding="utf-8")
        self.assertIn("Immediate Feedback", contract)
        self.assertIn("Feedback is delayed until completion", contract)
        self.assertIn("do not correct, teach, supply a standard answer", contract)


if __name__ == "__main__":
    unittest.main()
