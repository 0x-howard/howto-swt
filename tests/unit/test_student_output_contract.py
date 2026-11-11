#!/usr/bin/env python3
"""October 2026 student-facing output and dispatch regression checks."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from budget import calculate_position_overview, format_position_overview


def offer(name, wage=17):
    return {"id": name, "label": name, "state": "TX", "wage_usd_per_hour": wage,
            "expected_hours": 40, "work_weeks": 13, "rent_usd_per_week": 140,
            "food_usd_per_week": 80, "transport_usd_per_week": 0,
            "other_weekly_usd": 15, "project_cost_usd": 3300,
            "tax": {"federal_income_tax_percent": 10, "state_income_tax_percent": 0, "fica_percent": 0}}


class StudentOutputContractTests(unittest.TestCase):
    def test_single_offer_six_dim_two_finance_no_roi(self):
        text = format_position_overview(calculate_position_overview({"offers": [offer('A')]}))
        self.assertTrue(text.startswith('**项目费 $3,300，按 $17/h'))
        self.assertIn('预计可以回本。**', text.splitlines()[0])
        self.assertIn('## 1. 六维分析', text)
        self.assertIn('| 要素 | Offer 数据 | 分析 |', text)
        self.assertIn('## 2. 回本测算', text)
        self.assertIn('| 项目 | 每周 | 13 周合计 |', text)
        self.assertIn('回本进度：', text)
        self.assertNotIn('岗位收益对比', text)
        self.assertIn('## 3. 特殊注意事项', text)
        self.assertIn('## 4. 后续选项', text)
        self.assertTrue(text.endswith('回复字母或直接提问。'))
        for forbidden in ('口径：', '核验口径', '税费规划预留', '要注意', '问我就展开', '关键因素'):
            self.assertNotIn(forbidden, text)

    def test_two_offers_show_roi(self):
        text = format_position_overview(calculate_position_overview({"offers": [offer('A'), offer('B', 18)]}))
        self.assertIn('岗位收益对比', text)
        self.assertIn('| 要素 | 项目 | A | B |', text)
        self.assertIn('| 项目 | A | B |', text)
        self.assertIn('| **最终预计结余** |', text)
        self.assertIn('| 回本进度 |', text)

    def test_four_offers_ask_core_goal_first(self):
        offers = [offer(str(i), 15 + i) for i in range(4)]
        text = format_position_overview(calculate_position_overview({"offers": offers}))
        self.assertIn('比较前先确认：你的赴美核心诉求是什么？', text)
        self.assertIn('A. 多赚钱，尽快回本', text)
        self.assertNotIn('六维分析', text)

    def test_four_offers_money_goal_compares_top_three(self):
        offers = [offer(str(i), 15 + i) for i in range(4)]
        text = format_position_overview(calculate_position_overview({"offers": offers, "core_goal": "money"}))
        self.assertTrue(text.startswith('按你的核心诉求（多赚钱，尽快回本），从 4 份岗位中选出以下 3 份深入对比；其余：0（'))
        self.assertIn('| 要素 | 项目 | 3 | 2 | 1 |', text)
        self.assertIn('岗位收益对比', text)

    def test_four_offers_experience_goal_asks_selection_then_compares(self):
        offers = [offer(str(i), 15 + i) for i in range(4)]
        ask = format_position_overview(calculate_position_overview({"offers": offers, "core_goal": "experience"}))
        self.assertIn('请从下面 4 份岗位中选 3 份深入对比', ask)
        self.assertTrue(ask.endswith('回复 3 个编号。'))
        text = format_position_overview(calculate_position_overview(
            {"offers": offers, "core_goal": "experience", "selected_offer_ids": [1, 2, 4]}))
        self.assertIn('| 要素 | 项目 | 0 | 1 | 3 |', text)
        self.assertIn('**三份岗位共同**', text)
        with self.assertRaises(ValueError):
            calculate_position_overview({"offers": offers, "selected_offer_ids": [1, 1]})
        with self.assertRaises(ValueError):
            calculate_position_overview({"offers": offers, "core_goal": "fun"})

    def test_direct_skill_contract(self):
        router = (ROOT / 'skills/swt/SKILL.md').read_text(encoding='utf-8')
        handoff = (ROOT / 'shared/handoff-contract.md').read_text(encoding='utf-8')
        self.assertIn('直接交给对应 Skill 执行', router)
        self.assertIn('fallback only', handoff)
        stage = (ROOT / 'shared/stage-model.md').read_text(encoding='utf-8')
        self.assertIn('归国收尾', stage)
        self.assertIn('学员可见的八个阶段', stage)


if __name__ == '__main__':
    unittest.main()
