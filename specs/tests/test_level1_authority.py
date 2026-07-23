from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "specs" / "tooling"))

from semantics import validate_semantics
from render import render_markdown


LEVEL_0 = ROOT / "specs" / "levels" / "level-0" / "GVE-LEVEL-0.json"
LEVEL_1 = ROOT / "specs" / "levels" / "level-1" / "GVE-LEVEL-1.json"
LEVEL_1_MD = ROOT / "specs" / "levels" / "level-1" / "GVE-LEVEL-1.md"


class Level1AuthorityTests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def definitions(self) -> dict[str, dict]:
        return {item["id"]: item for item in self.load(LEVEL_1)["definitions"]}

    def requirements(self) -> dict[str, dict]:
        return {item["id"]: item for item in self.load(LEVEL_1)["requirements"]}

    def relationships(self) -> dict[str, dict]:
        return {item["id"]: item for item in self.load(LEVEL_1)["relationships"]}

    def test_level_1_declares_level_0_parent(self) -> None:
        document = self.load(LEVEL_1)
        self.assertEqual(document["specification"]["id"], "GVE-LEVEL-1")
        self.assertEqual(document["specification"]["level"], 1)
        self.assertEqual(document["specification"]["parent"], "GVE-LEVEL-0")
        self.assertTrue(LEVEL_0.is_file())

    def test_level_1_semantics_are_valid(self) -> None:
        validate_semantics(self.load(LEVEL_1), LEVEL_1)

    def test_level_1_projection_is_synchronized(self) -> None:
        self.assertEqual(
            LEVEL_1_MD.read_text(encoding="utf-8"),
            render_markdown(self.load(LEVEL_1)),
        )

    def test_payload_represents_one_workflow(self) -> None:
        self.assertIn(
            "exactly one governed workflow",
            self.requirements()["L1-REQ-002"]["text"].lower(),
        )

    def test_workflow_contains_one_or_more_operations(self) -> None:
        self.assertIn(
            "one or more governed operations",
            self.requirements()["L1-REQ-003"]["text"].lower(),
        )

    def test_each_operation_has_exactly_one_plugin(self) -> None:
        text = self.requirements()["L1-REQ-004"]["text"].lower()
        self.assertIn("every governed operation", text)
        self.assertIn("exactly one selected application plugin", text)

    def test_workflow_may_use_multiple_plugins(self) -> None:
        text = self.requirements()["L1-REQ-004"]["text"].lower()
        self.assertIn("workflow may use one or more application plugins", text)
        self.assertIn("one plugin may be assigned to multiple operations", text)
        exclusions = " ".join(self.load(LEVEL_1)["scope"]["excludes"]).lower()
        self.assertNotIn("multi-plugin composition", exclusions)
        self.assertNotIn("cross-plugin sequencing", exclusions)

    def test_plugin_semantics_are_operation_scoped(self) -> None:
        text = self.requirements()["L1-REQ-007"]["text"].lower()
        self.assertIn(
            "only the operation-specific content of operations assigned to it",
            text,
        )
        self.assertIn(
            "no plugin may interpret an operation assigned to another plugin",
            text,
        )
        self.assertIn(
            "core must not interpret plugin-owned operation semantics",
            text,
        )

    def test_handoff_declaration_is_distinct_from_runtime_handoff(self) -> None:
        definitions = self.definitions()
        declaration = definitions["DATA-HANDOFF-DECLARATION"]["text"].lower()
        runtime = definitions["DATA-HANDOFF"]["text"].lower()
        self.assertIn("pre-execution contract", declaration)
        self.assertIn("source operation", declaration)
        self.assertIn("target operation", declaration)
        self.assertIn("runtime transfer of actual", runtime)
        self.assertIn("validated data-handoff declaration", runtime)
        self.assertNotEqual(declaration, runtime)

    def test_complete_workflow_validation_checks_handoff_declarations(self) -> None:
        text = self.requirements()["L1-REQ-008"]["text"].lower()
        self.assertIn("before any governed operation begins execution", text)
        self.assertIn("validate the complete workflow plan", text)
        self.assertIn("exactly one plugin assignment for every operation", text)
        self.assertIn("all declared dependencies", text)
        self.assertIn("every data-handoff declaration", text)
        self.assertNotIn("all declared dependencies and data handoffs", text)

    def test_invalid_handoff_declaration_blocks_workflow_execution(self) -> None:
        text = self.requirements()["L1-REQ-009"]["text"].lower()
        self.assertIn("data-handoff declaration", text)
        self.assertIn("fail closed before workflow execution begins", text)

    def test_runtime_handoff_is_validated_before_dependent_operation(self) -> None:
        text = self.requirements()["L1-REQ-010A"]["text"].lower()
        self.assertIn("before a dependent operation begins execution", text)
        self.assertIn("validate each actual data handoff", text)
        self.assertIn("against its validated data-handoff declaration", text)
        self.assertIn("must remain blocked or fail closed without being attempted", text)

    def test_validation_is_not_execution(self) -> None:
        text = self.requirements()["L1-REQ-010"]["text"].lower()
        for term in ("attempted", "completed", "observed", "verified"):
            self.assertIn(term, text)
        self.assertIn("by themselves", text)

    def test_level_0_effect_distinctions_apply_per_operation_and_workflow(self) -> None:
        text = self.requirements()["L1-REQ-013"]["text"].lower()
        for term in (
            "requested",
            "authorized",
            "attempted",
            "completed",
            "observed",
            "verified",
        ):
            self.assertIn(term, text)
        self.assertIn("for each operation and for the workflow as a whole", text)

    def test_assignment_success_does_not_imply_interpretation_success(self) -> None:
        text = self.requirements()["L1-REQ-014"]["text"].lower()
        self.assertIn(
            "whose plugin assignment succeeds",
            text,
        )
        self.assertIn(
            "when instruction interpretation succeeds",
            text,
        )
        self.assertIn(
            "when instruction interpretation fails",
            text,
        )
        self.assertIn(
            "without claiming that an instruction was successfully interpreted",
            text,
        )

    def test_results_report_assignment_and_interpretation_separately(self) -> None:
        text = self.requirements()["L1-REQ-014"]["text"].lower()
        self.assertIn("identify the operation and its assigned plugin", text)
        self.assertIn("identify the interpreted instructions", text)
        self.assertIn("identify the failure", text)

    def test_results_preserve_runtime_handoff_blocking(self) -> None:
        text = self.requirements()["L1-REQ-015"]["text"].lower()
        self.assertIn("runtime handoff validation blocks a dependent operation", text)
        self.assertIn("failed or unavailable handoff", text)
        self.assertIn("must not claim that the dependent operation was attempted", text)

    def test_results_preserve_validation_failure_and_partial_execution(self) -> None:
        text = self.requirements()["L1-REQ-015"]["text"].lower()
        self.assertIn("without claiming that workflow execution began", text)
        for term in ("completed", "failed", "blocked", "skipped", "unattempted"):
            self.assertIn(term, text)
        self.assertIn("must not report the whole workflow as completed", text)

    def test_handoff_relationships_are_explicit(self) -> None:
        relationships = self.relationships()
        self.assertEqual(
            relationships["L1-REL-017"],
            {
                "id": "L1-REL-017",
                "source": "WORKFLOW-PLAN",
                "relation": "declares",
                "target": "DATA-HANDOFF-DECLARATION",
            },
        )
        self.assertEqual(
            relationships["L1-REL-018"],
            {
                "id": "L1-REL-018",
                "source": "DATA-HANDOFF-DECLARATION",
                "relation": "governs",
                "target": "DATA-HANDOFF",
            },
        )

    def test_level_1_keeps_concrete_mechanics_out_of_scope(self) -> None:
        text = self.requirements()["L1-REQ-016"]["text"].lower()
        for term in (
            "concrete workflow schema",
            "operation serialization format",
            "dependency-graph representation",
            "handoff serialization format",
            "plugin api",
            "registry implementation",
            "rollback mechanism",
        ):
            self.assertIn(term, text)

    def test_root_level_1_has_been_removed(self) -> None:
        self.assertFalse((ROOT / "LEVEL_1.md").exists())


if __name__ == "__main__":
    unittest.main()
