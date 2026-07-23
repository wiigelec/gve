from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "specs" / "schemas" / "level.schema.json"
LEVEL_PATH = ROOT / "specs" / "levels" / "level-0.json"
REQUIREMENT_ID = re.compile(r"^L[0-9]+-[A-Z][A-Z0-9]*-[0-9]{3}$")


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


class LevelSpecificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = _load(SCHEMA_PATH)
        cls.level = _load(LEVEL_PATH)

    def test_schema_is_closed_draft_2020_12_contract(self) -> None:
        self.assertEqual(
            self.schema["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(self.schema["properties"]["schema_version"], {"const": 1})
        self.assertFalse(
            self.schema["$defs"]["requirement"]["additionalProperties"]
        )

    def test_level_document_declares_schema_and_authority(self) -> None:
        self.assertEqual(self.level["$schema"], "../schemas/level.schema.json")
        self.assertEqual(
            self.level["authority"]["prose_specification"], "LEVEL_0.md"
        )
        self.assertEqual(
            self.level["authority"]["precedence"],
            [
                "prose_specification",
                "structured_level_specification",
                "implementation",
                "tests",
            ],
        )

    def test_level_document_has_exact_top_level_fields(self) -> None:
        allowed = set(self.schema["required"]) | {"$schema"}
        self.assertEqual(set(self.level), allowed)

    def test_requirement_ids_are_valid_and_unique(self) -> None:
        ids = [item["id"] for item in self.level["requirements"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(REQUIREMENT_ID.fullmatch(item) for item in ids))

    def test_every_requirement_has_exact_closed_fields(self) -> None:
        expected = set(self.schema["$defs"]["requirement"]["required"])
        for requirement in self.level["requirements"]:
            self.assertEqual(set(requirement), expected)

    def test_every_requirement_has_traceability(self) -> None:
        requirement_ids = {item["id"] for item in self.level["requirements"]}
        coverage = self.level["traceability"]["requirement_coverage"]
        coverage_ids = [item["requirement_id"] for item in coverage]
        self.assertEqual(set(coverage_ids), requirement_ids)
        self.assertEqual(len(coverage_ids), len(set(coverage_ids)))
        for item in coverage:
            self.assertTrue(item["implementation"])
            self.assertTrue(item["tests"])

    def test_referenced_maintained_tests_exist(self) -> None:
        maintained = {
            name
            for name, item in __import__(
                "gve.tests.test_level0", fromlist=["Level0PayloadTests"]
            ).Level0PayloadTests.__dict__.items()
            if callable(item) and name.startswith("test_")
        }
        references = {
            ref.rsplit(".", 1)[-1]
            for coverage in self.level["traceability"]["requirement_coverage"]
            for ref in coverage["tests"]
            if ref.startswith("gve.tests.test_level0.")
        }
        self.assertTrue(references)
        self.assertTrue(references <= maintained)

    def test_contracts_are_closed(self) -> None:
        for name in ("operation_description", "result_evidence"):
            contract = self.level["contracts"][name]
            self.assertIs(contract["closed"], True)
            self.assertEqual(contract["unknown_fields"], "reject")
            self.assertTrue(contract["required_fields"])


if __name__ == "__main__":
    unittest.main()
