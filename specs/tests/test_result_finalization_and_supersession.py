from __future__ import annotations

import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs"
PATHS = {
    "level0": SPECS / "levels" / "level-0" / "GVE-LEVEL-0.json",
    "level2": SPECS / "levels" / "level-2" / "GVE-LEVEL-2-RESULT-ASSEMBLY.json",
    "level3": SPECS / "levels" / "level-3" / "GVE-LEVEL-3.json",
    "realization": SPECS / "levels" / "level-3" / "GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION.json",
}


class ResultFinalizationAndSupersessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = {name: load_strict(path) for name, path in PATHS.items()}

    def definitions(self, name: str) -> dict[str, str]:
        return {item["id"]: item["text"] for item in self.documents[name]["definitions"]}

    def requirements(self, name: str) -> dict[str, str]:
        return {item["id"]: item["text"] for item in self.documents[name]["requirements"]}

    def requirement_containing(self, name: str, phrase: str) -> str:
        matches = [
            item["text"]
            for item in self.documents[name]["requirements"]
            if phrase in item["text"]
        ]
        self.assertEqual(len(matches), 1, f"expected one requirement containing {phrase!r}")
        return matches[0]

    def test_level_zero_preserves_truthful_record_when_finalization_fails(self) -> None:
        definitions = self.definitions("level0")
        requirements = self.requirements("level0")
        self.assertIn("inability to finalize", definitions["AUTHORITATIVE-RESULT"])
        self.assertIn("Failure to finalize", definitions["FINALIZED-RESULT"])
        self.assertIn(
            "must not be represented as successful finalization",
            requirements["L0-REQ-012"],
        )

    def test_level_two_separates_execution_record_from_finalized_result(self) -> None:
        definitions = self.definitions("level2")
        requirements = self.requirements("level2")
        self.assertIn(
            "whether or not a workflow result can be finalized",
            definitions["L2-RA-WORKFLOW-EXECUTION-RECORD"],
        )
        self.assertIn(
            "exists only when result finalization succeeds",
            definitions["L2-RA-AUTHORITATIVE-WORKFLOW-RESULT"],
        )
        self.assertIn(
            "no finalized authoritative workflow result may be claimed",
            requirements["L2-RA-REQ-019"],
        )

    def test_preexecution_partial_and_contradictory_outcomes_remain_reportable(self) -> None:
        text = self.requirement_containing(
            "realization", "Pre-execution validation failure"
        )
        self.assertIn("partial execution", text)
        self.assertIn("contradictory evidence", text)
        self.assertIn("without claiming", text)

    def test_versions_are_immutable_and_supersession_is_explicit(self) -> None:
        definitions = self.definitions("realization")
        self.assertIn("immutable", definitions["L3-ERR-RESULT-VERSION"])
        self.assertIn("correction reason", definitions["L3-ERR-SUPERSESSION"])
        requirement = self.requirement_containing(
            "realization", "supersession relationships must be acyclic"
        )
        self.assertIn("preserve every prior finalized version unchanged", requirement)

    def test_exactly_one_means_one_current_lineage_head(self) -> None:
        requirements = self.requirements("level2")
        self.assertIn("at most one current lineage head", requirements["L2-RA-REQ-022"])
        self.assertIn(
            "Multiple immutable historical versions are permitted",
            requirements["L2-RA-REQ-022"],
        )

    def test_status_never_substitutes_for_effect_claims(self) -> None:
        requirement = self.requirement_containing(
            "realization", "must not substitute for any effect-claim state"
        )
        self.assertIn("Lifecycle status", requirement)
        self.assertIn("current-head designation", requirement)

    def test_all_changed_markdown_files_are_exact_projections(self) -> None:
        for document_path in PATHS.values():
            document = load_strict(document_path)
            self.assertEqual(
                document_path.with_suffix(".md").read_text(encoding="utf-8"),
                render_markdown(document),
            )


if __name__ == "__main__":
    unittest.main()
