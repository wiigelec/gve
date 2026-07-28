from __future__ import annotations

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

    def test_fixed_behavior_vectors_pass(self) -> None:
        VALIDATOR.validate_behavior_fixture_set(
            self.fixture, VALIDATOR.BEHAVIOR_FIXTURE_PATH
        )

    def test_own_identity_is_omitted(self) -> None:
        first = self.evaluate("own-identity-omission")
        second = self.evaluate("own-identity-value-does-not-change-result")
        self.assertEqual(first["computed_identity"], second["computed_identity"])
        self.assertEqual(
            first["evidence"]["own_identity_field_omitted"], "identity"
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

    def test_ordered_and_unordered_aggregate_rules(self) -> None:
        ordered_ab = self.evaluate("ordered-aggregate-ab")["computed_identity"]
        ordered_ba = self.evaluate("ordered-aggregate-ba")["computed_identity"]
        unordered_ab = self.evaluate("unordered-aggregate-ab")["computed_identity"]
        unordered_ba = self.evaluate("unordered-aggregate-ba")["computed_identity"]
        self.assertNotEqual(ordered_ab, ordered_ba)
        self.assertEqual(unordered_ab, unordered_ba)

    def test_fail_closed_aggregate_and_verification_diagnostics(self) -> None:
        expected = {
            "duplicate-aggregate-member-rejects": "duplicate-aggregate-member",
            "empty-aggregate-rejects": "empty-aggregate-forbidden",
            "self-membership-rejects": "self-membership",
            "reference-family-mismatch-rejects": "reference-family-mismatch",
            "supplied-identity-mismatch-rejects": "supplied-identity-mismatch",
            "aggregate-cycle-rejects": "aggregate-cycle",
        }
        for name, diagnostic in expected.items():
            with self.subTest(name=name):
                result = self.evaluate(name)
                self.assertEqual(result["status"], "rejected")
                self.assertEqual(result["diagnostic"], diagnostic)

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
