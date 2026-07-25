from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.semantics import SemanticValidationError, validate_hierarchy
from specs.tooling.strict_json import load_strict
from specs.tooling.validate import discover_specifications


ROOT = Path(__file__).resolve().parents[2]
ACCEPTED_SPECS = ROOT / "specs"


class SpecificationSetInvariantTests(unittest.TestCase):
    def _copy_specs(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        destination = Path(temporary.name) / "specs"
        shutil.copytree(
            ACCEPTED_SPECS,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        return destination

    def _run_validation(self, specs_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "specs.tooling.validate",
                "--specs-root",
                str(specs_root),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def _assert_rejected(self, specs_root: Path, expected: str) -> None:
        result = self._run_validation(specs_root)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(expected, result.stderr)

    def _rewrite_document(
        self,
        specs_root: Path,
        level: int,
        specification_id: str,
        mutate,
    ) -> None:
        path = (
            specs_root
            / "levels"
            / f"level-{level}"
            / f"{specification_id}.json"
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

    def _remove_document(
        self,
        specs_root: Path,
        level: int,
        specification_id: str,
    ) -> None:
        path = (
            specs_root
            / "levels"
            / f"level-{level}"
            / f"{specification_id}.json"
        )
        path.unlink()
        path.with_suffix(".md").unlink()

    def _add_unexpected_document(
        self,
        specs_root: Path,
        level: int,
        specification_id: str,
    ) -> None:
        root_id = f"GVE-LEVEL-{level}"
        document = {
            "$schema": "../../schemas/GVE-LEVEL.schema.json",
            "specification": {
                "id": specification_id,
                "level": level,
                "title": f"Unexpected Level {level} Test Document",
                "version": "1.0.0",
                "status": "normative",
                "parent": root_id,
            },
            "document": {
                "role": "subordinate",
                "root": root_id,
                "imports": [root_id],
            },
            "summary": "A structurally valid unexpected normative test document.",
            "definitions": [],
            "requirements": [],
            "relationships": [],
            "scope": {
                "includes": ["Specification-set invariant testing"],
                "excludes": ["Accepted authority"],
            },
        }
        path = (
            specs_root
            / "levels"
            / f"level-{level}"
            / f"{specification_id}.json"
        )
        path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        path.with_suffix(".md").write_text(
            render_markdown(document),
            encoding="utf-8",
        )

    def test_accepted_repository_passes_normal_entrypoint(self) -> None:
        result = self._run_validation(ACCEPTED_SPECS)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("specification validation passed", result.stdout)

    def test_rejects_missing_required_level_two_member(self) -> None:
        specs_root = self._copy_specs()
        self._remove_document(
            specs_root,
            2,
            "GVE-LEVEL-2-RESULT-ASSEMBLY",
        )
        self._assert_rejected(
            specs_root,
            "GVE-LEVEL-2: unresolved specification-set member "
            "GVE-LEVEL-2-RESULT-ASSEMBLY",
        )

    def test_rejects_unexpected_level_two_member(self) -> None:
        specs_root = self._copy_specs()
        self._add_unexpected_document(
            specs_root,
            2,
            "GVE-LEVEL-2-UNEXPECTED",
        )
        self._assert_rejected(
            specs_root,
            "GVE-LEVEL-2: specification-set membership mismatch; "
            "missing=[], unexpected=['GVE-LEVEL-2-UNEXPECTED']",
        )

    def test_rejects_missing_required_level_three_member(self) -> None:
        specs_root = self._copy_specs()
        self._remove_document(
            specs_root,
            3,
            "GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION",
        )
        self._assert_rejected(
            specs_root,
            "GVE-LEVEL-3: unresolved specification-set member "
            "GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION",
        )

    def test_rejects_unexpected_level_three_member(self) -> None:
        specs_root = self._copy_specs()
        self._add_unexpected_document(
            specs_root,
            3,
            "GVE-LEVEL-3-UNEXPECTED",
        )
        self._assert_rejected(
            specs_root,
            "GVE-LEVEL-3: specification-set membership mismatch; "
            "missing=[], unexpected=['GVE-LEVEL-3-UNEXPECTED']",
        )

    def test_rejects_root_that_skips_immediate_parent_level(self) -> None:
        specs_root = self._copy_specs()

        def mutate(document: dict) -> None:
            document["specification"]["parent"] = "GVE-LEVEL-1"

        self._rewrite_document(specs_root, 3, "GVE-LEVEL-3", mutate)
        self._assert_rejected(
            specs_root,
            "GVE-LEVEL-3: root parent must be immediate prior-level root "
            "GVE-LEVEL-2; found GVE-LEVEL-1",
        )

    def test_rejects_non_normative_required_subordinate(self) -> None:
        specs_root = self._copy_specs()

        def mutate(document: dict) -> None:
            document["specification"]["status"] = "draft"

        self._rewrite_document(
            specs_root,
            2,
            "GVE-LEVEL-2-RESULT-ASSEMBLY",
            mutate,
        )
        self._assert_rejected(
            specs_root,
            "GVE-LEVEL-2-RESULT-ASSEMBLY: accepted specification-set member "
            "must have normative status; found draft",
        )

    def test_rejects_non_normative_required_root(self) -> None:
        specs_root = self._copy_specs()

        def mutate(document: dict) -> None:
            document["specification"]["status"] = "retired"

        self._rewrite_document(specs_root, 3, "GVE-LEVEL-3", mutate)
        self._assert_rejected(
            specs_root,
            "GVE-LEVEL-3: accepted specification-set member must have "
            "normative status; found retired",
        )

    def test_membership_diagnostic_is_discovery_order_independent(self) -> None:
        specs_root = self._copy_specs()
        self._add_unexpected_document(
            specs_root,
            2,
            "GVE-LEVEL-2-ZETA",
        )
        self._add_unexpected_document(
            specs_root,
            2,
            "GVE-LEVEL-2-ALPHA",
        )
        result = self._run_validation(specs_root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "GVE-LEVEL-2: specification-set membership mismatch; missing=[], "
            "unexpected=['GVE-LEVEL-2-ALPHA', 'GVE-LEVEL-2-ZETA']",
            result.stderr,
        )



if __name__ == "__main__":
    unittest.main()
