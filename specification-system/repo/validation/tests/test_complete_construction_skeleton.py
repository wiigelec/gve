from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SOURCE_ROOT / "validation/intrinsic/validate_skeleton.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "complete_construction_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class CompleteConstructionSkeletonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE_ROOT, self.root, symlinks=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_failure(self, code: str) -> None:
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.validate(self.root)
        self.assertTrue(str(raised.exception).startswith(code + ":"), str(raised.exception))

    def read_manifest(self) -> dict:
        return json.loads(
            (self.root / "REPOSITORY-SPECIFICATION-SET.json").read_text(encoding="utf-8")
        )

    def write_manifest(self, value: dict) -> None:
        (self.root / "REPOSITORY-SPECIFICATION-SET.json").write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def test_complete_skeleton_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_each_new_authority_area_is_required(self) -> None:
        for relative in (
            "authoritative/identity",
            "authoritative/development-process",
            "authoritative/normative-change",
            "authoritative/level-model",
            "authoritative/source-layout",
            "authoritative/platform-profile",
            "authoritative/schemas",
            "authoritative/schemas/platform-profile",
            "authoritative/conformance",
        ):
            with self.subTest(relative=relative):
                copy = Path(self.temporary.name) / relative.replace("/", "-")
                shutil.copytree(self.root, copy)
                shutil.rmtree(copy / relative)
                with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
                    VALIDATOR.validate(copy)
                self.assertTrue(str(raised.exception).startswith("REPO-SPEC-CONSTRUCTION-PATH-001:"))

    def test_each_new_validation_area_is_required(self) -> None:
        for relative in ("validation/lib", "validation/repository", "validation/fixtures"):
            with self.subTest(relative=relative):
                copy = Path(self.temporary.name) / relative.replace("/", "-")
                shutil.copytree(self.root, copy)
                shutil.rmtree(copy / relative)
                with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
                    VALIDATOR.validate(copy)
                self.assertTrue(str(raised.exception).startswith("REPO-SPEC-CONSTRUCTION-PATH-001:"))

        for relative in ("validation/fixtures/platform-profile",):
            with self.subTest(relative=relative):
                copy = Path(self.temporary.name) / relative.replace("/", "-")
                shutil.copytree(self.root, copy)
                shutil.rmtree(copy / relative)
                with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
                    VALIDATOR.validate(copy)
                self.assertTrue(str(raised.exception).startswith("REPO-SPEC-CONSTRUCTION-PATH-001:"))

    def test_unknown_artifact_class_fails(self) -> None:
        value = self.read_manifest()
        value["artifact_classes"][0] = "unknown-placeholder"
        self.write_manifest(value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-CLASS-001")

    def test_declared_missing_artifact_fails(self) -> None:
        path = self.root / "authoritative/identity/IDENTITY-AUTHORITY.json"
        path.unlink()
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PATH-001")

    def test_undeclared_participant_fails(self) -> None:
        source = self.root / "authoritative/identity/IDENTITY-AUTHORITY.json"
        target = self.root / "authoritative/identity/EXTRA-AUTHORITY.json"
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PATH-006")

    def test_manifest_inventory_mismatch_fails(self) -> None:
        value = self.read_manifest()
        value["artifact_paths"] = value["artifact_paths"][:-1]
        self.write_manifest(value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PATH-004")


if __name__ == "__main__":
    unittest.main()
