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
        "specification_artifact_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class SpecificationArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE_ROOT, self.root, symlinks=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def read_model(self) -> dict:
        return json.loads(
            (self.root / "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json")
            .read_text(encoding="utf-8")
        )

    def write_model(self, value: dict) -> None:
        (self.root / "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json").write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def assert_failure(self, code: str) -> None:
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.validate(self.root)
        self.assertTrue(str(raised.exception).startswith(code + ":"), str(raised.exception))

    def test_closed_artifact_class_model_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_unknown_relationship_fails_closed(self) -> None:
        value = self.read_model()
        value["class_constraints"]["schema"]["required_relationships"].append("unknown-target")
        self.write_model(value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-ARTIFACT-001")

    def test_contradictory_relationship_constraint_fails_closed(self) -> None:
        value = self.read_model()
        value["class_constraints"]["schema"]["forbidden_relationships"].append("schema-target")
        self.write_model(value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-ARTIFACT-001")

    def test_class_relationship_contract_cannot_be_reassigned(self) -> None:
        value = self.read_model()
        value["class_constraints"]["derived-artifact"]["required_relationships"] = [
            "conformance-target"
        ]
        self.write_model(value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-ARTIFACT-001")

    def test_projection_relationship_must_be_acyclic_and_deterministic(self) -> None:
        value = self.read_model()
        value["relationship_rules"]["projection-source"]["acyclic"] = False
        self.write_model(value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-ARTIFACT-001")

    def test_duplicate_relationship_type_fails_closed(self) -> None:
        value = self.read_model()
        value["relationship_types"].append("schema-target")
        self.write_model(value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-ARTIFACT-001")

    def test_schema_required_fields_bind_to_closed_model(self) -> None:
        path = self.root / "authoritative/schemas/specification-system/SPECIFICATION-ARTIFACT-CLASS-CONSTRUCTION-SCHEMA.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["required_fields"].remove("relationship_types")
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        self.assert_failure("REPO-SPEC-CONSTRUCTION-ARTIFACT-002")

    def test_schema_forbidden_claim_fields_are_complete(self) -> None:
        path = self.root / "authoritative/schemas/specification-system/SPECIFICATION-ARTIFACT-CLASS-CONSTRUCTION-SCHEMA.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["forbidden_claim_fields"].remove("final")
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        self.assert_failure("REPO-SPEC-CONSTRUCTION-ARTIFACT-002")

    def test_declared_fixture_cases_execute_exactly_once(self) -> None:
        fixture_path = self.root / "validation/fixtures/specification-system/SPECIFICATION-ARTIFACT-FIXTURES.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        model_path = self.root / "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json"
        original = json.loads(model_path.read_text(encoding="utf-8"))
        seen = set()
        for case in fixture["cases"]:
            self.assertNotIn(case["name"], seen)
            seen.add(case["name"])
            model = json.loads(json.dumps(original))
            for dotted_path, override in case["class_overrides"].items():
                target = model
                parts = dotted_path.split(".")
                for part in parts[:-1]:
                    target = target[part]
                target[parts[-1]] = override
            model_path.write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")
            if case["expected"] == "pass":
                VALIDATOR.validate(self.root)
            else:
                with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
                    VALIDATOR.validate(self.root)
                self.assertTrue(
                    str(raised.exception).startswith(case["expected_diagnostic"] + ":"),
                    str(raised.exception),
                )
        model_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
