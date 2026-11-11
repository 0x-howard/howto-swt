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
        self.assertTrue(text.startswith('**本岗位预计可以回本：'))
        self.assertIn('影响回本的关键因素：', text)
        self.assertIn('| 要素 | 内容 | 注意事项 |', text)
        self.assertIn('| 项目 | 金额 |', text)
        self.assertNotIn('岗位收益对比', text)
        self.assertIn('**后续选项**', text)
        self.assertTrue(text.endswith('回复字母或直接提问。'))
        for forbidden in ('口径：', '核验口径', '税费规划预留', '要注意', '问我就展开', '## '):
            self.assertNotIn(forbidden, text)

    def test_two_offers_show_roi(self):
        text = format_position_overview(calculate_position_overview({"offers": [offer('A'), offer('B', 18)]}))
        self.assertIn('岗位收益对比', text)
        self.assertIn('| 要素 | A | B |', text)
        self.assertIn('影响选择的关键因素：', text)
        self.assertIn('| **最终预计结余** |', text)

    def test_four_offers_compare_first_without_forced_picker(self):
        text = format_position_overview(calculate_position_overview({"offers": [offer(str(i), 15 + i) for i in range(4)]}))
        self.assertIn('| 要素 | 0 | 1 | 2 | 3 |', text)
        self.assertNotIn('回复编号即可', text)
        self.assertNotIn('岗位收益对比', text)

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
