from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs"
RUNTIME_JSON = (
    SPECS
    / "levels"
    / "level-3"
    / "GVE-LEVEL-3-RUNTIME-OWNERSHIP.json"
)
RUNTIME_MARKDOWN = RUNTIME_JSON.with_suffix(".md")


class LevelThreeRuntimeOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = load_strict(RUNTIME_JSON)
        cls.definitions = {
            item["id"]: item["text"] for item in cls.document["definitions"]
        }
        cls.requirements = {
            item["id"]: item["text"] for item in cls.document["requirements"]
        }

    def test_identity_parentage_root_and_imports(self) -> None:
        self.assertEqual(
            self.document["specification"],
            {
                "id": "GVE-LEVEL-3-RUNTIME-OWNERSHIP",
                "level": 3,
                "title": "GVE Level 3 Runtime Ownership",
                "version": "1.0.0",
                "status": "normative",
                "parent": "GVE-LEVEL-3",
            },
        )
        self.assertEqual(
            self.document["document"],
            {
                "role": "subordinate",
                "root": "GVE-LEVEL-3",
                "imports": ["GVE-LEVEL-3"],
            },
        )

    def test_runtime_component_responsibilities_are_complete(self) -> None:
        expected = {
            "L3-RO-COMMON-ENVELOPE-LOADER",
            "L3-RO-WORKFLOW-REPRESENTATION",
            "L3-RO-OPERATION-REPRESENTATION",
            "L3-RO-CORE-ORCHESTRATOR",
            "L3-RO-PLUGIN-REGISTRY-OWNER",
            "L3-RO-PLUGIN-INTERFACE-BOUNDARY",
            "L3-RO-ACTION-REGISTRY-OWNER",
            "L3-RO-ACTION-INTERFACE-BOUNDARY",
            "L3-RO-EXECUTION-CONTEXT",
            "L3-RO-COMMON-RUNTIME-FACILITIES",
            "L3-RO-IMMUTABLE-RUNTIME-SNAPSHOT",
            "L3-RO-ACTION-MODULE-BOUNDARY",
        }
        self.assertTrue(expected <= set(self.definitions))

    def test_core_plugin_and_action_ownership_remain_separate(self) -> None:
        core = self.requirements["L3-RO-REQ-003"]
        plugin_registry = self.requirements["L3-RO-REQ-005"]
        action = self.requirements["L3-RO-REQ-006"]

        self.assertIn("application-independent", core)
        self.assertIn("must not interpret", core)
        self.assertIn("plugin-owned action or input meaning", core)

        self.assertIn("Each plugin must own exactly one action registry", plugin_registry)
        self.assertIn("rather than directly with the core", plugin_registry)

        self.assertIn("Each action must retain ownership", action)
        self.assertIn("semantic interpretation", action)
        self.assertIn("governed execution behavior", action)

    def test_action_implementation_boundary_is_localized(self) -> None:
        addition = self.requirements["L3-RO-REQ-012"]
        change = self.requirements["L3-RO-REQ-013"]

        self.assertIn("independently identifiable implementation module", addition)
        self.assertIn("without core modification", addition)
        self.assertIn("unrelated action implementations", addition)

        self.assertIn("localized to that action module", change)
        self.assertIn("shared contracts", change)
        self.assertIn("separately identifiable", change)

    def test_runtime_identity_and_snapshot_rules_fail_closed(self) -> None:
        identity = self.requirements["L3-RO-REQ-008"]
        snapshot = self.requirements["L3-RO-REQ-009"]

        for condition in (
            "missing",
            "duplicate",
            "conflicting",
            "ambiguous",
            "stale",
            "incompatible",
            "mutated",
        ):
            self.assertIn(condition, identity)
        self.assertIn("must fail closed", identity)

        self.assertIn("immutable runtime snapshots", snapshot)
        self.assertIn("late registration", snapshot)
        self.assertIn("registry drift", snapshot)

    def test_sibling_responsibilities_are_explicitly_excluded(self) -> None:
        exclusion = self.requirements["L3-RO-REQ-015"]
        for phrase in (
            "validated-operation-contract production",
            "workflow-plan state transitions",
            "dependency or handoff eligibility",
            "evidence schemas",
            "operation-result schemas",
            "authoritative workflow-result assembly",
        ):
            self.assertIn(phrase, exclusion)

        scope = set(self.document["scope"]["excludes"])
        self.assertTrue(
            any("validated-operation-contract production" in item for item in scope)
        )
        self.assertTrue(
            any("Workflow resolution" in item for item in scope)
        )
        self.assertTrue(
            any("Evidence schemas" in item for item in scope)
        )

    def test_namespace_is_stable_and_distinct(self) -> None:
        definition_ids = set(self.definitions)
        requirement_ids = set(self.requirements)
        relationship_ids = {
            item["id"] for item in self.document["relationships"]
        }

        self.assertTrue(
            all(identifier.startswith("L3-RO-") for identifier in definition_ids)
        )
        self.assertTrue(
            all(identifier.startswith("L3-RO-REQ-") for identifier in requirement_ids)
        )
        self.assertTrue(
            all(identifier.startswith("L3-RO-REL-") for identifier in relationship_ids)
        )
        self.assertTrue(definition_ids.isdisjoint(requirement_ids))
        self.assertTrue(definition_ids.isdisjoint(relationship_ids))
        self.assertTrue(requirement_ids.isdisjoint(relationship_ids))

    def test_markdown_is_exact_projection(self) -> None:
        self.assertEqual(
            RUNTIME_MARKDOWN.read_text(encoding="utf-8"),
            render_markdown(self.document),
        )

    def test_repository_specification_validation_passes(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "specs.tooling.validate",
                "--specs-root",
                str(SPECS),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("specification validation passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
