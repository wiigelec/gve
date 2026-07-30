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
        "functional_area_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class FunctionalAreaTests(unittest.TestCase):
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

    def test_closed_functional_area_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_unknown_functional_area_field_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["unexpected"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_unknown_schema_field_fails_closed(self) -> None:
        path = "authoritative/schemas/functional-areas/FUNCTIONAL-AREA-CONSTRUCTION-SCHEMA.json"
        value = self.read_json(path)
        value["unexpected"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_unknown_functional_area_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["functional_areas"].append("unknown-area")
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001")

    def test_empty_functional_areas_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["functional_areas"] = []
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001")

    def test_duplicate_functional_areas_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["functional_areas"] = ["overview-documentation", "overview-documentation"]
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001")

    def test_missing_area_semantics_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["area_semantics"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001")

    def test_missing_kernel_classifications_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["kernel_classifications"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001")

    def test_missing_extension_rules_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["extension_rules"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001")

    def test_missing_placement_rules_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["placement_rules"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001")

    def test_empty_authority_separation_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["authority_separation"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001")

    def test_empty_decision_basis_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["decision_basis"] = {}
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001")

    def test_unknown_area_in_semantics_fails_closed(self) -> None:
        path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        value = self.read_json(path)
        value["area_semantics"]["unknown-area"] = {
            "description": "not a valid area",
            "kind": "temporary",
            "authority_classification": "non-normative",
            "lifecycle_classification": "temporary",
            "ownership_role": "artifact-owner",
            "containment": "may-not-contain-functional-areas",
            "dependency": "none",
            "path_significance": "well-known-root",
            "ignored_content": True,
            "required": False,
            "product_profile_extensible": False,
        }
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001")

    def test_declared_fixture_cases_execute_exactly_once(self) -> None:
        fixture = self.read_json(
            "validation/fixtures/functional-areas/FUNCTIONAL-AREA-FIXTURES.json"
        )
        seen = set()
        model_path = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
        for case in fixture["cases"]:
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
            self.write_json(model_path, self.read_json(model_path))


if __name__ == "__main__":
    unittest.main()
