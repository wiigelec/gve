from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SOURCE_ROOT / "validation/intrinsic/validate_identity_construction.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "identity_construction_validator_tests", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class IdentityConstructionTests(unittest.TestCase):
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

    def read_json(self, relative: str) -> dict:
        return json.loads((self.root / relative).read_text(encoding="utf-8"))

    def write_json(self, relative: str, value: dict) -> None:
        (self.root / relative).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def test_identity_construction_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_each_identity_artifact_is_required(self) -> None:
        for relative in VALIDATOR.ARTIFACTS:
            with self.subTest(relative=relative):
                copy = Path(self.temporary.name) / Path(relative).stem
                shutil.copytree(self.root, copy)
                (copy / relative).unlink()
                with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
                    VALIDATOR.validate(copy)
                self.assertTrue(str(raised.exception).startswith("GVE-RSI-PATH-001:"))

    def test_each_supporting_marker_is_required(self) -> None:
        for relative in VALIDATOR.SUPPORTING_PATHS:
            with self.subTest(relative=relative):
                copy = Path(self.temporary.name) / relative.replace("/", "-")
                shutil.copytree(self.root, copy)
                (copy / relative).unlink()
                with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
                    VALIDATOR.validate(copy)
                self.assertTrue(str(raised.exception).startswith("GVE-RSI-PATH-001:"))

    def test_unknown_field_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["final"] = True
        self.write_json(relative, value)
        self.assert_failure("GVE-RSI-FIELD-001")

    def test_missing_field_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        del value["responsibility"]
        self.write_json(relative, value)
        self.assert_failure("GVE-RSI-FIELD-002")

    def test_duplicate_identity_fails(self) -> None:
        first, second = VALIDATOR.ARTIFACTS[:2]
        first_value = self.read_json(first)
        second_value = self.read_json(second)
        second_value["construction_identity"] = first_value["construction_identity"]
        self.write_json(second, second_value)
        self.assert_failure("GVE-RSI-IDENTITY-002")

    def test_invalid_status_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["construction_status"] = "candidate"
        self.write_json(relative, value)
        self.assert_failure("GVE-RSI-STATUS-001")

    def test_normative_true_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["normative"] = True
        self.write_json(relative, value)
        self.assert_failure("GVE-RSI-STATUS-002")

    def test_manifest_omission_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        manifest = self.read_json("REPOSITORY-SPECIFICATION-SET.json")
        manifest["artifact_paths"].remove(relative)
        self.write_json("REPOSITORY-SPECIFICATION-SET.json", manifest)
        self.assert_failure("GVE-RSI-MANIFEST-001")

    def test_product_family_leakage_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["expected_relationships"].append("gve-plan")
        self.write_json(relative, value)
        self.assert_failure("GVE-RSI-PRODUCT-001")

    def test_maintained_product_import_fails(self) -> None:
        path = self.root / "validation/intrinsic/product_import.py"
        path.write_text("import gve\n", encoding="utf-8")
        self.assert_failure("GVE-RSI-DEPENDENCY-001")


if __name__ == "__main__":
    unittest.main()
