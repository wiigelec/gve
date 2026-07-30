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
        "product_artifact_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


PRODUCT_ARTIFACT_CLOSED_ROLES: tuple[str, ...] = (
    "maintained-source", "product-test", "configuration", "schema",
    "template", "generator", "generated-artifact", "command-line-executable",
    "library", "service", "package", "user-documentation",
    "release-automation", "repository-maintenance-tooling",
)
PRODUCT_ARTIFACT_PATH = "authoritative/product-artifacts/PRODUCT-ARTIFACTS.json"


class ProductArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE_ROOT, self.root, symlinks=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def read_json(self, relative: str) -> dict:
        return json.loads((self.root / relative).read_text(encoding="utf-8"))

    def write_json(self, relative: str, value: dict) -> None:
        (self.root / relative).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def assert_failure(self, code: str) -> None:
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.validate(self.root)
        self.assertTrue(str(raised.exception).startswith(code + ":"), str(raised.exception))

    def test_closed_product_artifact_model_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_unknown_product_artifact_field_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        value["unexpected"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_unknown_schema_field_fails_closed(self) -> None:
        path = "authoritative/schemas/product-artifacts/PRODUCT-ARTIFACT-CONSTRUCTION-SCHEMA.json"
        value = self.read_json(path)
        value["unexpected"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_fewer_than_fourteen_roles_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        value["artifact_roles"] = value["artifact_roles"][:5]
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PRODUCT-ARTIFACT-001")

    def test_extra_role_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        value["artifact_roles"].append("extra-role")
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PRODUCT-ARTIFACT-001")

    def test_unknown_role_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        value["artifact_roles"][0] = "unknown-role"
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PRODUCT-ARTIFACT-001")

    def test_duplicate_role_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        value["artifact_roles"].append("maintained-source")
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PRODUCT-ARTIFACT-001")

    def test_missing_artifact_roles_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        del value["artifact_roles"]
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-002")

    def test_empty_role_constraints_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        value["role_constraints"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PRODUCT-ARTIFACT-001")

    def test_missing_role_constraint_entry_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        del value["role_constraints"]["maintained-source"]
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PRODUCT-ARTIFACT-001")

    def test_empty_role_relationships_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        value["role_relationships"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PRODUCT-ARTIFACT-001")

    def test_empty_decision_basis_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        value["decision_basis"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PRODUCT-ARTIFACT-001")

    def test_forbidden_claim_field_fails_closed(self) -> None:
        path = PRODUCT_ARTIFACT_PATH
        value = self.read_json(path)
        value["accepted"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_declared_fixture_cases_execute_exactly_once(self) -> None:
        fixture = self.read_json(
            "validation/fixtures/product-artifacts/PRODUCT-ARTIFACT-FIXTURES.json"
        )
        seen = set()
        model_path = PRODUCT_ARTIFACT_PATH
        original = self.read_json(model_path)
        for case in fixture["cases"]:
            self.write_json(model_path, original)
            self.assertNotIn(case["name"], seen)
            seen.add(case["name"])
            model = self.read_json(model_path)
            for dotted_path, override in case["model_overrides"].items():
                target = model
                parts = dotted_path.split(".")
                for part in parts[:-1]:
                    target = target[part]
                target[parts[-1]] = override
            self.write_json(model_path, model)
            if case["expected"] == "pass":
                VALIDATOR.validate(self.root)
            else:
                with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
                    VALIDATOR.validate(self.root)
                self.assertTrue(
                    str(raised.exception).startswith(case["expected_diagnostic"] + ":"),
                    str(raised.exception),
                )


if __name__ == "__main__":
    unittest.main()
