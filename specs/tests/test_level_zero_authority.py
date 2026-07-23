from __future__ import annotations

import copy
import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.semantics import SemanticValidationError, validate_semantics
from specs.tooling.strict_json import load_strict
from specs.tooling.validate import validate_document


ROOT = Path(__file__).resolve().parents[1]
LEVEL = ROOT / "levels" / "level-0" / "GVE-LEVEL-0.json"
MARKDOWN = LEVEL.with_suffix(".md")
SCHEMA = ROOT / "schemas" / "GVE-LEVEL.schema.json"


class LevelZeroAuthorityTests(unittest.TestCase):
    def test_authoritative_json_is_structurally_valid(self) -> None:
        validate_document(LEVEL, SCHEMA)

    def test_authoritative_json_is_semantically_valid(self) -> None:
        validate_semantics(load_strict(LEVEL), LEVEL)

    def test_committed_markdown_is_deterministic_projection(self) -> None:
        self.assertEqual(
            MARKDOWN.read_text(encoding="utf-8"),
            render_markdown(load_strict(LEVEL)),
        )


    def test_semantic_validation_rejects_wrong_level_path(self) -> None:
        document = load_strict(LEVEL)
        invalid_paths = (
            ROOT / "levels" / "level-1" / "GVE-LEVEL-0.json",
            ROOT / "levels" / "level-zero" / "GVE-LEVEL-0.json",
            ROOT / "level-0" / "GVE-LEVEL-0.json",
        )
        for path in invalid_paths:
            with self.subTest(path=path):
                with self.assertRaisesRegex(
                    SemanticValidationError,
                    r"path must end with levels/level-0/GVE-LEVEL-0\.json",
                ):
                    validate_semantics(document, path)

    def test_renderer_names_the_document_being_rendered(self) -> None:
        document = copy.deepcopy(load_strict(LEVEL))
        document["specification"].update(
            {
                "id": "GVE-LEVEL-1",
                "level": 1,
                "title": "GVE Level 1",
                "parent": "GVE-LEVEL-0",
            }
        )
        rendered = render_markdown(document)
        self.assertIn(
            "> Generated deterministically from `GVE-LEVEL-1.json`.",
            rendered,
        )
        self.assertNotIn("`GVE-LEVEL-0.json`", rendered.splitlines()[2])

    def test_execution_evidence_is_defined_and_governed(self) -> None:
        document = load_strict(LEVEL)
        definitions = {item["id"]: item for item in document["definitions"]}
        requirements = {item["id"]: item for item in document["requirements"]}
        relationships = {item["id"]: item for item in document["relationships"]}

        self.assertIn("EXECUTION-EVIDENCE", definitions)
        self.assertIn(
            "EXECUTION-EVIDENCE",
            requirements["L0-REQ-010"]["references"],
        )
        self.assertEqual(
            relationships["L0-REL-006"],
            {
                "id": "L0-REL-006",
                "source": "GOVERNED-INSTRUCTION-SET",
                "relation": "interprets",
                "target": "EXECUTION-EVIDENCE",
            },
        )

    def test_level_zero_authority_properties(self) -> None:
        document = load_strict(LEVEL)
        self.assertEqual(document["specification"]["id"], "GVE-LEVEL-0")
        self.assertEqual(document["specification"]["level"], 0)
        self.assertEqual(document["specification"]["status"], "normative")
        self.assertIsNone(document["specification"]["parent"])


if __name__ == "__main__":
    unittest.main()
