from __future__ import annotations

import hashlib
import unittest

from specs.tooling.canonical_json import (
    CANONICALIZATION,
    DIGEST_ALGORITHM,
    IDENTITY_FORMAT,
    CanonicalJsonError,
    canonical_json,
    sha256_identity,
)


class CanonicalJsonTests(unittest.TestCase):
    def test_algorithm_identifiers_are_explicit(self) -> None:
        self.assertEqual(CANONICALIZATION, "gve-canonical-json-v1")
        self.assertEqual(DIGEST_ALGORITHM, "sha256")
        self.assertEqual(
            IDENTITY_FORMAT,
            "gve-canonical-json-v1+sha256:lowercase-hex",
        )

    def test_fixed_composite_vector(self) -> None:
        value = {
            "z": [None, True, False, -12, "é"],
            "a": "quote=\" slash=\\ line=\n control=\x01",
        }
        expected = (
            b'{"a":"quote=\\\" slash=\\\\ line=\\n control=\\u0001",'
            b'"z":[null,true,false,-12,"\xc3\xa9"]}'
        )
        self.assertEqual(canonical_json(value), expected)
        self.assertEqual(
            sha256_identity(value),
            "b5181b201f50046d75a14ad62c07586da14bd57d3f38280c2de0fa67c0392fc0",
        )

    def test_object_declaration_order_is_irrelevant(self) -> None:
        left = {"beta": 2, "alpha": 1}
        right = {"alpha": 1, "beta": 2}
        expected = b'{"alpha":1,"beta":2}'
        self.assertEqual(canonical_json(left), expected)
        self.assertEqual(canonical_json(right), expected)

    def test_arrays_retain_declared_order(self) -> None:
        self.assertEqual(canonical_json([2, 1]), b"[2,1]")
        self.assertNotEqual(canonical_json([2, 1]), canonical_json([1, 2]))

    def test_strings_are_not_unicode_normalized(self) -> None:
        composed = "é"
        decomposed = "e\u0301"
        self.assertEqual(canonical_json(composed), b'"\xc3\xa9"')
        self.assertEqual(canonical_json(decomposed), b'"e\xcc\x81"')
        self.assertNotEqual(sha256_identity(composed), sha256_identity(decomposed))

    def test_integer_vector_uses_minimal_decimal_form(self) -> None:
        value = [0, -1, 9223372036854775807, -9223372036854775808]
        expected = b"[0,-1,9223372036854775807,-9223372036854775808]"
        self.assertEqual(canonical_json(value), expected)
        self.assertEqual(
            hashlib.sha256(expected).hexdigest(),
            sha256_identity(value),
        )

    def test_floating_point_values_fail_closed(self) -> None:
        for value in (0.0, -0.0, 1.5, float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    CanonicalJsonError,
                    "floating-point values are not canonicalizable",
                ):
                    canonical_json(value)

    def test_non_string_object_member_name_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            CanonicalJsonError,
            "object member names must be strings",
        ):
            canonical_json({1: "value"})

    def test_surrogate_code_point_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            CanonicalJsonError,
            "surrogate code points are not canonicalizable",
        ):
            canonical_json("\ud800")

    def test_non_json_value_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            CanonicalJsonError,
            "unsupported canonical JSON value type: set",
        ):
            canonical_json({"value"})


if __name__ == "__main__":
    unittest.main()
