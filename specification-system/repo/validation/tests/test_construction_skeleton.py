from __future__ import annotations

import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SOURCE_ROOT / "validation/intrinsic/validate_skeleton.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "construction_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class ConstructionSkeletonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE_ROOT, self.root, symlinks=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_failure(self, code: str, *, root: Path | None = None) -> None:
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.validate(root or self.root)
        self.assertTrue(
            str(raised.exception).startswith(code + ":"),
            str(raised.exception),
        )

    def json_path(self, relative: str) -> Path:
        return self.root / relative

    def read_json(self, relative: str) -> dict:
        return json.loads(self.json_path(relative).read_text(encoding="utf-8"))

    def write_json(self, relative: str, value: dict) -> None:
        self.json_path(relative).write_text(
            json.dumps(value, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_valid_bounded_tree_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_missing_required_path_fails(self) -> None:
        self.json_path("derived/markdown/README.md").unlink()
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PATH-001")

    def test_malformed_json_fails(self) -> None:
        self.json_path("REPOSITORY-SPECIFICATION-SET.json").write_text(
            "{",
            encoding="utf-8",
        )
        self.assert_failure("REPO-SPEC-CONSTRUCTION-JSON-001")

    def test_non_standard_json_constant_fails(self) -> None:
        self.json_path("REPOSITORY-SPECIFICATION-SET.json").write_text(
            '{"construction_identity": NaN}',
            encoding="utf-8",
        )
        self.assert_failure("REPO-SPEC-CONSTRUCTION-JSON-001")

    def test_unknown_manifest_field_fails(self) -> None:
        value = self.read_json("REPOSITORY-SPECIFICATION-SET.json")
        value["extra"] = True
        self.write_json("REPOSITORY-SPECIFICATION-SET.json", value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_unknown_placeholder_field_fails(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["extra"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_duplicate_identity_fails(self) -> None:
        first = self.read_json(
            "authoritative/repository-model/REPOSITORY-MODEL.json"
        )
        second_path = (
            "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json"
        )
        second = self.read_json(second_path)
        second["construction_identity"] = first["construction_identity"]
        self.write_json(second_path, second)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-IDENTITY-003")

    def test_normative_placeholder_fails(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["normative"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-STATUS-002")

    def test_completion_claim_fails(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["construction_status"] = "complete"
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-STATUS-001")

    def test_fabricated_digest_field_fails(self) -> None:
        value = self.read_json("REPOSITORY-SPECIFICATION-SET.json")
        value["digest"] = "sha256:" + "0" * 64
        self.write_json("REPOSITORY-SPECIFICATION-SET.json", value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_absolute_artifact_path_fails(self) -> None:
        value = self.read_json("REPOSITORY-SPECIFICATION-SET.json")
        value["artifact_paths"][0] = "/tmp/REPOSITORY-MODEL.json"
        self.write_json("REPOSITORY-SPECIFICATION-SET.json", value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PATH-004")

    def test_traversal_artifact_path_fails(self) -> None:
        value = self.read_json("REPOSITORY-SPECIFICATION-SET.json")
        value["artifact_paths"][0] = "../REPOSITORY-MODEL.json"
        self.write_json("REPOSITORY-SPECIFICATION-SET.json", value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PATH-004")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlink_escape_fails(self) -> None:
        target = self.root / (
            "authoritative/repository-model/REPOSITORY-MODEL.json"
        )
        target.unlink()
        os.symlink("/tmp", target)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PATH-003")

    def test_work_derived_identity_fails(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["construction_identity"] = "issue-model"
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-NAME-001")

    def test_unrelated_product_or_third_party_import_fails(self) -> None:
        for module in ("some_other_product", "requests"):
            with self.subTest(module=module):
                copy = Path(self.temporary.name) / module
                shutil.copytree(self.root, copy, symlinks=True)
                path = copy / "validation/intrinsic/forbidden_dependency.py"
                path.write_text(f"import {module}\n", encoding="utf-8")
                self.assert_failure(
                    "REPO-SPEC-CONSTRUCTION-DEPENDENCY-001",
                    root=copy,
                )

    def test_standard_library_and_local_imports_pass(self) -> None:
        local_module = self.root / "repository_local_helper.py"
        local_module.write_text("VALUE = 1\n", encoding="utf-8")
        path = self.root / "validation/intrinsic/allowed_dependencies.py"
        path.write_text(
            "import json\n"
            "from pathlib import Path\n"
            "import repository_local_helper\n",
            encoding="utf-8",
        )
        VALIDATOR.validate(self.root)


if __name__ == "__main__":
    unittest.main()
