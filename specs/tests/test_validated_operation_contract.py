from __future__ import annotations

import unittest
from pathlib import Path

from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
LEVEL_1 = ROOT / "specs" / "levels" / "level-1" / "GVE-LEVEL-1.json"


class ValidatedOperationContractAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = load_strict(LEVEL_1)
        cls.definitions = {item["id"]: item for item in cls.document["definitions"]}
        cls.requirements = {item["id"]: item for item in cls.document["requirements"]}
        cls.relationships = {item["id"]: item for item in cls.document["relationships"]}

    def test_contract_definition_is_explicit_and_core_readable(self) -> None:
        text = self.definitions["VALIDATED-OPERATION-CONTRACT"]["text"]
        self.assertIn("plugin-produced, core-readable", text)
        self.assertIn("exactly one governed operation", text)
        self.assertIn("exactly one selected plugin", text)
        self.assertIn("neither duplicated nor reinterpreted by the core", text)

    def test_successful_plugin_interpretation_produces_contract(self) -> None:
        requirement = self.requirements["L1-REQ-008A"]
        self.assertIn("Successful instruction interpretation", requirement["text"])
        self.assertIn("exactly one validated operation contract", requirement["text"])
        self.assertIn("VALIDATED-OPERATION-CONTRACT", requirement["references"])

    def test_core_visible_fields_and_semantic_boundary_are_normative(self) -> None:
        text = self.requirements["L1-REQ-008B"]["text"]
        for phrase in (
            "contract identity and freshness",
            "operation and plugin identity",
            "governing authority",
            "lifecycle readiness",
            "evidence obligations",
            "failure behavior",
            "result-assembly obligations",
        ):
            self.assertIn(phrase, text)
        self.assertIn("must not derive, duplicate, or reinterpret", text)

    def test_invalid_contracts_fail_closed_before_execution(self) -> None:
        text = self.requirements["L1-REQ-008C"]["text"]
        for state in (
            "missing", "malformed", "invalid", "ambiguous", "conflicting",
            "unauthorized", "stale", "non-uniquely attributable",
        ):
            self.assertIn(state, text)
        self.assertIn("before operation execution", text)

    def test_contract_validation_is_not_an_effect_claim(self) -> None:
        text = self.requirements["L1-REQ-008C"]["text"]
        for claim in (
            "requested", "authorized", "attempted", "completed", "observed", "verified",
        ):
            self.assertIn(claim, text)

    def test_relationships_make_handoff_explicit(self) -> None:
        expected = {
            "L1-REL-020": ("INSTRUCTION-INTERPRETATION", "VALIDATED-OPERATION-CONTRACT"),
            "L1-REL-021": ("VALIDATED-OPERATION-CONTRACT", "GOVERNED-OPERATION"),
            "L1-REL-022": ("VALIDATED-OPERATION-CONTRACT", "SELECTED-PLUGIN"),
            "L1-REL-023": ("WORKFLOW-VALIDATION", "VALIDATED-OPERATION-CONTRACT"),
        }
        for identifier, endpoints in expected.items():
            relationship = self.relationships[identifier]
            self.assertEqual((relationship["source"], relationship["target"]), endpoints)


if __name__ == "__main__":
    unittest.main()
