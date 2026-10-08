#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from interaction import adapt_request, interaction_request, offer_selection_request, plan_interaction, render_fallback, validate_selection  # noqa: E402


def option(identifier, label=None):
    return {"id": identifier, "label": label or identifier.title(), "description": f"choose {identifier}"}


def capabilities(host, interface=None, **enabled):
    result = {
        "host": host, "native_interface": interface,
        "supports_single_choice": False, "supports_multi_choice": False,
        "supports_free_text": False, "supports_structured_form": False,
        "supports_confirmation": False,
    }
    result.update(enabled)
    return result


class InteractionContractTests(unittest.TestCase):
    def setUp(self):
        self.single = interaction_request(
            "single_choice", "next", "先做什么？", options=[option("position"), option("visa")],
            min_selections=1, max_selections=1, allow_other=True,
        )

    def test_direct_never_prompts(self):
        self.assertEqual(plan_interaction("DIRECT", None, None), {"action": "direct", "request": None})

    def test_confirm_uses_choice(self):
        self.assertEqual(plan_interaction("CONFIRM", None, self.single)["action"], "interact")

    def test_enum_clarify_uses_choice(self):
        self.assertEqual(plan_interaction("CLARIFY", "enum", self.single)["request"]["type"], "single_choice")

    def test_free_text_clarify_does_not_force_choice(self):
        request = interaction_request("free_text", "employer", "雇主名称是什么？")
        self.assertEqual(plan_interaction("CLARIFY", "free_text", request)["request"]["type"], "free_text")

    def test_known_context_is_not_requested_again(self):
        result = plan_interaction("CLARIFY", "enum", self.single, fact_key="current_stage", confirmed_context_keys=["current_stage"])
        self.assertEqual(result["action"], "direct")

    def test_single_choice_and_other(self):
        self.assertEqual(validate_selection(self.single, ["visa"])["status"], "accepted")
        self.assertEqual(validate_selection(self.single, other_text="别的事项")["status"], "accepted_other")

    def test_multi_choice(self):
        request = interaction_request("multi_choice", "offers", "选岗位", options=[option("a"), option("b"), option("c")], min_selections=1, max_selections=2)
        self.assertEqual(validate_selection(request, ["a", "c"])["selected_ids"], ["a", "c"])

    def test_sensitive_confirmation(self):
        request = interaction_request("confirmation", "edition_replace", "确认切换 Edition？", options=[option("continue", "继续"), option("cancel", "取消")], min_selections=1, max_selections=1, sensitive_confirmation=True)
        self.assertTrue(request["sensitive_confirmation"])
        self.assertIn("1. 继续", render_fallback(request))
        self.assertIn("2. 取消", render_fallback(request))

    def test_recommended_requires_basis(self):
        request = interaction_request("single_choice", "next", "下一步？", options=[option("a"), option("b")], min_selections=1, max_selections=1, recommended_option_id="a", recommendation_basis="已确认当前阶段")
        self.assertIn("A（推荐）", render_fallback(request))
        with self.assertRaisesRegex(ValueError, "evidence basis"):
            interaction_request("single_choice", "bad", "下一步？", options=[option("a"), option("b")], min_selections=1, max_selections=1, recommended_option_id="a")

    def test_no_ui_uses_numbered_fallback(self):
        delivery = adapt_request(self.single, capabilities("doubao-work"))
        self.assertEqual(delivery["delivery"], "text_fallback")
        self.assertIn("回复数字即可", delivery["text"])

    def test_user_cancel_and_invalid_selection(self):
        self.assertEqual(validate_selection(self.single, cancelled=True)["status"], "cancelled")
        with self.assertRaisesRegex(ValueError, "invalid selection"):
            validate_selection(self.single, ["unknown"])

    def test_offer_roi_exception_allows_more_than_four_options(self):
        functions = [{"id": char, "label": f"Offer {char}", "expected_weekly_net_surplus_usd": "100.00"} for char in "ABCDE"]
        request = offer_selection_request(functions)
        self.assertEqual(len(request["options"]), 5)
        self.assertEqual(request["max_selections"], 3)

    def test_four_host_adapter_capability_mappings_are_contract_tested(self):
        cases = {
            "codex": capabilities("codex", "request_user_input", supports_single_choice=True),
            "claude-code": capabilities("claude-code", "AskUserQuestion", supports_single_choice=True),
            "workbuddy": capabilities("workbuddy", "AskUserQuestion", supports_single_choice=True),
            "doubao-work": capabilities("doubao-work"),
        }
        self.assertEqual(adapt_request(self.single, cases["codex"])["delivery"], "native")
        self.assertEqual(adapt_request(self.single, cases["claude-code"])["interface"], "AskUserQuestion")
        self.assertEqual(adapt_request(self.single, cases["workbuddy"])["interface"], "AskUserQuestion")
        self.assertEqual(adapt_request(self.single, cases["doubao-work"])["delivery"], "text_fallback")

    def test_each_capability_flag_controls_native_delivery(self):
        requests = {
            "multi_choice": interaction_request("multi_choice", "m", "多选", options=[option("a"), option("b")], min_selections=1, max_selections=2),
            "free_text": interaction_request("free_text", "f", "填写"),
            "structured_form": interaction_request("structured_form", "s", "表单", fields=[{"id": "hours", "label": "每周工时", "required": True}]),
            "confirmation": interaction_request("confirmation", "c", "确认", options=[option("yes"), option("no")], min_selections=1, max_selections=1),
        }
        mapping = {
            "multi_choice": "supports_multi_choice", "free_text": "supports_free_text",
            "structured_form": "supports_structured_form", "confirmation": "supports_confirmation",
        }
        for kind, request in requests.items():
            with self.subTest(kind=kind):
                self.assertEqual(adapt_request(request, capabilities("host"))["delivery"], "text_fallback")
                self.assertEqual(adapt_request(request, capabilities("host", "native", **{mapping[kind]: True}))["delivery"], "native")

    def test_cross_executor_continuation_uses_one_semantic_request(self):
        request = interaction_request(
            "single_choice", "next_executor", "接下来处理哪项？",
            options=[option("swt-position"), option("swt-visa"), option("swt-arrival")],
            min_selections=1, max_selections=1,
        )
        self.assertEqual(validate_selection(request, ["swt-visa"])["selected_ids"], ["swt-visa"])

    def test_runtime_evidence_record_distinguishes_live_from_static(self):
        record = (ROOT / "references/interaction-adapters.md").read_text(encoding="utf-8")
        self.assertIn("Current-session tool inventory verified", record)
        self.assertIn("Installed-runtime static evidence; not live E2E", record)
        self.assertIn("Contract/static reference only", record)
        self.assertIn("Unverified live UI; contract only", record)


if __name__ == "__main__":
    unittest.main()
