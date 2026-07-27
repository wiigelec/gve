from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from specs.tooling.strict_json import load_strict
from specs.tooling.validate import (
    discover_specifications,
    load_specification_manifest,
    validate_specification_set,
)


ROOT = Path(__file__).resolve().parents[2]
ACCEPTED_SPECS = ROOT / "specs"


class Issue103SourceLayoutIntegrationTests(unittest.TestCase):
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

    def test_cross_level_member_is_discovered_once_and_revision_bound(self) -> None:
        manifest = load_specification_manifest(ACCEPTED_SPECS)
        members = [
            member for member in manifest["members"]
            if member["id"] == "GVE-SOURCE-LAYOUT"
        ]
        self.assertEqual(len(members), 1)
        member = members[0]
        self.assertEqual(member["role"], "cross-level")
        self.assertEqual(
            member["path"],
            "source-layout/GVE-SOURCE-LAYOUT.json",
        )
        self.assertEqual(
            member["schema_path"],
            "schemas/GVE-SOURCE-LAYOUT.schema.json",
        )
        document_path = ACCEPTED_SPECS / member["path"]
        self.assertEqual(
            hashlib.sha256(document_path.read_bytes()).hexdigest(),
            member["content_sha256"],
        )
        discovered = [
            path.relative_to(ACCEPTED_SPECS).as_posix()
            for path in discover_specifications(ACCEPTED_SPECS)
        ]
        self.assertEqual(discovered.count(member["path"]), 1)
        revision = validate_specification_set(ACCEPTED_SPECS)
        revision_ids = [
            item["id"] for item in revision["manifest"]["members"]
        ]
        self.assertEqual(revision_ids.count("GVE-SOURCE-LAYOUT"), 1)

    def test_complete_validation_reports_grandfathered_paths(self) -> None:
        import contextlib
        import io

        from specs.tooling.validate import main

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(["--specs-root", str(ACCEPTED_SPECS)])
        self.assertEqual(result, 0)
        self.assertIn(
            "grandfathered maintained Python paths: "
            "src/gve/processing_failure.py",
            output.getvalue(),
        )


    def test_cross_level_member_does_not_require_markdown_projection(self) -> None:
        self.assertFalse(
            (ACCEPTED_SPECS / "source-layout/GVE-SOURCE-LAYOUT.md").exists()
        )
        validate_specification_set(ACCEPTED_SPECS)

    def test_omitted_cross_level_candidate_fails_closed(self) -> None:
        specs_root = self._copy_specs()
        manifest_path = specs_root / "GVE-SPECIFICATION-SET.json"
        manifest = load_strict(manifest_path)
        manifest["members"] = [
            member for member in manifest["members"]
            if member["id"] != "GVE-SOURCE-LAYOUT"
        ]
        import json
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(Exception, "GVE-SOURCE-LAYOUT"):
            validate_specification_set(specs_root)

    def test_wrong_schema_binding_fails_closed(self) -> None:
        specs_root = self._copy_specs()
        manifest_path = specs_root / "GVE-SPECIFICATION-SET.json"
        manifest = load_strict(manifest_path)
        member = next(
            member for member in manifest["members"]
            if member["id"] == "GVE-SOURCE-LAYOUT"
        )
        member["schema_path"] = "schemas/GVE-LEVEL.schema.json"
        import json
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        with self.assertRaises(Exception):
            validate_specification_set(specs_root)

    def test_level_only_fixture_manifest_does_not_require_repository_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            specs_root = root / "specs"
            shutil.copytree(ROOT / "specs", specs_root)
            manifest_path = specs_root / "GVE-SPECIFICATION-SET.json"
            manifest = load_strict(manifest_path)
            manifest["members"] = [
                member
                for member in manifest["members"]
                if member["role"] != "cross-level"
            ]
            manifest_path.write_text(
                json.dumps(manifest, indent=2) + "\n",
                encoding="utf-8",
            )
            source_layout = specs_root / "source-layout"
            shutil.rmtree(source_layout)
            result = validate_specification_set(specs_root)
            self.assertTrue(result["identity"].startswith("gve-spec-revision-sha256:"))



if __name__ == "__main__":
    unittest.main()
