from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from specs.tooling.identity import (
    IdentityFrameworkError,
    canonical_json_bytes,
    compute_identity,
    validate_fixed_identity_vectors,
    render_identity_framework_markdown,
    validate_identity_family_registry,
    verify_identity,
    validate_identity_framework,
)


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = ROOT / "identity/GVE-IDENTITY-FRAMEWORK.json"
SCHEMA = ROOT / "schemas/GVE-IDENTITY-FRAMEWORK.schema.json"
VECTORS = ROOT / "tests/fixtures/issue_76/identity_vectors.json"
MARKDOWN = ROOT / "identity/GVE-IDENTITY-FRAMEWORK.md"


class Issue76IdentityFrameworkCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.framework = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.vectors = json.loads(VECTORS.read_text(encoding="utf-8"))

    def assert_rejected(self, framework: dict, expected: str) -> None:
        with self.assertRaisesRegex(IdentityFrameworkError, expected):
            validate_identity_framework(framework)

    def test_framework_matches_schema(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        errors = sorted(
            Draft202012Validator(self.schema).iter_errors(self.framework),
            key=lambda error: list(error.path),
        )
        self.assertEqual([], errors)

    def test_framework_passes_semantic_validation(self) -> None:
        validate_identity_framework(self.framework)

    def test_rejects_wrong_governing_authority(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["authority"]["governing_specification"] = "GVE-LEVEL-0"
        self.assert_rejected(framework, "incorrect governing specification")

    def test_rejects_semantically_bare_family_pattern(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["representation"]["family_pattern"] = "^[a-z0-9]+$"
        self.assert_rejected(framework, "pattern rejects gve-effect")

    def test_rejects_missing_canonicalization_version(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["canonicalization_versions"] = []
        self.assert_rejected(framework, "gve-canonical-json-v1 is required")

    def test_rejects_duplicate_digest_algorithm(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["digest_algorithms"].append(
            copy.deepcopy(framework["digest_algorithms"][0])
        )
        self.assert_rejected(framework, "duplicate digest algorithm")

    def test_rejects_inconsistent_sha256_declaration(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["digest_algorithms"][0]["encoded_length"] = 63
        self.assert_rejected(framework, "sha256 declaration is inconsistent")

    def test_rejects_implicit_embedded_identity_handling(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["embedded_identity_rules"][
            "implicit_handling_prohibited"
        ] = False
        self.assert_rejected(framework, "implicit embedded identity handling")

    def test_rejects_ambiguous_reference_semantics(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["reference_semantics"]["ambiguous_reference_prohibited"] = False
        self.assert_rejected(framework, "ambiguous reference semantics")

    def test_rejects_incomplete_aggregate_semantics(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["aggregate_semantics"]["required_for_aggregate_kinds"].remove(
            "closure_boundary"
        )
        self.assert_rejected(framework, "aggregate semantic inventory is incomplete")

    def test_rejects_permitted_aggregate_cycles(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["aggregate_semantics"]["cycle_policy"] = "permit"
        self.assert_rejected(framework, "aggregate cycles must be rejected")

    def test_rejects_incomplete_fail_closed_inventory(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["fail_closed_conditions"].remove("cross-domain-substitution")
        self.assert_rejected(framework, "fail-closed condition inventory is incomplete")

    def test_rejects_disabled_framework_invariant(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["framework_invariants"][
            "cross_domain_substitution_prohibited"
        ] = False
        self.assert_rejected(framework, "every framework invariant must be enabled")

    def test_family_registry_passes_semantic_validation(self) -> None:
        validate_identity_family_registry(self.framework)

    def test_rejects_incomplete_family_registry(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["identity_families"].pop()
        self.assert_rejected(framework, "identity family registry is incomplete")

    def test_rejects_cross_domain_prefix_substitution(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["identity_families"][0]["domain_separation_prefix"] = (
            "gve/effect/v1\x00"
        )
        self.assert_rejected(framework, "prefix does not match its domain")

    def test_rejects_duplicate_domain_prefix(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["identity_families"][1]["domain_separation_prefix"] = (
            framework["identity_families"][0]["domain_separation_prefix"]
        )
        self.assert_rejected(framework, "duplicate domain-separation prefix")

    def test_rejects_unknown_family_canonicalization(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["identity_families"][0]["canonicalization_version"] = "stale-v0"
        self.assert_rejected(framework, "unknown canonicalization version")

    def test_rejects_unknown_family_digest_algorithm(self) -> None:
        framework = copy.deepcopy(self.framework)
        framework["identity_families"][0]["digest_algorithm"] = "sha1"
        self.assert_rejected(framework, "unknown digest algorithm")

    def test_rejects_aggregate_without_rules(self) -> None:
        framework = copy.deepcopy(self.framework)
        revision = next(
            family
            for family in framework["identity_families"]
            if family["id"] == "gve-spec-revision"
        )
        revision["aggregate"] = None
        self.assert_rejected(framework, "requires aggregate rules")

    def test_rejects_self_referential_aggregate(self) -> None:
        framework = copy.deepcopy(self.framework)
        revision = next(
            family
            for family in framework["identity_families"]
            if family["id"] == "gve-spec-revision"
        )
        revision["aggregate"]["member_family_ids"] = ["gve-spec-revision"]
        self.assert_rejected(framework, "self-referential")

    def test_rejects_circular_aggregate_registry(self) -> None:
        framework = copy.deepcopy(self.framework)
        revision = next(
            family
            for family in framework["identity_families"]
            if family["id"] == "gve-spec-revision"
        )
        composition = next(
            family
            for family in framework["identity_families"]
            if family["id"] == "gve-governance-composition"
        )
        revision["aggregate"]["member_family_ids"] = [
            "gve-governance-composition"
        ]
        composition["aggregate"]["member_family_ids"] = ["gve-spec-revision"]
        self.assert_rejected(framework, "circular aggregate")

    def test_fixed_identity_vectors_pass(self) -> None:
        validate_fixed_identity_vectors(self.framework, self.vectors)

    def test_unordered_aggregate_identity_is_order_independent(self) -> None:
        vector = next(
            item
            for item in self.vectors["positive"]
            if item["id"] == "unordered-spec-revision"
        )
        first = compute_identity(
            self.framework,
            vector["family_id"],
            vector["value"],
            member_identities=vector["member_identities"],
        )
        second = compute_identity(
            self.framework,
            vector["family_id"],
            vector["value"],
            member_identities=list(reversed(vector["member_identities"])),
        )
        self.assertEqual(first, second)

    def test_ordered_aggregate_identity_is_order_sensitive(self) -> None:
        vector = next(
            item
            for item in self.vectors["positive"]
            if item["id"] == "ordered-governance-composition"
        )
        first = compute_identity(
            self.framework,
            vector["family_id"],
            vector["value"],
            member_identities=vector["member_identities"],
        )
        second = compute_identity(
            self.framework,
            vector["family_id"],
            vector["value"],
            member_identities=list(reversed(vector["member_identities"])),
        )
        self.assertNotEqual(first, second)

    def test_own_identity_field_is_omitted(self) -> None:
        value = {"identity": "one", "operation": "write", "target": "x"}
        changed = {"identity": "two", "operation": "write", "target": "x"}
        self.assertEqual(
            compute_identity(self.framework, "gve-effect", value),
            compute_identity(self.framework, "gve-effect", changed),
        )

    def test_cross_domain_substitution_is_rejected(self) -> None:
        effect = next(
            item
            for item in self.vectors["positive"]
            if item["id"] == "effect-object"
        )
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "claimed identity family does not match",
        ):
            verify_identity(
                self.framework,
                "gve-evidence",
                effect["expected_identity"],
                effect["value"],
            )

    def test_floating_point_is_not_canonicalizable(self) -> None:
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "floating-point values are not canonicalizable",
        ):
            canonical_json_bytes({"value": 1.5})

    def test_non_string_object_key_is_not_canonicalizable(self) -> None:
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "non-string object member names",
        ):
            canonical_json_bytes({1: "value"})

    def test_unknown_family_is_rejected(self) -> None:
        with self.assertRaisesRegex(IdentityFrameworkError, "unknown identity family"):
            compute_identity(self.framework, "gve-unknown", {"value": 1})

    def test_aggregate_requires_complete_membership(self) -> None:
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "requires complete member identities",
        ):
            compute_identity(
                self.framework,
                "gve-spec-revision",
                {"revision": "alpha"},
            )

    def test_duplicate_aggregate_members_are_rejected(self) -> None:
        member = self.vectors["positive"][0]["expected_identity"]
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "duplicate members",
        ):
            compute_identity(
                self.framework,
                "gve-spec-revision",
                {"revision": "alpha"},
                member_identities=[member, member],
            )

    def test_mutated_fixed_vector_is_rejected(self) -> None:
        vectors = copy.deepcopy(self.vectors)
        vectors["positive"][0]["expected_identity"] = (
            "gve-effect-sha256:" + "0" * 64
        )
        self.assert_rejected_vectors(vectors, "does not match")

    def assert_rejected_vectors(self, vectors: dict, expected: str) -> None:
        with self.assertRaisesRegex(IdentityFrameworkError, expected):
            validate_fixed_identity_vectors(self.framework, vectors)

    def test_repository_integration_is_normative(self) -> None:
        self.assertEqual(
            "repository-integrated",
            self.framework["authority"]["integration_state"],
        )
        self.assertTrue(
            self.framework["repository_integration"][
                "normative_manifest_binding_required"
            ]
        )
        self.assertTrue(
            self.framework["repository_integration"][
                "deterministic_markdown_projection_required"
            ]
        )

    def test_identity_framework_markdown_is_deterministic(self) -> None:
        self.assertEqual(
            render_identity_framework_markdown(self.framework),
            MARKDOWN.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
