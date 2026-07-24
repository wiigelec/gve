from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs"
LEVEL_3_JSON = SPECS / "levels" / "level-3" / "GVE-LEVEL-3.json"
LEVEL_3_MARKDOWN = LEVEL_3_JSON.with_suffix(".md")

EXPECTED_DOCUMENTS = {
    "GVE-LEVEL-3",
    "GVE-LEVEL-3-RUNTIME-OWNERSHIP",
    "GVE-LEVEL-3-PLUGIN-ACTION-CONTRACTS",
    "GVE-LEVEL-3-WORKFLOW-PLANNING-LIFECYCLE",
    "GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION",
}

EXPECTED_RESPONSIBILITY_DEFINITIONS = {
    "LEVEL-3-RUNTIME-OWNERSHIP",
    "LEVEL-3-PLUGIN-ACTION-CONTRACTS",
    "LEVEL-3-WORKFLOW-PLANNING-LIFECYCLE",
    "LEVEL-3-EVIDENCE-RESULT-REALIZATION",
}


class LevelThreeRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = load_strict(LEVEL_3_JSON)

    def test_root_identity_parentage_and_imports(self) -> None:
        self.assertEqual(
            self.document["specification"],
            {
                "id": "GVE-LEVEL-3",
                "level": 3,
                "title": "GVE Level 3",
                "version": "1.0.0",
                "status": "normative",
                "parent": "GVE-LEVEL-2",
            },
        )
        self.assertEqual(
            self.document["document"],
            {
                "role": "root",
                "root": "GVE-LEVEL-3",
                "imports": [],
            },
        )

    def test_exact_five_document_decomposition(self) -> None:
        definitions = {
            item["id"]: item["text"] for item in self.document["definitions"]
        }
        self.assertTrue(EXPECTED_RESPONSIBILITY_DEFINITIONS <= set(definitions))

        decomposition = next(
            item
            for item in self.document["requirements"]
            if item["id"] == "L3-ROOT-REQ-004"
        )
        for identifier in EXPECTED_DOCUMENTS:
            self.assertIn(identifier, decomposition["text"])

        relationships = {
            item["target"]
            for item in self.document["relationships"]
            if item["relation"] == "contains-responsibility"
        }
        self.assertEqual(relationships, EXPECTED_RESPONSIBILITY_DEFINITIONS)

    def test_root_namespace_is_stable_and_distinct(self) -> None:
        requirement_ids = {item["id"] for item in self.document["requirements"]}
        relationship_ids = {item["id"] for item in self.document["relationships"]}
        self.assertTrue(requirement_ids)
        self.assertTrue(relationship_ids)
        self.assertTrue(
            all(identifier.startswith("L3-ROOT-REQ-") for identifier in requirement_ids)
        )
        self.assertTrue(
            all(identifier.startswith("L3-ROOT-REL-") for identifier in relationship_ids)
        )
        self.assertTrue(requirement_ids.isdisjoint(relationship_ids))

    def test_evidence_result_realization_owns_versioned_results(self) -> None:
        definition = next(
            item
            for item in self.document["definitions"]
            if item["id"] == "LEVEL-3-EVIDENCE-RESULT-REALIZATION"
        )
        self.assertIn("authoritative execution-record realization", definition["text"])
        self.assertIn("explicit supersession", definition["text"])
        self.assertIn("one current lineage head", definition["text"])

    def test_legacy_level_three_material_is_absent(self) -> None:
        serialized = json.dumps(self.document, ensure_ascii=False)
        self.assertNotIn("LEVEL_3.md", serialized)
        self.assertNotIn("HISTORICAL-LEVEL-3-MATERIAL", serialized)

    def test_markdown_is_exact_projection(self) -> None:
        self.assertEqual(
            LEVEL_3_MARKDOWN.read_text(encoding="utf-8"),
            render_markdown(self.document),
        )

    def test_repository_specification_validation_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "specs.tooling.validate", "--specs-root", str(SPECS)],
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
