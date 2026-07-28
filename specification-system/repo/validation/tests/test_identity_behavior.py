from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SOURCE_ROOT / "validation/intrinsic/validate_identity_construction.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "identity_behavior_validator_tests", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class IdentityBehaviorConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(
            (SOURCE_ROOT / VALIDATOR.BEHAVIOR_FIXTURE_PATH).read_text(encoding="utf-8")
        )
        cls.registry = VALIDATOR._behavior_family_registry(
            cls.fixture["family_declarations"], "fixture.family_declarations"
        )
        cls.cases = {case["name"]: case for case in cls.fixture["cases"]}

    def evaluate(self, name: str) -> dict:
        return VALIDATOR.evaluate_behavior_request(
            self.cases[name]["request"], self.registry
        )

    def assert_validation_code(self, code: str, callable_) -> None:
        with self.assertRaises(VALIDATOR.ValidationFailure) as caught:
            callable_()
        self.assertTrue(str(caught.exception).startswith(code + ":"))

    def test_fixed_behavior_vectors_pass(self) -> None:
        VALIDATOR.validate_behavior_fixture_set(
            self.fixture, VALIDATOR.BEHAVIOR_FIXTURE_PATH
        )

    def test_own_identity_omission_matching_and_contradiction(self) -> None:
        omitted = self.evaluate("own-identity-omission")
        matching = self.evaluate("matching-own-identity-verifies")
        contradictory = self.evaluate("contradictory-own-identity-rejects")
        self.assertEqual(omitted["computed_identity"], matching["computed_identity"])
        self.assertEqual(matching["status"], "verified")
        self.assertEqual(
            omitted["evidence"]["own_identity_field_omitted"], "identity"
        )
        self.assertEqual(contradictory["status"], "rejected")
        self.assertEqual(
            contradictory["diagnostic"], "contradictory-own-identity"
        )

    def test_reference_modes_are_distinct_and_verified(self) -> None:
        by_identity = self.evaluate("by-identity-reference-verifies")
        embedded = self.evaluate("identity-plus-value-recomputes")
        self.assertEqual(by_identity["status"], "verified")
        self.assertEqual(embedded["status"], "verified")
        self.assertEqual(
            self.evaluate("missing-by-identity-context-rejects")["diagnostic"],
            "missing-reference-context",
        )
        self.assertEqual(
            self.evaluate("identity-plus-value-mismatch-rejects")["diagnostic"],
            "embedded-reference-identity-mismatch",
        )

    def test_ordered_unordered_and_empty_aggregate_rules(self) -> None:
        ordered_ab = self.evaluate("ordered-aggregate-ab")["computed_identity"]
        ordered_ba = self.evaluate("ordered-aggregate-ba")["computed_identity"]
        unordered_ab = self.evaluate("unordered-aggregate-ab")["computed_identity"]
        unordered_ba = self.evaluate("unordered-aggregate-ba")["computed_identity"]
        self.assertNotEqual(ordered_ab, ordered_ba)
        self.assertEqual(unordered_ab, unordered_ba)
        self.assertEqual(self.evaluate("empty-aggregate-allowed")["status"], "derived")
        self.assertEqual(
            self.evaluate("empty-aggregate-rejects")["diagnostic"],
            "empty-aggregate-forbidden",
        )

    def test_fail_closed_aggregate_and_verification_diagnostics(self) -> None:
        expected = {
            "duplicate-aggregate-member-rejects": "duplicate-aggregate-member",
            "self-membership-rejects": "self-membership",
            "reference-family-mismatch-rejects": "reference-family-mismatch",
            "supplied-identity-mismatch-rejects": "supplied-identity-mismatch",
            "direct-cycle-rejects": "aggregate-cycle",
            "indirect-cycle-rejects": "aggregate-cycle",
        }
        for name, diagnostic in expected.items():
            with self.subTest(name=name):
                result = self.evaluate(name)
                self.assertEqual(result["status"], "rejected")
                self.assertEqual(result["diagnostic"], diagnostic)

    def test_request_and_context_shapes_fail_closed(self) -> None:
        request = copy.deepcopy(self.cases["own-identity-omission"]["request"])
        request["unknown"] = True
        self.assert_validation_code(
            "REPO-SPEC-IDENTITY-FIELD-001",
            lambda: VALIDATOR.evaluate_behavior_request(request, self.registry),
        )

        request = copy.deepcopy(self.cases["by-identity-reference-verifies"]["request"])
        request["verification_context"].append(
            copy.deepcopy(request["verification_context"][0])
        )
        self.assert_validation_code(
            "REPO-SPEC-IDENTITY-BEHAVIOR-CONTEXT-001",
            lambda: VALIDATOR.evaluate_behavior_request(request, self.registry),
        )

        request = copy.deepcopy(self.cases["by-identity-reference-verifies"]["request"])
        request["verification_context"][0]["verified"] = False
        self.assert_validation_code(
            "REPO-SPEC-IDENTITY-BEHAVIOR-CONTEXT-001",
            lambda: VALIDATOR.evaluate_behavior_request(request, self.registry),
        )

    def test_family_declaration_policies_fail_closed(self) -> None:
        mutations = [
            ("references", "mode", "unsupported"),
            ("references", "value_field", "value"),
            ("verification", "context_source", "embedded-value"),
            ("aggregate", "ordering", "unordered"),
            ("aggregate", "closure_boundary", "transitive"),
            ("aggregate", "duplicate_policy", "allow"),
            ("aggregate", "cycle_policy", "allow"),
            ("aggregate", "membership_field", "../members"),
        ]
        ordered = next(
            item for item in self.fixture["family_declarations"]
            if item["family_name"] == "ordered-bundle"
        )
        link = next(
            item for item in self.fixture["family_declarations"]
            if item["family_name"] == "link"
        )
        for section, field, value in mutations:
            with self.subTest(section=section, field=field, value=value):
                declarations = copy.deepcopy(self.fixture["family_declarations"])
                target_name = "ordered-bundle" if section == "aggregate" else "link"
                target = next(
                    item for item in declarations if item["family_name"] == target_name
                )
                target[section][field] = value
                self.assert_validation_code(
                    "REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001",
                    lambda declarations=declarations: VALIDATOR._behavior_family_registry(
                        declarations, "mutated.family_declarations"
                    ),
                )

    def test_malformed_reference_and_unknown_family_fail_closed(self) -> None:
        request = copy.deepcopy(self.cases["by-identity-reference-verifies"]["request"])
        request["value"]["references"][0]["extra"] = True
        result = VALIDATOR.evaluate_behavior_request(request, self.registry)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["diagnostic"], "malformed-reference")

        request = copy.deepcopy(self.cases["own-identity-omission"]["request"])
        request["family_name"] = "unknown-family"
        result = VALIDATOR.evaluate_behavior_request(request, self.registry)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["diagnostic"], "unknown-family")

    def test_evidence_is_deterministic_and_construction_only(self) -> None:
        first = self.evaluate("ordered-aggregate-ab")
        second = self.evaluate("ordered-aggregate-ab")
        self.assertEqual(first, second)
        self.assertEqual(
            set(first["evidence"]),
            {
                "family_name",
                "canonicalization_version",
                "digest_algorithm",
                "domain_prefix",
                "own_identity_field_omitted",
                "reference_count",
                "aggregate_member_count",
                "aggregate_ordering",
                "canonical_value_sha256",
                "computed_identity",
            },
        )


if __name__ == "__main__":
    unittest.main()
