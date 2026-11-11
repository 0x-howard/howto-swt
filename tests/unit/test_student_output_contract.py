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

    def test_experience_goal_ranks_by_travel_facts(self):
        offers = [offer(str(i), 15 + i) for i in range(4)]
        offers[0]["details"] = {"nearest_city": "Boston", "nearest_city_hours": 2, "days_per_week": 5}
        offers[1]["details"] = {"nearest_city": "Denver", "nearest_city_hours": 6, "days_per_week": 6}
        offers[2]["details"] = {"nearest_city": "Seattle", "nearest_city_hours": 3, "days_per_week": 6}
        text = format_position_overview(calculate_position_overview({"offers": offers, "core_goal": "experience", "missing_confirmed": True}))
        self.assertIn('| 要素 | 项目 | 0 | 2 | 3 |', text)
        self.assertIn('按你的诉求（旅行与体验），0 最匹配：距 Boston 约 2 小时、周末可往返大城市、每周上班约 5 天。', text)
        self.assertIn('- **距大城市**：0 更近，距 Boston 约 2 小时。', text)
        self.assertIn('- **上班天数**：0 每周少上 1 天。', text)
        self.assertLess(text.index('**距大城市**'), text.index('**时薪**'))

    def test_english_goal_orders_notes_and_names_fit(self):
        a, b = offer('A'), offer('B', 18)
        a["details"] = {"customer_facing": True, "english_level": "Advanced", "cultural_activities": "雇主组织周末出游。"}
        b["details"] = {"customer_facing": False, "tips": True}
        text = format_position_overview(calculate_position_overview({"offers": [a, b], "core_goal": "english", "missing_confirmed": True}))
        self.assertIn('按你的诉求（提升英语与文化交流），A 最匹配：面向顾客、日常用英语沟通、英语要求 Advanced、有文化交流活动。', text)
        self.assertIn('- **面向顾客**：A 面向顾客，B 以后台工作为主。', text)
        self.assertIn('- **工作英语环境**：岗位面向顾客，日常用英语沟通；雇主要求英语 Advanced。', text)
        notes = text[text.index('**B**'):]
        self.assertLess(notes.index('工作英语环境'), notes.index('小费'))

    def test_minimum_hours_surplus_when_range_given(self):
        item = offer('A')
        item.update(min_hours=30, max_hours=40, expected_hours=35)
        text = format_position_overview(calculate_position_overview({"offers": [item]}))
        self.assertIn('按最低每周 30 小时计算，最终预计结余约', text)
        two = format_position_overview(calculate_position_overview({"offers": [item, offer('B')]}))
        self.assertIn('| 最低工时结余 |', two)
        self.assertIn('（30h/周） | — |', two)

    def test_new_detail_fields_are_validated(self):
        item = offer('A')
        item["details"] = {"amenities": ["超市", ""]}
        with self.assertRaises(ValueError):
            calculate_position_overview({"offers": [item]})

    def test_missing_offer_fields_are_asked_before_analysis(self):
        item = offer('A')
        item["details"] = {"tips": True}
        text = format_position_overview(calculate_position_overview({"offers": [item]}))
        self.assertTrue(text.startswith('我这里检测不到以下信息，麻烦你看一遍 Offer 提供给我：'))
        self.assertIn('- 餐饮安排（Meals）', text)
        self.assertIn('- 住宿押金（Deposit amount）', text)
        self.assertNotIn('小费（Tips）', text)
        self.assertNotIn('六维分析', text)
        self.assertTrue(text.endswith('Offer 上确实没写的，回复「没写」，我按估算继续。'))
        confirmed = format_position_overview(calculate_position_overview({"offers": [item], "missing_confirmed": True}))
        self.assertIn('## 1. 六维分析', confirmed)
        typed = offer('B')
        del typed["expected_hours"]
        asked = format_position_overview(calculate_position_overview({"offers": [typed], "missing_confirmed": True}))
        self.assertIn('- 每周工时（Estimated hours per week）', asked)

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
