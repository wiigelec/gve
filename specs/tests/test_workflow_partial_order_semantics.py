"""Acceptance tests for deterministic workflow partial-order semantics."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEVEL_2 = ROOT / "levels" / "level-2" / "GVE-LEVEL-2-WORKFLOW-COMPOSITION.json"
LEVEL_3 = ROOT / "levels" / "level-3" / "GVE-LEVEL-3-WORKFLOW-PLANNING-LIFECYCLE.json"


def _document(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _definition(document: dict, identifier: str) -> str:
    return next(
        item["text"] for item in document["definitions"] if item["id"] == identifier
    )


def _requirement(document: dict, identifier: str) -> str:
    return next(
        item["text"] for item in document["requirements"] if item["id"] == identifier
    )


class WorkflowPartialOrderSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.level_2 = _document(LEVEL_2)
        self.level_3 = _document(LEVEL_3)

    def test_level_2_defines_plan_order_as_partial_order(self) -> None:
        text = _definition(self.level_2, "L2-WC-ORDERING-CONSTRAINT").lower()
        self.assertIn("partial order", text)
        self.assertIn("predecessor", text)
        self.assertIn("successor", text)
        self.assertNotIn("deterministic operation order", text)

    def test_level_2_accepts_independent_operations(self) -> None:
        text = _requirement(self.level_2, "L2-WC-REQ-009").lower()
        self.assertIn("acyclic partial order", text)
        self.assertIn("independent operations", text)
        self.assertIn("multiple topological serializations", text)
        self.assertNotIn("multiple unresolved valid orders", text)

    def test_level_2_rejects_invalid_constraint_meaning(self) -> None:
        text = _requirement(self.level_2, "L2-WC-REQ-009").lower()
        for phrase in (
            "cycles",
            "contradictory",
            "unresolved operation",
            "ambiguous constraint",
        ):
            self.assertIn(phrase, text)

    def test_level_2_plan_identity_is_declaration_order_independent(self) -> None:
        text = _requirement(self.level_2, "L2-WC-REQ-013").lower()
        self.assertIn("partial-order", text)
        self.assertIn("declaration order", text)
        self.assertIn("topological serialization", text)

    def test_level_3_plan_acceptance_uses_partial_order(self) -> None:
        text = _requirement(self.level_3, "L3-WPL-REQ-004").lower()
        self.assertIn("acyclic partial order", text)
        self.assertIn("independent operations", text)
        self.assertNotIn("duplicate positions", text)
        self.assertNotIn("multiple unresolved valid orders", text)

    def test_level_3_separates_scheduler_choice_from_plan_meaning(self) -> None:
        text = _requirement(self.level_3, "L3-WPL-REQ-010").lower()
        self.assertIn("scheduler", text)
        self.assertIn("topological serialization", text)
        self.assertIn("must not alter", text)
        self.assertIn("accepted-plan", text)

    def test_level_3_does_not_define_unique_attempt_start_order(self) -> None:
        text = _definition(self.level_3, "L3-WPL-ATTEMPT-ORDER").lower()
        self.assertNotIn("uniquely determined order", text)
        self.assertIn("eligible", text)
        self.assertIn("partial order", text)


if __name__ == "__main__":
    unittest.main()
