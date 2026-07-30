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
        "governed_development_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


GOVERNED_DEVELOPMENT_PATH = "authoritative/governed-development/GOVERNED-DEVELOPMENT.json"


class GovernedDevelopmentTests(unittest.TestCase):
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

    def test_closed_model_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_unknown_field_fails_closed(self) -> None:
        path = GOVERNED_DEVELOPMENT_PATH
        value = self.read_json(path)
        value["unexpected"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_unknown_schema_field_fails_closed(self) -> None:
        path = "authoritative/schemas/governed-development/GOVERNED-DEVELOPMENT-CONSTRUCTION-SCHEMA.json"
        value = self.read_json(path)
        value["unexpected"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_empty_lifecycle_stages_fails_closed(self) -> None:
        path = GOVERNED_DEVELOPMENT_PATH
        value = self.read_json(path)
        value["lifecycle_stages"] = []
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-GOVERNED-DEVELOPMENT-001")

    def test_empty_bounded_work_stages_fails_closed(self) -> None:
        path = GOVERNED_DEVELOPMENT_PATH
        value = self.read_json(path)
        value["bounded_work_stages"] = []
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-GOVERNED-DEVELOPMENT-001")

    def test_empty_stage_semantics_fails_closed(self) -> None:
        path = GOVERNED_DEVELOPMENT_PATH
        value = self.read_json(path)
        value["stage_semantics"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-GOVERNED-DEVELOPMENT-001")

    def test_empty_decision_basis_fails_closed(self) -> None:
        path = GOVERNED_DEVELOPMENT_PATH
        value = self.read_json(path)
        value["decision_basis"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-GOVERNED-DEVELOPMENT-001")

    def test_forbidden_claim_field_fails_closed(self) -> None:
        path = GOVERNED_DEVELOPMENT_PATH
        value = self.read_json(path)
        value["accepted"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_declared_fixture_cases_execute_exactly_once(self) -> None:
        fixture = self.read_json(
            "validation/fixtures/governed-development/GOVERNED-DEVELOPMENT-FIXTURES.json"
        )
        seen = set()
        model_path = GOVERNED_DEVELOPMENT_PATH
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
