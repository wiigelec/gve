from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs"
CONTRACTS_JSON = (
    SPECS
    / "levels"
    / "level-3"
    / "GVE-LEVEL-3-PLUGIN-ACTION-CONTRACTS.json"
)
CONTRACTS_MARKDOWN = CONTRACTS_JSON.with_suffix(".md")


class LevelThreePluginActionContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = load_strict(CONTRACTS_JSON)
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
                "id": "GVE-LEVEL-3-PLUGIN-ACTION-CONTRACTS",
                "level": 3,
                "title": "GVE Level 3 Plugin and Action Contracts",
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
                "imports": [
                    "GVE-LEVEL-3",
                    "GVE-LEVEL-3-RUNTIME-OWNERSHIP",
                ],
            },
        )

    def test_contract_and_registry_definitions_are_complete(self) -> None:
        expected = {
            "L3-PAC-COMMON-PLUGIN-CONTRACT",
            "L3-PAC-COMMON-ACTION-CONTRACT",
            "L3-PAC-PLUGIN-REGISTRATION",
            "L3-PAC-ACTION-REGISTRATION",
            "L3-PAC-PLUGIN-RESOLUTION",
            "L3-PAC-ACTION-RESOLUTION",
            "L3-PAC-DECLARED-INPUT-CONTRACT",
            "L3-PAC-STRUCTURAL-INPUT-CONFORMANCE",
            "L3-PAC-ACTION-INTERPRETATION",
            "L3-PAC-VALIDATED-OPERATION-CONTRACT",
            "L3-PAC-CONTRACT-FRESHNESS",
            "L3-PAC-REGISTRY-VALIDATION",
            "L3-PAC-SEALED-REGISTRY-SNAPSHOT",
            "L3-PAC-CONTRACT-ATTRIBUTION",
        }
        self.assertTrue(expected <= set(self.definitions))

    def test_registration_ownership_and_resolution_order(self) -> None:
        plugin = self.requirements["L3-PAC-REQ-002"]
        action = self.requirements["L3-PAC-REQ-003"]
        order = self.requirements["L3-PAC-REQ-004"]

        self.assertIn("core-owned plugin registry", plugin)
        self.assertIn("at most one compatible registered plugin", plugin)

        self.assertIn("exactly one owning plugin's action registry", action)
        self.assertIn("must not register directly with the core", action)

        self.assertIn("plugin resolution before action resolution", order)
        self.assertIn("only the selected plugin may resolve", order)
        self.assertIn("sealed action-registry snapshot", order)

    def test_action_owns_inputs_and_semantic_interpretation(self) -> None:
        core = self.requirements["L3-PAC-REQ-005"]
        action = self.requirements["L3-PAC-REQ-006"]
        structural = self.requirements["L3-PAC-REQ-007"]

        self.assertIn("must not interpret", core)
        self.assertIn("plugin-owned action or input meaning", core)

        self.assertIn("one complete declared input contract", action)
        self.assertIn("authoritative application-specific interpretation", action)

        self.assertIn("before action interpretation", structural)
        self.assertIn("must fail closed", structural)
        self.assertIn("without inventing action-specific meaning", structural)

    def test_validated_contract_is_exactly_one_fresh_and_attributable(self) -> None:
        production = self.requirements["L3-PAC-REQ-008"]
        binding = self.requirements["L3-PAC-REQ-009"]
        freshness = self.requirements["L3-PAC-REQ-010"]

        self.assertIn("exactly one", production)
        self.assertIn("fresh, valid, immutable", production)
        self.assertIn("uniquely attributable", production)
        self.assertIn("zero contracts", production)
        self.assertIn("multiple contracts", production)
        self.assertIn("reused contracts", production)

        for phrase in (
            "workflow identity",
            "operation identity",
            "plugin identity",
            "action identity",
            "plugin-interface version",
            "action-interface version",
            "plugin-registry snapshot identity",
            "action-registry snapshot identity",
            "governing authority",
            "complete interpreted inputs",
        ):
            self.assertIn(phrase, binding)

        self.assertIn("invalidate the prior contract", freshness)
        self.assertIn("require fresh production", freshness)

    def test_registry_validation_sealing_and_fail_closed_conditions(self) -> None:
        sealing = self.requirements["L3-PAC-REQ-011"]
        failures = self.requirements["L3-PAC-REQ-012"]
        contract_failures = self.requirements["L3-PAC-REQ-013"]

        for phrase in (
            "complete",
            "validated",
            "deterministic",
            "sealed",
            "uniquely identified",
            "immutable",
        ):
            self.assertIn(phrase, sealing)

        for phrase in (
            "Duplicate registration",
            "late registration",
            "unavailable identity",
            "unauthorized registration",
            "conflicting ownership",
            "ambiguous resolution",
            "identity mutation",
            "incompatible interface version",
            "incomplete registry validation",
            "registry snapshot drift",
        ):
            self.assertIn(phrase, failures)
        self.assertIn("must fail closed", failures)

        for phrase in (
            "missing",
            "malformed",
            "unauthorized",
            "stale",
            "incompatible",
            "conflicting",
            "duplicate",
            "incomplete",
            "non-uniquely attributable",
        ):
            self.assertIn(phrase, contract_failures)
        self.assertIn("must not be repaired by inference", contract_failures)

    def test_action_addition_remains_localized(self) -> None:
        requirement = self.requirements["L3-PAC-REQ-014"]
        self.assertIn("independently identifiable source module", requirement)
        self.assertIn("one explicit registration entry", requirement)
        self.assertIn("must not require core modification", requirement)
        self.assertIn("unrelated action implementations", requirement)

    def test_sibling_responsibilities_are_explicitly_excluded(self) -> None:
        status = self.requirements["L3-PAC-REQ-015"]
        exclusion = self.requirements["L3-PAC-REQ-016"]

        for phrase in (
            "no workflow-plan acceptance",
            "operation eligibility",
            "attempt",
            "completion",
            "observation",
            "verification",
            "effect",
            "evidence sufficiency",
            "authoritative result claim",
        ):
            self.assertIn(phrase, status)

        for phrase in (
            "workflow-plan states",
            "dependency or handoff eligibility",
            "attempt ordering",
            "blocking",
            "skipping",
            "cancellation",
            "timeout",
            "lifecycle transitions",
            "evidence schemas",
            "operation-result schemas",
            "authoritative workflow-result assembly",
        ):
            self.assertIn(phrase, exclusion)


    def test_contract_production_ordinal_allocator_is_explicit(self) -> None:
        definition = self.definitions[
            "L3-PAC-CONTRACT-PRODUCTION-ORDINAL-ALLOCATOR"
        ]
        authority = self.requirements["L3-PAC-REQ-021"]
        behavior = self.requirements["L3-PAC-REQ-022"]
        failures = self.requirements["L3-PAC-REQ-023"]

        self.assertIn("selected action", definition)
        self.assertIn("sole authority", definition)
        self.assertIn("plan-candidate-and-operation production lineage", definition)
        self.assertIn("least unused ordinal", definition)

        self.assertIn("sole contract-production ordinal allocator", authority)
        self.assertIn("plan-candidate identity and operation identity", authority)
        self.assertIn("nonnegative signed-64-bit ordinal", authority)

        self.assertIn("first contract production must receive ordinal zero", behavior)
        self.assertIn("Exact replay must retain the prior ordinal", behavior)
        self.assertIn("Regeneration must receive the least nonnegative ordinal", behavior)

        self.assertIn("must not yield the same new ordinal", failures)
        self.assertIn("reused-as-new ordinal", failures)
        self.assertIn("exhausted domain", failures)
        self.assertIn("must fail closed", failures)

    def test_namespace_is_stable_and_distinct(self) -> None:
        definition_ids = set(self.definitions)
        requirement_ids = set(self.requirements)
        relationship_ids = {
            item["id"] for item in self.document["relationships"]
        }

        self.assertTrue(
            all(identifier.startswith("L3-PAC-") for identifier in definition_ids)
        )
        self.assertTrue(
            all(identifier.startswith("L3-PAC-REQ-") for identifier in requirement_ids)
        )
        self.assertTrue(
            all(identifier.startswith("L3-PAC-REL-") for identifier in relationship_ids)
        )
        self.assertTrue(definition_ids.isdisjoint(requirement_ids))
        self.assertTrue(definition_ids.isdisjoint(relationship_ids))
        self.assertTrue(requirement_ids.isdisjoint(relationship_ids))

    def test_markdown_is_exact_projection(self) -> None:
        self.assertEqual(
            CONTRACTS_MARKDOWN.read_text(encoding="utf-8"),
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
