from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SOURCE_ROOT / "validation/intrinsic/validate_identity_construction.py"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from validation.intrinsic.identity_behavior_adapter import (  # noqa: E402
    build_behavior_registry,
    evaluate_behavior,
)

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

    def assert_failure(self, code: str) -> str:
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.validate(self.root)
        message = str(raised.exception)
        self.assertTrue(message.startswith(code + ":"), message)
        return message

    def test_identity_family_construction_and_fixtures_pass(self) -> None:
        VALIDATOR.validate(self.root)

    def test_unknown_and_missing_model_fields_fail(self) -> None:
        relative = VALIDATOR.ARTIFACTS[2]
        value = self.read_json(relative)
        value["unknown"] = True
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-FIELD-001")
        value = dict(VALIDATOR.EXPECTED_FAMILY)
        del value["conflict_rules"]
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-FIELD-002")

    def test_canonical_model_policy_remains_enforced(self) -> None:
        relative = VALIDATOR.ARTIFACTS[1]
        value = self.read_json(relative)
        value["canonicalization_version"] = "canonical-json-v2"
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-CANONICAL-001")

    def test_canonical_schema_policy_remains_enforced(self) -> None:
        value = self.read_json(VALIDATOR.SCHEMA_PATH)
        value["field_constraints"]["canonicalization_version"] = ["canonical-json-v2"]
        self.write_json(VALIDATOR.SCHEMA_PATH, value)
        self.assert_failure("REPO-SPEC-IDENTITY-SCHEMA-001")

    def test_identifier_distinction_is_structurally_required(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        del value["identifier_distinction"]
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-FIELD-002")

    def test_each_governed_fixture_case_has_expected_result(self) -> None:
        fixture = self.read_json(VALIDATOR.FIXTURE_PATH)
        self.assertGreaterEqual(len(fixture["cases"]), 10)
        VALIDATOR.validate_fixture_set(fixture, VALIDATOR.FIXTURE_PATH)

    def test_reusable_identity_library_matches_governed_behavior_fixtures(self) -> None:
        fixture = self.read_json(VALIDATOR.BEHAVIOR_FIXTURE_PATH)
        registry = build_behavior_registry(
            fixture["family_declarations"],
            location=VALIDATOR.BEHAVIOR_FIXTURE_PATH + ".family_declarations",
        )
        self.assertGreaterEqual(len(fixture["cases"]), 10)
        for case in fixture["cases"]:
            with self.subTest(case=case["name"]):
                observed = evaluate_behavior(case["request"], registry)
                self.assertEqual(observed["status"], case["expected_status"])
                self.assertEqual(observed["computed_identity"], case["expected_identity"])
                self.assertEqual(observed["diagnostic"], case["expected_diagnostic"])

    def test_unsupported_canonical_digest_and_encoding_fail(self) -> None:
        base = VALIDATOR.EXPECTED_FIXTURE_SET["cases"][0]["declarations"][0]
        for field, value, code in (
            ("canonicalization_version", "other", "REPO-SPEC-IDENTITY-FAMILY-CANONICAL-001"),
            ("digest_algorithm", "sha-512", "REPO-SPEC-IDENTITY-FAMILY-DIGEST-001"),
            ("digest_encoding", "base64", "REPO-SPEC-IDENTITY-FAMILY-DIGEST-002"),
        ):
            with self.subTest(field=field):
                declaration = json.loads(json.dumps(base))
                declaration[field] = value
                with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
                    VALIDATOR.validate_family_declarations([declaration], field)
                self.assertTrue(str(raised.exception).startswith(code + ":"))

    def test_domain_prefix_and_cross_family_uniqueness_fail(self) -> None:
        cases = VALIDATOR.EXPECTED_FIXTURE_SET["cases"]
        codes = {
            "malformed-domain-prefix": "REPO-SPEC-IDENTITY-FAMILY-DOMAIN-001",
            "duplicate-family-construction-identity": "REPO-SPEC-IDENTITY-FAMILY-UNIQUE-001",
            "duplicate-family-name": "REPO-SPEC-IDENTITY-FAMILY-UNIQUE-002",
            "duplicate-semantic-family": "REPO-SPEC-IDENTITY-FAMILY-UNIQUE-003",
            "duplicate-domain-prefix": "REPO-SPEC-IDENTITY-FAMILY-UNIQUE-004",
        }
        for case in cases:
            if case["name"] in codes:
                with self.subTest(case=case["name"]):
                    with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
                        VALIDATOR.validate_family_declarations(case["declarations"], case["name"])
                    self.assertTrue(str(raised.exception).startswith(codes[case["name"]] + ":"))

    def test_preimage_duplicates_overlap_and_categories_fail(self) -> None:
        cases = VALIDATOR.EXPECTED_FIXTURE_SET["cases"]
        codes = {
            "duplicate-preimage-fields": "REPO-SPEC-IDENTITY-FAMILY-PREIMAGE-001",
            "overlapping-preimage-fields": "REPO-SPEC-IDENTITY-FAMILY-PREIMAGE-002",
            "invalid-subject-category": "REPO-SPEC-IDENTITY-FAMILY-CATEGORY-001",
        }
        for case in cases:
            if case["name"] in codes:
                with self.subTest(case=case["name"]):
                    with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
                        VALIDATOR.validate_family_declarations(case["declarations"], case["name"])
                    self.assertTrue(str(raised.exception).startswith(codes[case["name"]] + ":"))

    def test_later_stage_and_final_authority_fields_fail(self) -> None:
        case = next(
            item for item in VALIDATOR.EXPECTED_FIXTURE_SET["cases"]
            if item["name"] == "undeclared-later-stage-field"
        )
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.validate_family_declarations(case["declarations"], case["name"])
        self.assertTrue(str(raised.exception).startswith("REPO-SPEC-IDENTITY-FIELD-001:"))
        fixture = self.read_json(VALIDATOR.FIXTURE_PATH)
        fixture["accepted"] = True
        self.write_json(VALIDATOR.FIXTURE_PATH, fixture)
        self.assert_failure("REPO-SPEC-IDENTITY-FIELD-001")

    def test_fixture_manifest_omission_missing_and_undeclared_fail(self) -> None:
        manifest = self.read_json(VALIDATOR.MANIFEST_PATH)
        manifest["artifact_paths"].remove(VALIDATOR.FIXTURE_PATH)
        self.write_json(VALIDATOR.MANIFEST_PATH, manifest)
        self.assert_failure("REPO-SPEC-IDENTITY-MANIFEST-001")

    def test_fixture_duplicate_key_and_invalid_utf8_fail(self) -> None:
        path = self.root / VALIDATOR.FIXTURE_PATH
        raw = path.read_text(encoding="utf-8")
        path.write_text(raw.replace('"construction_status":', '"construction_identity": "duplicate",\n  "construction_status":', 1), encoding="utf-8")
        self.assert_failure("REPO-SPEC-IDENTITY-JSON-001")
        path.write_bytes(b"\xff")
        self.assert_failure("REPO-SPEC-IDENTITY-JSON-001")

if __name__ == "__main__":
    unittest.main()
