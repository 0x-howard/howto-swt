#!/usr/bin/env python3
"""October 2026 student-facing output and dispatch regression checks."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from budget import calculate_position_overview, format_position_overview


def with_confirm(payload):
    return {**payload, "assumptions_confirmed": True}


def offer(name, wage=17):
    return {"id": name, "label": name, "state": "TX", "wage_usd_per_hour": wage,
            "expected_hours": 40, "work_weeks": 13, "rent_usd_per_week": 140,
            "food_usd_per_week": 80, "transport_usd_per_week": 0,
            "other_weekly_usd": 15, "project_cost_usd": 3300,
            "tax": {"federal_income_tax_percent": 10, "state_income_tax_percent": 0, "fica_percent": 0}}


def full_details():
    return {
        "tips": True,
        "meals": "none",
        "housing_deposit_usd": 0,
        "employer_transport": "none",
        "second_job_allowed": False,
        "ssn_required_before_work": False,
    }


class StudentOutputContractTests(unittest.TestCase):
    def test_single_offer_six_dim_two_finance_no_roi(self):
        text = format_position_overview(calculate_position_overview(with_confirm({"offers": [offer('A')]})))
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
        text = format_position_overview(calculate_position_overview(with_confirm({"offers": [offer('A'), offer('B', 18)]})))
        self.assertIn('岗位收益对比', text)
        self.assertIn('| 要素 | 项目 | A | B |', text)
        self.assertIn('| 项目 | A | B |', text)
        self.assertIn('| **最终预计结余** |', text)
        self.assertIn('| 回本进度 |', text)

    def test_four_offers_ask_core_goal_first(self):
        offers = [offer(str(i), 15 + i) for i in range(4)]
        text = format_position_overview(calculate_position_overview({"offers": offers}))
        self.assertIn('你的赴美核心诉求是什么', text)
        self.assertNotIn('六维分析', text)

    def test_min_hours_line(self):
        item = offer('A')
        item.update(min_hours=30, max_hours=40, expected_hours=35)
        text = format_position_overview(calculate_position_overview(with_confirm({"offers": [item]})))
        self.assertIn('按最低每周 30 小时计算，最终预计结余约', text)
        two = format_position_overview(calculate_position_overview(with_confirm({"offers": [item, offer('B')]})))
        self.assertIn('| 最低工时结余 |', two)
        self.assertIn('（30h/周） | — |', two)

    def test_new_detail_fields_are_validated(self):
        item = offer('A')
        item["details"] = {"amenities": ["超市", ""]}
        with self.assertRaises(ValueError):
            calculate_position_overview(with_confirm({"offers": [item]}))

    def test_full_checklist_skips_popup(self):
        item = offer("A")
        item["details"] = full_details()
        text = format_position_overview(calculate_position_overview({
            "offers": [item], "missing_confirmed": True,
        }))
        self.assertIn("六维分析", text)
        self.assertNotIn("确认住宿周租", text)
        self.assertNotIn("确认项目费", text)

    def test_each_missing_field_is_its_own_question(self):
        item = offer("A")
        del item["rent_usd_per_week"]
        # project fee on offer; soft details missing → many separate questions
        result = calculate_position_overview({"offers": [item]})
        self.assertEqual(result["stage"], "confirm_assumptions")
        ids = [q["id"] for q in result["assumption_form"]["questions"]]
        self.assertIn("rent_usd_per_week", ids)
        self.assertIn("tips", ids)
        self.assertIn("meals", ids)
        self.assertTrue(result["interaction"]["separate_questions"])
        self.assertEqual(len(result["interaction"]["questions"]), len(ids))
        text = format_position_overview(result)
        self.assertIn("问题 1", text)
        self.assertNotIn("已从材料读到", text)
        self.assertNotIn("六维分析", text)

    def test_missing_confirmed_skips_soft_but_asks_rent_or_fee(self):
        item = offer("A")
        del item["rent_usd_per_week"]
        del item["project_cost_usd"]
        result = calculate_position_overview({"offers": [item], "missing_confirmed": True})
        self.assertEqual(result["stage"], "confirm_assumptions")
        ids = [q["id"] for q in result["assumption_form"]["questions"]]
        self.assertEqual(ids, ["rent_usd_per_week", "project_fee"])
        text = format_position_overview(result)
        self.assertIn("确认住宿周租", text)
        self.assertIn("确认项目费", text)
        self.assertNotIn("确认小费", text)

    def test_hours_missing_becomes_its_own_question(self):
        item = offer("B")
        del item["expected_hours"]
        item["details"] = full_details()
        result = calculate_position_overview({"offers": [item], "missing_confirmed": True})
        self.assertEqual(result["stage"], "confirm_assumptions")
        ids = [q["id"] for q in result["assumption_form"]["questions"]]
        self.assertEqual(ids, ["hours_per_week"])
        done = format_position_overview(calculate_position_overview(with_confirm({
            "offers": [item], "missing_confirmed": True,
        })))
        self.assertIn("六维分析", done)

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
