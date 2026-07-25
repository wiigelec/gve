from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.strict_json import load_strict
from specs.tooling.validate import (
    discover_specifications,
    load_specification_manifest,
    validate_specification_set,
)


ROOT = Path(__file__).resolve().parents[2]
ACCEPTED_SPECS = ROOT / "specs"


class Issue74SpecificationManifestTests(unittest.TestCase):
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

    def test_manifest_is_complete_ordered_and_content_bound(self) -> None:
        manifest = load_specification_manifest(ACCEPTED_SPECS)
        members = manifest["members"]
        identifiers = [member["id"] for member in members]
        self.assertEqual(identifiers, sorted(identifiers))
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(
            [path.relative_to(ACCEPTED_SPECS).as_posix() for path in discover_specifications(ACCEPTED_SPECS)],
            [member["path"] for member in members],
        )
        for member in members:
            path = ACCEPTED_SPECS / member["path"]
            document = load_strict(path)
            self.assertEqual(document["specification"]["id"], member["id"])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                member["content_sha256"],
            )

    def test_filename_discovery_does_not_grant_authority(self) -> None:
        specs_root = self._copy_specs()
        source = specs_root / "levels/level-3/GVE-LEVEL-3.json"
        unexpected = specs_root / "levels/level-3/GVE-LEVEL-3-UNDECLARED.json"
        document = load_strict(source)
        document["specification"]["id"] = "GVE-LEVEL-3-UNDECLARED"
        document["specification"]["title"] = "Undeclared Candidate"
        document["specification"]["parent"] = "GVE-LEVEL-3"
        document["document"] = {
            "role": "subordinate",
            "root": "GVE-LEVEL-3",
            "imports": ["GVE-LEVEL-3"],
        }
        unexpected.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        declared = [path.name for path in discover_specifications(specs_root)]
        self.assertNotIn(unexpected.name, declared)
        result = self._run_validation(specs_root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected=['GVE-LEVEL-3-UNDECLARED']", result.stderr)

    def test_manifest_omission_removes_authority_and_fails_closed(self) -> None:
        specs_root = self._copy_specs()
        manifest_path = specs_root / "GVE-SPECIFICATION-SET.json"
        manifest = load_strict(manifest_path)
        manifest["members"] = [
            member
            for member in manifest["members"]
            if member["id"] != "GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION"
        ]
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        result = self._run_validation(specs_root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "unexpected=['GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION']",
            result.stderr,
        )

    def test_content_change_requires_manifest_identity_update(self) -> None:
        specs_root = self._copy_specs()
        path = specs_root / "levels/level-0/GVE-LEVEL-0.json"
        document = load_strict(path)
        document["summary"] += " Changed without manifest update."
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        path.with_suffix(".md").write_text(
            render_markdown(document),
            encoding="utf-8",
        )
        result = self._run_validation(specs_root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manifest content_sha256 conflicts", result.stderr)

    def test_validation_revision_uses_exact_manifest_members(self) -> None:
        manifest = load_specification_manifest(ACCEPTED_SPECS)
        revision = validate_specification_set(ACCEPTED_SPECS)
        self.assertEqual(
            [member["id"] for member in revision["manifest"]["members"]],
            [member["id"] for member in manifest["members"]],
        )


if __name__ == "__main__":
    unittest.main()
