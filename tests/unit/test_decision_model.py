import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from decision_model import clarification_level_for, validate_decision  # noqa: E402


class DecisionModelTests(unittest.TestCase):
    def test_accepts_canonical_answer_record(self):
        validate_decision({
            "intent": "GENERAL_QA", "route": "swt", "confidence": "medium", "risk": "green",
            "evidence_status": "confirmed", "materiality": "non_material",
            "missing_information": "none", "clarification_level": 1,
            "next_action": "answer", "reason_code": "direct_answer",
        })

    def test_critical_conflict_requires_verification_or_pause(self):
        record = {
            "intent": "CONFLICT", "route": "swt-visa", "confidence": "high", "risk": "red",
            "evidence_status": "conflicting", "materiality": "critical",
            "missing_information": "safety_blocking", "clarification_level": 4,
            "next_action": "pause_action", "reason_code": "fact_conflict",
        }
        validate_decision(record)
        with self.assertRaises(ValueError):
            validate_decision(dict(record, next_action="answer"))

    def test_finite_stage_and_route(self):
        base = {
            "intent": "NAVIGATION", "route": "swt", "confidence": "medium", "risk": "green",
            "evidence_status": "confirmed", "materiality": "non_material",
            "missing_information": "none", "next_action": "answer", "reason_code": "direct_answer",
        }
        with self.assertRaises(ValueError):
            validate_decision(dict(base, stage="12"))
        with self.assertRaises(ValueError):
            validate_decision(dict(base, route="new-skill"))
        with self.assertRaises(ValueError):
            validate_decision(dict(base, intent="CALCULATION", route="swt"))

    def test_missing_information_maps_to_existing_clarification_levels(self):
        self.assertEqual(
            [clarification_level_for(value) for value in ("none", "low_impact", "conclusion_changes", "safety_blocking")],
            [1, 2, 3, 4],
        )
        with self.assertRaises(ValueError):
            clarification_level_for("invented")

    def test_known_context_is_not_requested_again(self):
        record = {
            "intent": "NAVIGATION", "route": "swt", "confidence": "high", "risk": "green",
            "evidence_status": "confirmed", "materiality": "material",
            "missing_information": "conclusion_changes", "clarification_level": 3,
            "known_context_keys": ["sponsor_name"], "missing_information_keys": ["program_year"],
            "next_action": "ask_one_question", "reason_code": "context_needed",
        }
        validate_decision(record)
        with self.assertRaises(ValueError):
            validate_decision(dict(record, missing_information_keys=["sponsor_name"]))

    def test_assessment_and_practice_stay_separate(self):
        record = {
            "intent": "ENGLISH_PRACTICE", "route": "swt-english", "confidence": "high", "risk": "green",
            "evidence_status": "confirmed", "materiality": "non_material",
            "missing_information": "none", "next_action": "start_practice", "reason_code": "practice_requested",
        }
        validate_decision(record)
        with self.assertRaises(ValueError):
            validate_decision(dict(record, next_action="start_assessment"))


if __name__ == "__main__":
    unittest.main()
