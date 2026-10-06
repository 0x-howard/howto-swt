#!/usr/bin/env python3
"""Deterministic tests for SWT English Assessment readiness calculations."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from speaking_score import (  # noqa: E402
    PROFILES,
    calculate_comprehensive,
    calculate_readiness,
    load_minimum_evidence,
    load_profile_weights,
)


def evidence_set(scores=None, counts=None, confidences=None):
    scores = scores or {}
    counts = counts or {}
    confidences = confidences or {}
    return {
        key: {
            "score": scores.get(key, 7),
            "confidence": confidences.get(key, "high"),
            "evidence_count": counts.get(key, load_minimum_evidence()[key]),
        }
        for key in load_minimum_evidence()
    }


class SpeakingScoreTests(unittest.TestCase):
    def test_profile_weights_match_v07_rubric(self):
        weights = load_profile_weights()
        self.assertEqual(set(weights), set(PROFILES))
        self.assertEqual(weights["agency_generic"], {
            "comprehension_relevance": 20, "fluency_coherence": 20, "vocabulary": 15,
            "grammar": 10, "pronunciation_intelligibility": 15, "interaction_repair": 10,
            "task_communication": 10,
        })
        self.assertEqual(weights["sponsor_generic"], {
            "comprehension_relevance": 25, "fluency_coherence": 15, "vocabulary": 10,
            "grammar": 10, "pronunciation_intelligibility": 15, "interaction_repair": 20,
            "task_communication": 5,
        })
        self.assertEqual(weights["host_generic"], {
            "comprehension_relevance": 20, "fluency_coherence": 15, "vocabulary": 10,
            "grammar": 5, "pronunciation_intelligibility": 15, "interaction_repair": 10,
            "task_communication": 25,
        })
        self.assertEqual(weights["visa_interview_generic"], {
            "comprehension_relevance": 30, "fluency_coherence": 15, "vocabulary": 5,
            "grammar": 5, "pronunciation_intelligibility": 15, "interaction_repair": 15,
            "task_communication": 15,
        })
        self.assertTrue(all(sum(profile.values()) == 100 for profile in weights.values()))

    def test_sponsor_weighted_calculation_is_deterministic(self):
        criteria = evidence_set({
            "comprehension_relevance": 8, "fluency_coherence": 6, "vocabulary": 7,
            "grammar": 7, "pronunciation_intelligibility": 8, "interaction_repair": 5,
            "task_communication": 6,
        })
        result = calculate_readiness(criteria, "sponsor_generic", "voice")
        self.assertEqual(result["target_readiness"], 6.8)
        self.assertEqual(result["readiness_status"], "complete")
        self.assertEqual(result["weight_coverage_pct"], 100)

    def test_rounding_uses_half_up(self):
        criteria = evidence_set({key: 6.25 for key in load_minimum_evidence()})
        self.assertEqual(calculate_readiness(criteria, "agency_generic", "voice")["target_readiness"], 6.3)

    def test_unavailable_pronunciation_returns_partial_assessment(self):
        criteria = evidence_set()
        criteria["pronunciation_intelligibility"] = {
            "score": None, "confidence": "low", "evidence_count": 0,
        }
        result = calculate_readiness(criteria, "sponsor_generic", "transcript")
        self.assertEqual(result["target_readiness"], 7.0)
        self.assertEqual(result["weight_coverage_pct"], 85)
        self.assertEqual(result["readiness_status"], "partial")
        self.assertEqual(result["missing_criteria"]["pronunciation_intelligibility"], "audio_required")

    def test_text_mode_rejects_a_pronunciation_score(self):
        criteria = evidence_set()
        with self.assertRaisesRegex(ValueError, "cannot be scored from text"):
            calculate_readiness(criteria, "agency_generic", "text")

    def test_text_mode_leaves_spoken_interaction_unavailable(self):
        criteria = evidence_set()
        criteria["pronunciation_intelligibility"] = {"score": None, "confidence": "low", "evidence_count": 0}
        criteria["interaction_repair"] = {"score": None, "confidence": "low", "evidence_count": 0}
        result = calculate_readiness(criteria, "agency_generic", "text")
        self.assertEqual(result["missing_criteria"]["interaction_repair"], "spoken_interaction_unavailable")
        self.assertEqual(result["readiness_status"], "partial")

    def test_missing_or_undersampled_criterion_is_excluded_and_partial(self):
        criteria = evidence_set(counts={"interaction_repair": 1})
        result = calculate_readiness(criteria, "sponsor_generic", "voice")
        self.assertEqual(result["readiness_status"], "partial")
        self.assertEqual(result["weight_coverage_pct"], 80)
        self.assertEqual(result["missing_criteria"]["interaction_repair"], "undersampled:1/2")
        del criteria["grammar"]
        result = calculate_readiness(criteria, "sponsor_generic", "voice")
        self.assertEqual(result["missing_criteria"]["grammar"], "missing")

    def test_confidence_is_conservatively_carried_into_result(self):
        criteria = evidence_set(confidences={"interaction_repair": "low"})
        result = calculate_readiness(criteria, "sponsor_generic", "voice")
        self.assertEqual(result["confidence"], "low")

    def test_comprehensive_maps_one_evidence_set_to_four_profiles(self):
        result = calculate_comprehensive(evidence_set(), "voice")
        self.assertEqual(set(result["profiles"]), set(PROFILES))
        self.assertTrue(all(item["readiness_status"] == "complete" for item in result["profiles"].values()))

    def test_no_scores_produces_null_partial_result(self):
        result = calculate_readiness({}, "visa_interview_generic", "text")
        self.assertIsNone(result["target_readiness"])
        self.assertEqual(result["weight_coverage_pct"], 0)
        self.assertEqual(result["readiness_status"], "partial")

    def test_invalid_score_and_profile_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 10"):
            calculate_readiness(evidence_set({"grammar": 10.1}), "agency_generic")
        with self.assertRaisesRegex(ValueError, "profile must be one of"):
            calculate_readiness({}, "agency_example")


if __name__ == "__main__":
    unittest.main()
