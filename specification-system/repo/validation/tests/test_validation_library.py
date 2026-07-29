from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


CONSTRUCTION_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CONSTRUCTION_ROOT))

from validation.lib import (  # noqa: E402
    ValidationError,
    build_family_registry,
    canonical_json_bytes,
    evaluate_request,
    exact_fields,
    functional_identifier,
    load_json_bytes,
    load_json_path,
    normalized_field_name,
    require_disjoint,
    require_unique,
)


class StrictJsonTests(unittest.TestCase):
    def test_loads_strict_utf8_json(self) -> None:
        self.assertEqual(
            load_json_bytes(b'{"value":1}', source="fixture"),
            {"value": 1},
        )

    def test_rejects_duplicate_members(self) -> None:
        with self.assertRaisesRegex(
            ValidationError, r"fixture: duplicate object member value"
        ):
            load_json_bytes(b'{"value":1,"value":2}', source="fixture")

    def test_rejects_non_standard_constants(self) -> None:
        with self.assertRaisesRegex(
            ValidationError, r"fixture: non-standard JSON constant NaN"
        ):
            load_json_bytes(b'{"value":NaN}', source="fixture")

    def test_rejects_fractional_numbers(self) -> None:
        with self.assertRaisesRegex(
            ValidationError, r"fixture: non-integer JSON number 1.5"
        ):
            load_json_bytes(b'{"value":1.5}', source="fixture")

    def test_rejects_malformed_utf8(self) -> None:
        with self.assertRaisesRegex(ValidationError, r"fixture: .*utf-8"):
            load_json_bytes(b'{"value":"\xff"}', source="fixture")

    def test_path_loader_preserves_source_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "value.json"
            path.write_bytes(b'{"value":1}')
            self.assertEqual(load_json_path(path), {"value": 1})


class CanonicalJsonTests(unittest.TestCase):
    def test_orders_object_members_and_preserves_array_order(self) -> None:
        value = {"z": [2, 1], "a": "value"}
        self.assertEqual(
            canonical_json_bytes(value),
            b'{"a":"value","z":[2,1]}',
        )

    def test_uses_exact_string_escapes(self) -> None:
        self.assertEqual(
            canonical_json_bytes('a"\\\n\x01/é'),
            b'"a\\"\\\\\\n\\u0001/\xc3\xa9"',
        )

    def test_rejects_out_of_range_integer(self) -> None:
        with self.assertRaisesRegex(
            ValidationError, r"value: integer is outside signed-64-bit range"
        ):
            canonical_json_bytes(2**63)

    def test_rejects_fraction(self) -> None:
        with self.assertRaisesRegex(
            ValidationError, r"value: fractions and exponents are forbidden"
        ):
            canonical_json_bytes(1.5)

    def test_rejects_surrogate(self) -> None:
        with self.assertRaisesRegex(
            ValidationError, r"value: surrogate code point is forbidden"
        ):
            canonical_json_bytes("\ud800")


class ContractTests(unittest.TestCase):
    def test_exact_fields_rejects_unknown_before_missing(self) -> None:
        with self.assertRaisesRegex(
            ValidationError, r"object: unknown fields: extra"
        ):
            exact_fields(
                {"extra": 1},
                allowed={"required"},
                required={"required"},
                location="object",
            )

    def test_exact_fields_rejects_missing(self) -> None:
        with self.assertRaisesRegex(
            ValidationError, r"object: missing fields: required"
        ):
            exact_fields(
                {},
                allowed={"required"},
                required={"required"},
                location="object",
            )

    def test_functional_identifier(self) -> None:
        self.assertEqual(
            functional_identifier("validation-library", location="identity"),
            "validation-library",
        )
        with self.assertRaisesRegex(
            ValidationError, r"identity: invalid functional identifier"
        ):
            functional_identifier("Validation_Library", location="identity")

    def test_normalized_field_name(self) -> None:
        self.assertEqual(
            normalized_field_name("field_name", location="field"),
            "field_name",
        )
        with self.assertRaisesRegex(
            ValidationError, r"field: invalid normalized field name"
        ):
            normalized_field_name("field-name", location="field")

    def test_unique_and_disjoint_sequences(self) -> None:
        self.assertEqual(require_unique(["a", "b"], location="values"), ["a", "b"])
        with self.assertRaisesRegex(
            ValidationError, r"values: duplicate value at index 1"
        ):
            require_unique(["a", "a"], location="values")
        with self.assertRaisesRegex(
            ValidationError, r"fields: overlapping values: b"
        ):
            require_disjoint(["a", "b"], ["b", "c"], location="fields")


def object_family(name: str = "leaf", prefix: str = "leaf-v1") -> dict[str, object]:
    return {
        "family_construction_identity": f"{name}-family-construction",
        "family_name": name,
        "semantic_domain": "repository-specification",
        "object_kind": "object",
        "canonicalization_version": "canonical-json-v1",
        "digest_algorithm": "sha-256",
        "digest_encoding": "lowercase-hexadecimal",
        "domain_prefix": prefix,
        "included_preimage_fields": ["name", "identity"],
        "omitted_preimage_fields": [],
        "own_identity": {"mode": "omit-own-identity", "field": "identity"},
        "references": {
            "mode": "none",
            "identity_field": None,
            "value_field": None,
            "allowed_family_names": [],
        },
        "aggregate": None,
        "verification": {"mode": "none", "context_source": "none"},
        "unavailable_capabilities": [
            "governing-revision-binding",
            "manifest-bootstrap",
            "sealing",
            "acceptance",
        ],
    }


def aggregate_family(ordering: str = "unordered") -> dict[str, object]:
    return {
        "family_construction_identity": f"{ordering}-set-family-construction",
        "family_name": f"{ordering}-set",
        "semantic_domain": "repository-specification",
        "object_kind": f"{ordering}-aggregate",
        "canonicalization_version": "canonical-json-v1",
        "digest_algorithm": "sha-256",
        "digest_encoding": "lowercase-hexadecimal",
        "domain_prefix": f"{ordering}-set-v1",
        "included_preimage_fields": ["members", "identity"],
        "omitted_preimage_fields": [],
        "own_identity": {"mode": "omit-own-identity", "field": "identity"},
        "references": {
            "mode": "by-identity",
            "identity_field": "identity",
            "value_field": None,
            "allowed_family_names": ["leaf"],
        },
        "aggregate": {
            "membership_field": "members",
            "member_family_names": ["leaf"],
            "ordering": ordering,
            "duplicate_policy": "reject",
            "empty_policy": "reject",
            "closure_boundary": "direct",
            "cycle_policy": "reject",
        },
        "verification": {
            "mode": "verified-identity-set",
            "context_source": "caller-supplied",
        },
        "unavailable_capabilities": [
            "governing-revision-binding",
            "manifest-bootstrap",
            "sealing",
            "acceptance",
        ],
    }


class IdentityLibraryTests(unittest.TestCase):
    def test_derives_and_verifies_object_identity(self) -> None:
        registry = build_family_registry([object_family()])
        derived = evaluate_request(
            {
                "mode": "derive",
                "family_name": "leaf",
                "value": {"name": "alpha"},
                "supplied_identity": None,
                "verification_context": [],
            },
            registry,
        )
        self.assertEqual(derived["status"], "derived")
        identity = derived["computed_identity"]
        verified = evaluate_request(
            {
                "mode": "verify",
                "family_name": "leaf",
                "value": {"name": "alpha", "identity": identity},
                "supplied_identity": identity,
                "verification_context": [],
            },
            registry,
        )
        self.assertEqual(verified["status"], "verified")
        self.assertEqual(verified["computed_identity"], identity)

    def test_rejects_contradictory_own_identity(self) -> None:
        registry = build_family_registry([object_family()])
        result = evaluate_request(
            {
                "mode": "derive",
                "family_name": "leaf",
                "value": {
                    "name": "alpha",
                    "identity": {"family": "leaf", "encoded_digest": "0" * 64},
                },
                "supplied_identity": None,
                "verification_context": [],
            },
            registry,
        )
        self.assertEqual(result["diagnostic"], "contradictory-own-identity")

    def test_unordered_aggregate_sorts_by_identity(self) -> None:
        registry = build_family_registry([object_family(), aggregate_family()])
        first = evaluate_request(
            {
                "mode": "derive",
                "family_name": "leaf",
                "value": {"name": "alpha"},
                "supplied_identity": None,
                "verification_context": [],
            },
            registry,
        )["computed_identity"]
        second = evaluate_request(
            {
                "mode": "derive",
                "family_name": "leaf",
                "value": {"name": "beta"},
                "supplied_identity": None,
                "verification_context": [],
            },
            registry,
        )["computed_identity"]
        context = [
            {"identity": first, "family_name": "leaf", "verified": True},
            {"identity": second, "family_name": "leaf", "verified": True},
        ]
        forward = evaluate_request(
            {
                "mode": "derive",
                "family_name": "unordered-set",
                "value": {"members": [{"identity": first}, {"identity": second}]},
                "supplied_identity": None,
                "verification_context": context,
            },
            registry,
        )
        reverse = evaluate_request(
            {
                "mode": "derive",
                "family_name": "unordered-set",
                "value": {"members": [{"identity": second}, {"identity": first}]},
                "supplied_identity": None,
                "verification_context": context,
            },
            registry,
        )
        self.assertEqual(forward["computed_identity"], reverse["computed_identity"])
        self.assertEqual(forward["evidence"]["aggregate_ordering"], "unordered")

    def test_aggregate_rejects_duplicate_and_missing_context(self) -> None:
        registry = build_family_registry([object_family(), aggregate_family()])
        identity = evaluate_request(
            {
                "mode": "derive",
                "family_name": "leaf",
                "value": {"name": "alpha"},
                "supplied_identity": None,
                "verification_context": [],
            },
            registry,
        )["computed_identity"]
        duplicate = evaluate_request(
            {
                "mode": "derive",
                "family_name": "unordered-set",
                "value": {"members": [{"identity": identity}, {"identity": identity}]},
                "supplied_identity": None,
                "verification_context": [
                    {"identity": identity, "family_name": "leaf", "verified": True}
                ],
            },
            registry,
        )
        self.assertEqual(duplicate["diagnostic"], "duplicate-aggregate-member")
        missing = evaluate_request(
            {
                "mode": "derive",
                "family_name": "unordered-set",
                "value": {"members": [{"identity": identity}]},
                "supplied_identity": None,
                "verification_context": [],
            },
            registry,
        )
        self.assertEqual(missing["diagnostic"], "missing-reference-context")

    def test_family_registry_rejects_later_capability_expansion(self) -> None:
        declaration = object_family()
        declaration["unavailable_capabilities"] = []
        with self.assertRaisesRegex(ValidationError, r"policy mismatch"):
            build_family_registry([declaration])


if __name__ == "__main__":
    unittest.main()
