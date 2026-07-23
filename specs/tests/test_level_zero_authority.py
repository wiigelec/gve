from __future__ import annotations

import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.semantics import validate_semantics
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

    def test_level_zero_authority_properties(self) -> None:
        document = load_strict(LEVEL)
        self.assertEqual(document["specification"]["id"], "GVE-LEVEL-0")
        self.assertEqual(document["specification"]["level"], 0)
        self.assertEqual(document["specification"]["status"], "normative")
        self.assertIsNone(document["specification"]["parent"])


if __name__ == "__main__":
    unittest.main()
