from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
ACCEPTED_SPECS = ROOT / "specs"
LEVEL_0 = ACCEPTED_SPECS / "levels" / "level-0" / "GVE-LEVEL-0.json"
LEVEL_1 = ACCEPTED_SPECS / "levels" / "level-1" / "GVE-LEVEL-1.json"
SCHEMA = ACCEPTED_SPECS / "schemas" / "GVE-LEVEL.schema.json"


class SemanticValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.specs_root = Path(self.temporary.name) / "specs"
        (self.specs_root / "schemas").mkdir(parents=True)
        (self.specs_root / "schemas" / SCHEMA.name).write_bytes(SCHEMA.read_bytes())
        self.documents = {
            0: load_strict(LEVEL_0),
            1: load_strict(LEVEL_1),
        }
        self.write_all()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_all(self) -> None:
        for level, document in self.documents.items():
            directory = self.specs_root / "levels" / f"level-{level}"
            directory.mkdir(parents=True, exist_ok=True)
            json_path = directory / f"GVE-LEVEL-{level}.json"
            json_path.write_text(
                json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            json_path.with_suffix(".md").write_text(
                render_markdown(document),
                encoding="utf-8",
            )

    def run_validation(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "specs.tooling.validate",
                "--specs-root",
                str(self.specs_root),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def assert_rejected(self, expected: str) -> None:
        self.write_all()
        result = self.run_validation()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(expected, result.stderr)

    def test_accepted_level_set_passes_normal_entrypoint(self) -> None:
        result = self.run_validation()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("specification validation passed", result.stdout)

    def test_rejects_duplicate_identifier(self) -> None:
        duplicate = copy.deepcopy(self.documents[1]["definitions"][0])
        self.documents[1]["definitions"].append(duplicate)
        self.assert_rejected("duplicate definition identifier GVE-CORE")

    def test_rejects_cross_class_identifier_collision(self) -> None:
        self.documents[1]["requirements"][0]["id"] = "GVE-CORE"
        self.assert_rejected("ambiguous identifier GVE-CORE")

    def test_rejects_unresolved_requirement_reference(self) -> None:
        self.documents[1]["requirements"][0]["references"] = ["MISSING-DEFINITION"]
        self.assert_rejected(
            "requirement L1-REQ-001 has unresolved definition reference "
            "MISSING-DEFINITION"
        )

    def test_rejects_unresolved_relationship_endpoint(self) -> None:
        self.documents[1]["relationships"][0]["target"] = "MISSING-ENDPOINT"
        self.assert_rejected(
            "relationship L1-REL-001 has unresolved target endpoint "
            "MISSING-ENDPOINT"
        )

    def test_rejects_identity_level_mismatch(self) -> None:
        self.documents[1]["specification"]["id"] = "GVE-LEVEL-2"
        self.assert_rejected("specification id does not match numeric level 1")

    def test_rejects_unresolved_parent(self) -> None:
        self.documents[1]["specification"]["parent"] = "GVE-LEVEL-9"
        self.assert_rejected("unresolved parent specification GVE-LEVEL-9")

    def test_rejects_self_parenting(self) -> None:
        self.documents[1]["specification"]["parent"] = "GVE-LEVEL-1"
        self.assert_rejected("self-parenting is invalid")

    def test_rejects_inheritance_cycle(self) -> None:
        level_2 = copy.deepcopy(self.documents[0])
        level_2["specification"].update(
            {
                "id": "GVE-LEVEL-2",
                "level": 2,
                "title": "GVE Level 2 Test Fixture",
                "parent": "GVE-LEVEL-1",
            }
        )
        self.documents[1]["specification"]["parent"] = "GVE-LEVEL-2"
        self.documents[2] = level_2
        self.assert_rejected("inheritance cycle")

    def test_rejects_invalid_parent_level_ordering(self) -> None:
        level_2 = copy.deepcopy(self.documents[0])
        level_2["specification"].update(
            {
                "id": "GVE-LEVEL-2",
                "level": 2,
                "title": "GVE Level 2 Test Fixture",
                "parent": "GVE-LEVEL-0",
            }
        )
        self.documents[1]["specification"]["parent"] = "GVE-LEVEL-2"
        self.documents[2] = level_2
        self.assert_rejected("invalid parent level ordering")


if __name__ == "__main__":
    unittest.main()
