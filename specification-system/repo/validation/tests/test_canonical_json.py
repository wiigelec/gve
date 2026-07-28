from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "validation/intrinsic/validate_canonical_json.py"
FIXTURES = ROOT / "validation/fixtures/identity/canonical-json"

SPEC = importlib.util.spec_from_file_location("canonical_json_validator", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CanonicalJsonTests(unittest.TestCase):
    def test_fixed_positive_vectors(self) -> None:
        vectors = (
            ("object-reordered.input.json", "object-reordered.canonical.json"),
            ("unicode.input.json", "unicode.canonical.json"),
        )
        for source_name, expected_name in vectors:
            with self.subTest(source=source_name):
                source = (FIXTURES / source_name).read_bytes()
                expected = (FIXTURES / expected_name).read_bytes()
                self.assertEqual(MODULE.canonicalize_bytes(source), expected)
                self.assertFalse(expected.startswith(b"\xef\xbb\xbf"))
                self.assertFalse(expected.endswith(b"\n"))

    def test_object_order_is_source_independent(self) -> None:
        left = MODULE.canonicalize_bytes(b'{"b":2,"a":1}')
        right = MODULE.canonicalize_bytes(b'{ "a" : 1, "b" : 2 }')
        self.assertEqual(left, right)
        self.assertEqual(left, b'{"a":1,"b":2}')

    def test_arrays_preserve_order(self) -> None:
        self.assertEqual(MODULE.canonicalize_bytes(b'[3,2,1]'), b'[3,2,1]')

    def test_signed_64_bit_integer_boundary(self) -> None:
        self.assertEqual(
            MODULE.canonicalize_bytes(b'[-9223372036854775808,9223372036854775807]'),
            b'[-9223372036854775808,9223372036854775807]',
        )
        for source in (b'9223372036854775808', b'-9223372036854775809'):
            with self.subTest(source=source):
                with self.assertRaisesRegex(
                    MODULE.CanonicalJsonFailure,
                    "^CANONICAL_JSON_UNSUPPORTED_NUMBER:",
                ):
                    MODULE.canonicalize_bytes(source)

    def test_negative_fixtures_fail_with_stable_codes(self) -> None:
        cases = (
            ("duplicate-key.input.json", "CANONICAL_JSON_DUPLICATE_KEY"),
            ("floating-point.input.json", "CANONICAL_JSON_UNSUPPORTED_NUMBER"),
            ("surrogate.input.json", "CANONICAL_JSON_INVALID_UNICODE"),
        )
        for filename, code in cases:
            with self.subTest(filename=filename):
                with self.assertRaises(MODULE.CanonicalJsonFailure) as caught:
                    MODULE.canonicalize_bytes((FIXTURES / filename).read_bytes())
                self.assertEqual(caught.exception.code, code)

    def test_non_standard_constants_fail(self) -> None:
        for source in (b'NaN', b'Infinity', b'-Infinity'):
            with self.subTest(source=source):
                with self.assertRaisesRegex(
                    MODULE.CanonicalJsonFailure,
                    "^CANONICAL_JSON_NON_STANDARD_CONSTANT:",
                ):
                    MODULE.canonicalize_bytes(source)

    def test_invalid_utf8_and_bom_fail(self) -> None:
        cases = (
            (b'{"value":"\xff"}', "CANONICAL_JSON_INVALID_UTF8"),
            (b'\xef\xbb\xbf{}', "CANONICAL_JSON_INVALID_UTF8"),
        )
        for source, code in cases:
            with self.subTest(source=source):
                with self.assertRaises(MODULE.CanonicalJsonFailure) as caught:
                    MODULE.canonicalize_bytes(source)
                self.assertEqual(caught.exception.code, code)

    def test_malformed_json_fails(self) -> None:
        with self.assertRaisesRegex(
            MODULE.CanonicalJsonFailure,
            "^CANONICAL_JSON_MALFORMED:",
        ):
            MODULE.canonicalize_bytes(b'{"missing":}')

    def test_python_values_reject_floats_and_surrogates(self) -> None:
        for value, code in (
            (1.0, "CANONICAL_JSON_UNSUPPORTED_NUMBER"),
            ("\ud800", "CANONICAL_JSON_INVALID_UNICODE"),
        ):
            with self.subTest(value=repr(value)):
                with self.assertRaises(MODULE.CanonicalJsonFailure) as caught:
                    MODULE.canonical_json_bytes(value)
                self.assertEqual(caught.exception.code, code)

    def test_cli_has_exact_stdout_and_deterministic_failure(self) -> None:
        success = subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), str(FIXTURES / "object-reordered.input.json")],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(success.returncode, 0)
        self.assertEqual(
            success.stdout,
            (FIXTURES / "object-reordered.canonical.json").read_bytes(),
        )
        self.assertEqual(success.stderr, b"")

        failure = subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), str(FIXTURES / "duplicate-key.input.json")],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(failure.returncode, 1)
        self.assertEqual(failure.stdout, b"")
        self.assertEqual(
            failure.stderr,
            b"CANONICAL_JSON_DUPLICATE_KEY: a\n",
        )

    def test_unsupported_cli_version_fails(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR_PATH),
                str(FIXTURES / "object-reordered.input.json"),
                "--canonicalization-version",
                "unknown",
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, b"")
        self.assertEqual(
            completed.stderr,
            b"CANONICAL_JSON_UNSUPPORTED_VERSION: unknown\n",
        )

    def test_validator_has_no_maintained_product_import(self) -> None:
        source = VALIDATOR_PATH.read_text(encoding="utf-8")
        self.assertNotIn("maintained product", source.lower())


if __name__ == "__main__":
    unittest.main()
