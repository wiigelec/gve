from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from specs.tooling.level2_audit import (
    EXPECTED_LEVEL_TWO_DOCUMENTS,
    LevelTwoAuditError,
    audit_level_two,
)
from specs.tooling.render import render_markdown
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
ACCEPTED_SPECS = ROOT / "specs"


class LevelTwoAcceptanceAuditTests(unittest.TestCase):
    def test_accepted_repository_level_two_audit_passes(self) -> None:
        result = audit_level_two(ACCEPTED_SPECS)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["document_count"], 6)
        self.assertEqual(set(result["documents"]), EXPECTED_LEVEL_TWO_DOCUMENTS)

    def _copy_specs(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        destination = Path(temporary.name) / "specs"
        for source in ACCEPTED_SPECS.rglob("*"):
            relative = source.relative_to(ACCEPTED_SPECS)
            target = destination / relative
            if source.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif "__pycache__" not in source.parts:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
        return destination

    def _rewrite_document(self, specs_root: Path, identifier: str, mutate) -> None:
        path = (
            specs_root
            / "levels"
            / "level-2"
            / f"{identifier}.json"
        )
        document = load_strict(path)
        mutate(document)
        path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        path.with_suffix(".md").write_text(
            render_markdown(document),
            encoding="utf-8",
        )

    def test_rejects_missing_discovered_level_two_document(self) -> None:
        specs_root = self._copy_specs()
        identifier = "GVE-LEVEL-2-RESULT-ASSEMBLY"
        (specs_root / "levels" / "level-2" / f"{identifier}.json").unlink()
        (specs_root / "levels" / "level-2" / f"{identifier}.md").unlink()
        with self.assertRaisesRegex(LevelTwoAuditError, "discovery mismatch"):
            audit_level_two(specs_root)

    def test_rejects_markdown_projection_drift(self) -> None:
        specs_root = self._copy_specs()
        projection = (
            specs_root
            / "levels"
            / "level-2"
            / "GVE-LEVEL-2-WORKFLOW-COMPOSITION.md"
        )
        projection.write_text(
            projection.read_text(encoding="utf-8") + "drift\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(LevelTwoAuditError, "projection drift"):
            audit_level_two(specs_root)

    def test_rejects_missing_required_contract_safeguard(self) -> None:
        specs_root = self._copy_specs()

        def mutate(document: dict) -> None:
            document["requirements"] = [
                item
                for item in document["requirements"]
                if item["id"] != "L2-WC-REQ-005"
            ]

        self._rewrite_document(
            specs_root,
            "GVE-LEVEL-2-WORKFLOW-COMPOSITION",
            mutate,
        )
        with self.assertRaisesRegex(
            LevelTwoAuditError, "missing required requirements"
        ):
            audit_level_two(specs_root)

    def test_rejects_ambiguous_local_plugin_assignment_rule(self) -> None:
        specs_root = self._copy_specs()

        def mutate(document: dict) -> None:
            for item in document["requirements"]:
                if item["id"] == "L2-LPB-REQ-002":
                    item["text"] = (
                        "A declared operation may be assigned to any available "
                        "plugin domain."
                    )

        self._rewrite_document(
            specs_root,
            "GVE-LEVEL-2-LOCAL-PLUGIN-BOUNDARIES",
            mutate,
        )
        with self.assertRaisesRegex(
            LevelTwoAuditError, "unique domain assignment"
        ):
            audit_level_two(specs_root)

    def test_rejects_core_interpretation_of_plugin_meaning(self) -> None:
        specs_root = self._copy_specs()

        def mutate(document: dict) -> None:
            for item in document["requirements"]:
                if item["id"] == "L2-LPB-REQ-010":
                    item["text"] = (
                        "The core may interpret domain-specific operation meaning."
                    )

        self._rewrite_document(
            specs_root,
            "GVE-LEVEL-2-LOCAL-PLUGIN-BOUNDARIES",
            mutate,
        )
        with self.assertRaisesRegex(
            LevelTwoAuditError, "prohibit core domain interpretation"
        ):
            audit_level_two(specs_root)

    def test_rejects_overlapping_local_plugin_ownership(self) -> None:
        specs_root = self._copy_specs()

        def mutate(document: dict) -> None:
            for item in document["requirements"]:
                if item["id"] == "L2-LPB-REQ-013":
                    item["text"] = (
                        "Filesystem, command-execution, and local-Git domains "
                        "may overlap."
                    )

        self._rewrite_document(
            specs_root,
            "GVE-LEVEL-2-LOCAL-PLUGIN-BOUNDARIES",
            mutate,
        )
        with self.assertRaisesRegex(
            LevelTwoAuditError, "reject overlapping ownership"
        ):
            audit_level_two(specs_root)

    def test_rejects_collapsed_effect_states(self) -> None:
        specs_root = self._copy_specs()

        def mutate(document: dict) -> None:
            for item in document["requirements"]:
                if item["id"] == "L2-RA-REQ-004":
                    item["text"] = (
                        "Successful completion establishes all effect states."
                    )

        self._rewrite_document(
            specs_root,
            "GVE-LEVEL-2-RESULT-ASSEMBLY",
            mutate,
        )
        with self.assertRaisesRegex(
            LevelTwoAuditError, "effect-state distinctions"
        ):
            audit_level_two(specs_root)


if __name__ == "__main__":
    unittest.main()
