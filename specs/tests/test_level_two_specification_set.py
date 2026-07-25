from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs"
LEVEL_0 = SPECS / "levels" / "level-0" / "GVE-LEVEL-0.json"
LEVEL_1 = SPECS / "levels" / "level-1" / "GVE-LEVEL-1.json"
SCHEMA = SPECS / "schemas" / "GVE-LEVEL.schema.json"
MANIFEST_SCHEMA = SPECS / "schemas" / "GVE-SPECIFICATION-SET.schema.json"


class LevelTwoSpecificationSetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.specs_root = Path(self.temporary.name) / "specs"
        (self.specs_root / "schemas").mkdir(parents=True)
        (self.specs_root / "schemas" / SCHEMA.name).write_bytes(SCHEMA.read_bytes())
        (self.specs_root / "schemas" / MANIFEST_SCHEMA.name).write_bytes(
            MANIFEST_SCHEMA.read_bytes()
        )
        self.documents = {
            "GVE-LEVEL-0": load_strict(LEVEL_0),
            "GVE-LEVEL-1": load_strict(LEVEL_1),
        }
        self._add_level_two_set()
        self.write_all()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _base_document(
        self,
        identifier: str,
        *,
        title: str,
        parent: str,
        role: str,
        root: str,
        imports: list[str],
    ) -> dict:
        document = copy.deepcopy(self.documents["GVE-LEVEL-0"])
        document["specification"].update(
            {
                "id": identifier,
                "level": 2,
                "title": title,
                "version": "0.1.0",
                "status": "normative",
                "parent": parent,
            }
        )
        document["document"] = {
            "role": role,
            "root": root,
            "imports": imports,
        }
        document["definitions"] = []
        document["requirements"] = []
        document["relationships"] = []
        document["scope"] = {
            "includes": ["Synthetic Level 2 specification-set validation."],
            "excludes": ["Substantive Level 2 product semantics."],
        }
        return document

    def _add_level_two_set(self) -> None:
        root = self._base_document(
            "GVE-LEVEL-2",
            title="GVE Level 2 Root Test Fixture",
            parent="GVE-LEVEL-1",
            role="root",
            root="GVE-LEVEL-2",
            imports=[],
        )
        root["document"]["members"] = [
            "GVE-LEVEL-2",
            "GVE-LEVEL-2-ALPHA",
            "GVE-LEVEL-2-BETA",
        ]
        root["definitions"] = [
            {"id": "L2-ROOT-TERM", "term": "Root term", "text": "Root definition."}
        ]

        alpha = self._base_document(
            "GVE-LEVEL-2-ALPHA",
            title="GVE Level 2 Alpha Test Fixture",
            parent="GVE-LEVEL-2",
            role="subordinate",
            root="GVE-LEVEL-2",
            imports=["GVE-LEVEL-2"],
        )
        alpha["definitions"] = [
            {"id": "L2-ALPHA-TERM", "term": "Alpha term", "text": "Alpha definition."}
        ]
        alpha["requirements"] = [
            {
                "id": "L2-ALPHA-REQ",
                "text": "Alpha uses the root term.",
                "references": ["L2-ROOT-TERM"],
            }
        ]

        beta = self._base_document(
            "GVE-LEVEL-2-BETA",
            title="GVE Level 2 Beta Test Fixture",
            parent="GVE-LEVEL-2",
            role="subordinate",
            root="GVE-LEVEL-2",
            imports=["GVE-LEVEL-2-ALPHA"],
        )
        beta["requirements"] = [
            {
                "id": "L2-BETA-REQ",
                "text": "Beta uses the transitively imported root term.",
                "references": ["L2-ROOT-TERM"],
            }
        ]
        beta["relationships"] = [
            {
                "id": "L2-BETA-REL",
                "source": "L2-BETA-REQ",
                "relation": "depends-on",
                "target": "L2-ALPHA-TERM",
            }
        ]

        self.documents.update(
            {
                "GVE-LEVEL-2": root,
                "GVE-LEVEL-2-ALPHA": alpha,
                "GVE-LEVEL-2-BETA": beta,
            }
        )

    def write_all(self) -> None:
        levels = self.specs_root / "levels"
        if levels.exists():
            for path in sorted(levels.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
        for document in self.documents.values():
            specification = document["specification"]
            directory = levels / f"level-{specification['level']}"
            directory.mkdir(parents=True, exist_ok=True)
            json_path = directory / f"{specification['id']}.json"
            json_path.write_text(
                json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            json_path.with_suffix(".md").write_text(
                render_markdown(document),
                encoding="utf-8",
            )

        members = []
        for path in sorted(levels.glob("level-*/GVE-LEVEL-*.json")):
            document = load_strict(path)
            members.append(
                {
                    "path": path.relative_to(self.specs_root).as_posix(),
                    "role": document.get("document", {}).get("role", "root"),
                    "id": document["specification"]["id"],
                    "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        members.sort(key=lambda member: member["id"])
        manifest = {
            "$schema": "schemas/GVE-SPECIFICATION-SET.schema.json",
            "schema_version": 1,
            "canonicalization": "gve-canonical-json-v1",
            "digest_algorithm": "sha256",
            "identity_format": "gve-canonical-json-v1+sha256:lowercase-hex",
            "members": members,
        }
        (self.specs_root / "GVE-SPECIFICATION-SET.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

    def run_validation(self) -> subprocess.CompletedProcess[str]:
        self.write_all()
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
        result = self.run_validation()
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(expected, result.stderr)

    def test_accepts_root_and_two_subordinate_documents(self) -> None:
        result = self.run_validation()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("specification validation passed", result.stdout)

    def test_rejects_missing_root_membership_metadata(self) -> None:
        self.documents["GVE-LEVEL-2"]["document"].pop("members")
        self.assert_rejected(
            "decomposed specification-set root must declare document.members"
        )

    def test_rejects_unresolved_declared_member(self) -> None:
        self.documents["GVE-LEVEL-2"]["document"]["members"].append(
            "GVE-LEVEL-2-MISSING"
        )
        self.assert_rejected(
            "unresolved specification-set member GVE-LEVEL-2-MISSING"
        )

    def test_rejects_undeclared_discovered_member(self) -> None:
        self.documents["GVE-LEVEL-2"]["document"]["members"].remove(
            "GVE-LEVEL-2-BETA"
        )
        self.assert_rejected(
            "specification-set membership mismatch; missing=[], "
            "unexpected=['GVE-LEVEL-2-BETA']"
        )

    def test_rejects_root_omitted_from_declared_members(self) -> None:
        self.documents["GVE-LEVEL-2"]["document"]["members"].remove(
            "GVE-LEVEL-2"
        )
        self.assert_rejected(
            "specification-set membership mismatch; missing=[], "
            "unexpected=['GVE-LEVEL-2']"
        )

    def test_rejects_member_from_another_specification_set(self) -> None:
        self.documents["GVE-LEVEL-2"]["document"]["members"].append(
            "GVE-LEVEL-1"
        )
        self.assert_rejected(
            "declared specification-set member GVE-LEVEL-1 "
            "is another specification-set root"
        )

    def test_membership_diagnostic_ignores_declaration_order(self) -> None:
        members = self.documents["GVE-LEVEL-2"]["document"]["members"]
        members.remove("GVE-LEVEL-2-BETA")
        first = self.run_validation()
        self.assertNotEqual(first.returncode, 0, first.stdout)

        members.reverse()
        second = self.run_validation()
        self.assertNotEqual(second.returncode, 0, second.stdout)
        self.assertEqual(first.stderr, second.stderr)

    def test_rejects_zero_roots(self) -> None:
        self.documents["GVE-LEVEL-2"]["document"]["role"] = "subordinate"
        self.assert_rejected("must contain exactly one root document; found 0")

    def test_rejects_multiple_roots(self) -> None:
        alpha = self.documents["GVE-LEVEL-2-ALPHA"]
        alpha["document"].update({"role": "root", "root": "GVE-LEVEL-2-ALPHA"})
        self.assert_rejected("must contain exactly one root document; found 2")

    def test_rejects_unresolved_membership_root(self) -> None:
        self.documents["GVE-LEVEL-2-ALPHA"]["document"]["root"] = "GVE-LEVEL-2-MISSING"
        self.assert_rejected("unresolved specification-set root GVE-LEVEL-2-MISSING")

    def test_rejects_unresolved_import(self) -> None:
        self.documents["GVE-LEVEL-2-ALPHA"]["document"]["imports"] = [
            "GVE-LEVEL-2-MISSING"
        ]
        self.assert_rejected("unresolved import target GVE-LEVEL-2-MISSING")

    def test_rejects_import_cycle(self) -> None:
        self.documents["GVE-LEVEL-2-ALPHA"]["document"]["imports"] = [
            "GVE-LEVEL-2-BETA"
        ]
        self.assert_rejected("import cycle")

    def test_rejects_cross_document_identifier_conflict(self) -> None:
        duplicate = copy.deepcopy(
            self.documents["GVE-LEVEL-2"]["definitions"][0]
        )
        self.documents["GVE-LEVEL-2-ALPHA"]["definitions"].append(duplicate)
        self.assert_rejected("cross-document identifier conflict L2-ROOT-TERM")

    def test_rejects_reference_without_import_visibility(self) -> None:
        self.documents["GVE-LEVEL-2-ALPHA"]["document"]["imports"] = []
        self.assert_rejected(
            "unresolved definition reference L2-ROOT-TERM in visible imports"
        )

    def test_rejects_subordinate_parent_outside_set_root(self) -> None:
        self.documents["GVE-LEVEL-2-ALPHA"]["specification"]["parent"] = "GVE-LEVEL-1"
        self.assert_rejected(
            "subordinate parent must be specification-set root GVE-LEVEL-2"
        )


if __name__ == "__main__":
    unittest.main()
