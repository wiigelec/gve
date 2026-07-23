from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "specs" / "tooling"))

from semantics import validate_semantics
from render import render_markdown


LEVEL_0 = ROOT / "specs" / "levels" / "level-0" / "GVE-LEVEL-0.json"
LEVEL_1 = ROOT / "specs" / "levels" / "level-1" / "GVE-LEVEL-1.json"
LEVEL_1_MD = ROOT / "specs" / "levels" / "level-1" / "GVE-LEVEL-1.md"


class Level1AuthorityTests(unittest.TestCase):
    def load(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_level_1_declares_level_0_parent(self) -> None:
        document = self.load(LEVEL_1)
        self.assertEqual(document["specification"]["id"], "GVE-LEVEL-1")
        self.assertEqual(document["specification"]["level"], 1)
        self.assertEqual(document["specification"]["parent"], "GVE-LEVEL-0")
        self.assertTrue(LEVEL_0.is_file())

    def test_level_1_semantics_are_valid(self) -> None:
        validate_semantics(self.load(LEVEL_1), LEVEL_1)

    def test_level_1_projection_is_synchronized(self) -> None:
        self.assertEqual(
            LEVEL_1_MD.read_text(encoding="utf-8"),
            render_markdown(self.load(LEVEL_1)),
        )

    def test_level_1_preserves_required_effect_language(self) -> None:
        requirements = " ".join(
            item["text"] for item in self.load(LEVEL_1)["requirements"]
        ).lower()
        for term in (
            "requested",
            "authorized",
            "attempted",
            "completed",
            "observed",
            "verified",
        ):
            self.assertIn(term, requirements)

    def test_level_1_requires_exactly_one_selected_plugin(self) -> None:
        requirements = " ".join(
            item["text"] for item in self.load(LEVEL_1)["requirements"]
        ).lower()
        self.assertIn("exactly one selected application plugin", requirements)
        self.assertIn("fail closed", requirements)

    def test_root_level_1_has_been_removed(self) -> None:
        self.assertFalse((ROOT / "LEVEL_1.md").exists())


if __name__ == "__main__":
    unittest.main()
