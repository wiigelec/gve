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
    spec = importlib.util.spec_from_file_location("identity_family_validator_tests", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

VALIDATOR = load_validator()

class IdentityFamilyConstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE_ROOT, self.root, symlinks=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def read_json(self, relative: str) -> dict:
        return json.loads((self.root / relative).read_text(encoding="utf-8"))

    def write_json(self, relative: str, value: dict) -> None:
        (self.root / relative).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def assert_failure(self, code: str) -> None:
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.validate(self.root)
        self.assertTrue(str(raised.exception).startswith(code + ":"), str(raised.exception))

    def test_identity_family_construction_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_unknown_family_field_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[2]
        value = self.read_json(relative)
        value["unknown"] = True
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-FIELD-001")

    def test_changed_family_policy_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[2]
        value = self.read_json(relative)
        value["field_constraints"]["digest_algorithm"] = ["sha-512"]
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-FAMILY-001")

    def test_changed_identity_model_policy_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["subject_categories"] = ["object"]
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-MODEL-001")

    def test_changed_model_schema_fails(self) -> None:
        value = self.read_json(VALIDATOR.MODEL_SCHEMA_PATH)
        value["closed"] = False
        self.write_json(VALIDATOR.MODEL_SCHEMA_PATH, value)
        self.assert_failure("REPO-SPEC-IDENTITY-SCHEMA-001")

    def test_changed_family_schema_fails(self) -> None:
        value = self.read_json(VALIDATOR.FAMILY_SCHEMA_PATH)
        value["target_construction_identity"] = "identity-model-construction"
        self.write_json(VALIDATOR.FAMILY_SCHEMA_PATH, value)
        self.assert_failure("REPO-SPEC-IDENTITY-SCHEMA-001")

if __name__ == "__main__":
    unittest.main()
