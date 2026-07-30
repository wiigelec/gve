from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SOURCE_ROOT / "validation/intrinsic/validate_specification_identities.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "specification_identities_validator_tests", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class SpecificationIdentitiesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE_ROOT, self.root, symlinks=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_failure(self, code: str) -> str:
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.validate(self.root)
        message = str(raised.exception)
        self.assertTrue(message.startswith(code + ":"), message)
        return message

    def read_json(self, relative: str) -> dict:
        return json.loads((self.root / relative).read_text(encoding="utf-8"))

    def write_json(self, relative: str, value: dict) -> None:
        (self.root / relative).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_specification_identity_profile_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_manifest_duplicate_policy_must_remain_closed(self) -> None:
        relative = VALIDATOR.MODEL_PATH
        value = self.read_json(relative)
        value["manifest_model"]["duplicate_policy"] = "allow"
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-SPECIFICATION-IDENTITY-001")

    def test_schema_target_must_remain_fixed(self) -> None:
        relative = VALIDATOR.SCHEMA_PATH
        value = self.read_json(relative)
        value["target_construction_identity"] = "alternate-specification-identities-construction"
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-SPECIFICATION-IDENTITY-002")

    def test_conformance_boundary_must_remain_closed(self) -> None:
        relative = VALIDATOR.CONFORMANCE_PATH
        value = self.read_json(relative)
        value["authority_boundary"]["accepted-conformance"] = True
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-SPECIFICATION-IDENTITY-004")

    def test_conformance_vector_ids_must_remain_unique(self) -> None:
        relative = VALIDATOR.CONFORMANCE_VECTOR_PATH
        value = self.read_json(relative)
        value["vectors"][1]["vector_id"] = value["vectors"][0]["vector_id"]
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-SPECIFICATION-IDENTITY-006")


if __name__ == "__main__":
    unittest.main()
