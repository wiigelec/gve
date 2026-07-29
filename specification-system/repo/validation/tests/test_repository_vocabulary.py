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
        "repository_vocabulary_validator", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class RepositoryVocabularyTests(unittest.TestCase):
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

    def test_closed_repository_vocabulary_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_unknown_model_field_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["unexpected"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_unknown_schema_field_fails_closed(self) -> None:
        path = "authoritative/schemas/repository-model/REPOSITORY-VOCABULARY-CONSTRUCTION-SCHEMA.json"
        value = self.read_json(path)
        value["unexpected"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-FIELD-001")

    def test_file_containment_is_forbidden(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["containment_rules"]["file_may_contain"] = True
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-001")

    def test_directory_containment_is_required(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["containment_rules"]["directory_may_contain"] = False
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-001")

    def test_backslash_path_fails_closed(self) -> None:
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.contained_path(self.root, "authoritative\\repository-model", "test")
        self.assertTrue(str(raised.exception).startswith("REPO-SPEC-CONSTRUCTION-PATH-002:"))

    def test_nul_path_fails_closed(self) -> None:
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.contained_path(self.root, "authoritative/repository-model\u0000", "test")
        self.assertTrue(str(raised.exception).startswith("REPO-SPEC-CONSTRUCTION-PATH-002:"))

    def test_schema_required_fields_are_unique(self) -> None:
        path = "authoritative/schemas/repository-model/REPOSITORY-VOCABULARY-CONSTRUCTION-SCHEMA.json"
        value = self.read_json(path)
        value["required_fields"].append(value["required_fields"][0])
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-002")

    def test_duplicate_tree_member_path_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["records"]["tree_members"].append(dict(value["records"]["tree_members"][0], id="duplicate-path"))
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004")

    def test_duplicate_area_id_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["records"]["areas"].append(dict(value["records"]["areas"][0]))
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004")

    def test_duplicate_owner_target_and_role_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["records"]["owners"].append(dict(value["records"]["owners"][0], id="duplicate-owner"))
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004")

    def test_classification_conflict_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["records"]["tree_members"][1]["lifecycle_classification"] = "generated"
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004")

    def test_unknown_tree_member_classification_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["records"]["tree_members"][1]["entry_kind"] = "symlink"
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004")

    def test_invalid_containment_parent_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["records"]["containments"][0]["parent"] = "authority-example"
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004")

    def test_dependency_cycle_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["records"]["dependencies"].append({
            "source": "authority",
            "target": "authority-example",
            "relation": "depends-on",
        })
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004")

    def test_tree_member_traversal_path_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["records"]["tree_members"][1]["path"] = "authority/../example.json"
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-PATH-002")

    def test_unknown_owner_target_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["records"]["owners"][0]["target"] = "unknown-target"
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004")

    def test_duplicate_dependency_fails_closed(self) -> None:
        path = "authoritative/repository-model/REPOSITORY-MODEL.json"
        value = self.read_json(path)
        value["records"]["dependencies"].append(dict(value["records"]["dependencies"][0]))
        self.write_json(path, value)
        self.assert_failure("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004")

    def test_declared_fixture_cases_execute_exactly_once(self) -> None:
        fixture = self.read_json(
            "validation/fixtures/repository-model/REPOSITORY-VOCABULARY-FIXTURES.json"
        )
        seen = set()
        model_path = "authoritative/repository-model/REPOSITORY-MODEL.json"
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
