#!/usr/bin/env python3

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from orchestration import (  # noqa: E402
    EXECUTOR_STATES,
    choose_routing_mode,
    effective_facts,
    validate_handoff,
    validate_transition,
)


def handoff(executor="swt-position", state="INTAKE"):
    return {
        "handoff_version": "1.0",
        "router": "swt",
        "executor": executor,
        "intent": "DECISION",
        "user_goal": "compare offers",
        "known_facts": {"sponsor": "Old Sponsor", "season": 2027},
        "changed_facts": {"sponsor": "CIEE"},
        "missing_critical_facts": [],
        "constraints": ["do not invent offer terms"],
        "requested_output": "decision and next action",
        "state": state,
    }


class OrchestrationContractTests(unittest.TestCase):
    def test_five_clear_tasks_are_direct(self):
        for executor in EXECUTOR_STATES:
            with self.subTest(executor=executor):
                self.assertEqual(choose_routing_mode([executor]), "DIRECT")

    def test_multiple_routes_require_confirmation(self):
        self.assertEqual(choose_routing_mode(["swt-application", "swt-position"]), "CONFIRM")

    def test_missing_route_fact_requires_minimal_clarification(self):
        self.assertEqual(choose_routing_mode([], ["task_object"]), "CLARIFY")
        self.assertEqual(choose_routing_mode(["swt-position"], ["is_offer_or_application_status"]), "CLARIFY")

    def test_changed_facts_override_known_facts_without_mutation(self):
        value = handoff()
        merged = effective_facts(value)
        self.assertEqual(merged["sponsor"], "CIEE")
        self.assertEqual(merged["season"], 2027)
        self.assertEqual(value["known_facts"]["sponsor"], "Old Sponsor")

    def test_known_context_is_not_requested_again(self):
        value = handoff()
        value["missing_critical_facts"] = ["sponsor"]
        with self.assertRaisesRegex(ValueError, "known fact"):
            validate_handoff(value)

    def test_executor_cannot_accept_another_executors_state(self):
        value = handoff("swt-position", "FACT_EXTRACTION")
        with self.assertRaisesRegex(ValueError, "selected executor"):
            validate_handoff(value)

    def test_valid_handoff_and_forward_or_same_state_transitions(self):
        value = handoff()
        validate_handoff(value)
        validate_transition("swt-position", "INTAKE", "NORMALIZE")
        validate_transition("swt-position", "ANALYZE", "ANALYZE")

    def test_backward_transition_requires_changed_facts(self):
        with self.assertRaisesRegex(ValueError, "changed facts"):
            validate_transition("swt-position", "DECISION", "NORMALIZE")
        validate_transition("swt-position", "DECISION", "NORMALIZE", facts_changed=True)

    def test_cross_executor_transition_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "one Executor"):
            validate_transition("swt-visa", "FACT_EXTRACTION", "BUDGET")

    def test_router_stays_compact_and_delegates_domain_logic(self):
        router = (ROOT / "skills/swt/SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(router.splitlines()), 90)
        self.assertIn("不在本 Skill 里重复岗位、英语、签证、申请或抵美业务逻辑", router)


if __name__ == "__main__":
    unittest.main()
