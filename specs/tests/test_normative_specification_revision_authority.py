from __future__ import annotations

import unittest
from pathlib import Path

from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
LEVELS = ROOT / "specs" / "levels"


def _document(level: int, identifier: str) -> dict:
    return load_strict(
        LEVELS / f"level-{level}" / f"{identifier}.json"
    )


class NormativeSpecificationRevisionAuthorityTests(unittest.TestCase):
    def test_document_authority_defines_complete_revision_contract(self) -> None:
        authority = _document(2, "GVE-LEVEL-2-DOCUMENT-AUTHORITY")
        definitions = {
            item["id"]: item["text"]
            for item in authority["definitions"]
        }
        requirements = {
            item["id"]: item["text"]
            for item in authority["requirements"]
        }

        for identifier in (
            "L2-DA-NORMATIVE-CONTENT-IDENTITY",
            "L2-DA-REVISION-MEMBER-BINDING",
            "L2-DA-REVISION-MANIFEST",
            "L2-DA-SPECIFICATION-REVISION",
            "L2-DA-HISTORICAL-ATTRIBUTION",
        ):
            self.assertIn(identifier, definitions)

        for identifier in (
            "L2-DA-REQ-013",
            "L2-DA-REQ-014",
            "L2-DA-REQ-015",
            "L2-DA-REQ-016",
            "L2-DA-REQ-017",
            "L2-DA-REQ-018",
            "L2-DA-REQ-019",
        ):
            self.assertIn(identifier, requirements)

        self.assertIn(
            "every accepted normative JSON specification document exactly once",
            requirements["L2-DA-REQ-013"],
        )
        self.assertIn(
            "semantic-version string",
            requirements["L2-DA-REQ-014"],
        )
        self.assertIn(
            "repository commit",
            requirements["L2-DA-REQ-014"],
        )
        self.assertIn(
            "derived Markdown projection",
            requirements["L2-DA-REQ-014"],
        )
        self.assertIn(
            "Any change to authoritative normative JSON content",
            requirements["L2-DA-REQ-016"],
        )
        self.assertIn(
            "current governing specification-set revision",
            requirements["L2-DA-REQ-018"],
        )
        self.assertIn(
            "Historical contracts",
            requirements["L2-DA-REQ-019"],
        )

    def test_workflow_composition_imports_revision_authority(self) -> None:
        composition = _document(2, "GVE-LEVEL-2-WORKFLOW-COMPOSITION")
        self.assertIn(
            "GVE-LEVEL-2-DOCUMENT-AUTHORITY",
            composition["document"]["imports"],
        )
        contract_text = " ".join(
            item["text"]
            for item in composition["requirements"]
            if item["id"] in {"L2-WC-REQ-005", "L2-WC-REQ-006"}
        )
        self.assertIn("governing instruction set", contract_text)
        self.assertIn("fresh", contract_text)

    def test_level_three_contracts_require_instruction_set_revision(self) -> None:
        contracts = _document(3, "GVE-LEVEL-3-PLUGIN-ACTION-CONTRACTS")
        requirement = next(
            item
            for item in contracts["requirements"]
            if item["id"] == "L3-PAC-REQ-FRESHNESS-BINDING-IDENTITIES"
        )
        self.assertIn(
            "governed instruction set revision",
            requirement["text"],
        )
        self.assertIn(
            "Freshness must not be established by an unbound Boolean assertion",
            requirement["text"],
        )

    def test_plan_evidence_and_results_retain_governing_authority(self) -> None:
        lifecycle = _document(
            3,
            "GVE-LEVEL-3-WORKFLOW-PLANNING-LIFECYCLE",
        )
        evidence = _document(
            3,
            "GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION",
        )

        lifecycle_text = " ".join(
            item["text"]
            for item in lifecycle["definitions"] + lifecycle["requirements"]
        )
        evidence_text = " ".join(
            item["text"]
            for item in evidence["definitions"] + evidence["requirements"]
        )

        self.assertIn("governing authority", lifecycle_text)
        self.assertIn("accepted-plan snapshot", lifecycle_text)
        self.assertIn("governing authority", evidence_text)
        self.assertIn("authoritative execution record", evidence_text)
        self.assertIn("result-realization attempt", evidence_text)


if __name__ == "__main__":
    unittest.main()
