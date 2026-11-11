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
    format_result,
    load_minimum_evidence,
    opening_question,
    start_line,
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


class SpeakingResultFormatTests(unittest.TestCase):
    def transcript_criteria(self):
        criteria = evidence_set({"comprehension_relevance": 7, "fluency_coherence": 6, "vocabulary": 5.5,
                                 "grammar": 5, "interaction_repair": 6.5, "task_communication": 6.5})
        criteria["pronunciation_intelligibility"] = {"score": None, "confidence": "low", "evidence_count": 0}
        return criteria

    def test_opening_and_start_lines(self):
        self.assertIn("E. 综合测评（一次覆盖以上四种）", opening_question())
        self.assertEqual(start_line("sponsor_generic", "transcript"),
                         "好的，我们做一次 Sponsor 面试口语测试。你用的是语音输入，我按转写文字评估，发音不打分；中间不纠错，结束后统一反馈。")

    def test_transcript_result_is_compressed_and_chinese(self):
        text = format_result({"profile": "sponsor_generic", "input_mode": "transcript", "ielts_style": 5,
                              "criteria": self.transcript_criteria(),
                              "notes": {"grammar": "时态不稳，如 \"Last summer I go\"。"}})
        self.assertTrue(text.startswith("**按 Sponsor 面试的要求，你目前的准备度约 6.3 / 10（部分测评）：理解与切题较好，主要短板是语法控制和词汇表达。**"))
        self.assertIn("| Sponsor 面试准备度 | 6.3 / 10（部分测评） |", text)
        self.assertIn("| IELTS 风格部分估计 | ≈ 5.0 / 9（不含发音） |", text)
        self.assertIn("- **语法控制**：时态不稳", text)
        self.assertIn("- **词汇表达**：5.5 / 10", text)
        self.assertEqual(text.count("\n- **"), 3)
        self.assertIn("按语音转写评估，发音未测；语音识别错误不计入。", text)
        self.assertTrue(text.endswith("D. 再测一次"))
        self.assertNotIn("Readiness", text)

    def test_text_mode_and_undersampled_limits(self):
        criteria = self.transcript_criteria()
        criteria["interaction_repair"] = {"score": None, "confidence": "low", "evidence_count": 0}
        criteria["task_communication"]["evidence_count"] = 1
        text = format_result({"profile": "host_generic", "input_mode": "text", "target_position": "Cashier", "criteria": criteria})
        self.assertIn("| 雇主面试准备度（Cashier） |", text)
        self.assertIn("当前为文字模拟，不能代表完整口语表现；发音和口头互动未测。", text)
        self.assertIn("任务沟通样本不足，未计入准备度。", text)

    def test_comprehensive_result_names_largest_gap(self):
        text = format_result({"profile": "comprehensive", "input_mode": "transcript", "criteria": self.transcript_criteria()})
        self.assertTrue(text.startswith("**综合测评（部分测评）：签证面试准备度最高（6.4 / 10），机构面试最低（6.1 / 10）。**"))
        self.assertIn("| 场景 | 准备度 |", text)
        self.assertIn("机构面试更看重词汇表达，这是两者相差最大的原因。", text)

    def test_unknown_note_key_rejected(self):
        with self.assertRaises(ValueError):
            format_result({"profile": "sponsor_generic", "criteria": {}, "notes": {"accent": "x"}})


if __name__ == "__main__":
    unittest.main()
