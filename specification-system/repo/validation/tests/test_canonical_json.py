from __future__ import annotations

import ast
import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "validation/intrinsic/validate_canonical_json.py"
IDENTITY_VALIDATOR_PATH = ROOT / "validation/intrinsic/validate_identity_construction.py"
MODEL_PATH = ROOT / "authoritative/identity/CANONICAL-JSON.json"
SCHEMA_PATH = ROOT / "authoritative/schemas/identity/CANONICAL-JSON-CONSTRUCTION-SCHEMA.json"
FIXTURES = ROOT / "validation/fixtures/identity/canonical-json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_module("canonical_json_validator", VALIDATOR_PATH)
IDENTITY = load_module("identity_construction_validator", IDENTITY_VALIDATOR_PATH)


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

    def test_object_order_is_source_independent_and_recursive(self) -> None:
        left = MODULE.canonicalize_bytes(b'{"b":{"d":4,"c":3},"a":1}')
        right = MODULE.canonicalize_bytes(b'{"a":1,"b":{"c":3,"d":4}}')
        self.assertEqual(left, right)
        self.assertEqual(left, b'{"a":1,"b":{"c":3,"d":4}}')

    def test_arrays_preserve_order(self) -> None:
        self.assertEqual(MODULE.canonicalize_bytes(b'[3,2,1]'), b'[3,2,1]')

    def test_signed_64_bit_integer_boundary_and_negative_zero(self) -> None:
        self.assertEqual(
            MODULE.canonicalize_bytes(b'[-9223372036854775808,9223372036854775807,-0]'),
            b'[-9223372036854775808,9223372036854775807,0]',
        )
        for source in (b'9223372036854775808', b'-9223372036854775809'):
            with self.subTest(source=source):
                with self.assertRaisesRegex(
                    MODULE.CanonicalJsonFailure,
                    "^REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-NUMBER:",
                ):
                    MODULE.canonicalize_bytes(source)

    def test_fraction_and_exponent_forms_fail(self) -> None:
        for source in (b"1.5", b"1e2", b"-2E-3"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(
                    MODULE.CanonicalJsonFailure,
                    "^REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-NUMBER:",
                ):
                    MODULE.canonicalize_bytes(source)

    def test_nonminimal_source_integer_is_malformed_json(self) -> None:
        with self.assertRaisesRegex(
            MODULE.CanonicalJsonFailure,
            "^REPO-SPEC-CANONICAL-JSON-MALFORMED:",
        ):
            MODULE.canonicalize_bytes(b"01")

    def test_strings_escape_exactly_and_do_not_normalize_unicode(self) -> None:
        source = '"quote:\\" slash:/ reverse:\\\\ controls:\\b\\f\\n\\r\\t composed:é decomposed:é"'.encode()
        expected = '"quote:\\" slash:/ reverse:\\\\ controls:\\b\\f\\n\\r\\t composed:é decomposed:é"'.encode()
        self.assertEqual(MODULE.canonicalize_bytes(source), expected)
        self.assertNotEqual("é".encode("utf-8"), "é".encode("utf-8"))

    def test_negative_fixtures_fail_with_stable_codes(self) -> None:
        cases = (
            ("duplicate-key.input.json", "REPO-SPEC-CANONICAL-JSON-DUPLICATE-KEY"),
            ("floating-point.input.json", "REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-NUMBER"),
            ("surrogate.input.json", "REPO-SPEC-CANONICAL-JSON-INVALID-UNICODE"),
        )
        for filename, code in cases:
            with self.subTest(filename=filename):
                with self.assertRaises(MODULE.CanonicalJsonFailure) as caught:
                    MODULE.canonicalize_bytes((FIXTURES / filename).read_bytes())
                self.assertEqual(caught.exception.code, code)

    def test_non_standard_constants_fail(self) -> None:
        for source in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(
                    MODULE.CanonicalJsonFailure,
                    "^REPO-SPEC-CANONICAL-JSON-NON-STANDARD-CONSTANT:",
                ):
                    MODULE.canonicalize_bytes(source)

    def test_invalid_utf8_and_bom_fail(self) -> None:
        for source in (b'{"value":"\xff"}', b"\xef\xbb\xbf{}"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(
                    MODULE.CanonicalJsonFailure,
                    "^REPO-SPEC-CANONICAL-JSON-INVALID-UTF8:",
                ):
                    MODULE.canonicalize_bytes(source)

    def test_malformed_json_fails(self) -> None:
        with self.assertRaisesRegex(
            MODULE.CanonicalJsonFailure,
            "^REPO-SPEC-CANONICAL-JSON-MALFORMED:",
        ):
            MODULE.canonicalize_bytes(b'{"missing":}')

    def test_python_values_reject_floats_surrogates_and_non_string_keys(self) -> None:
        for value, code in (
            (1.0, "REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-NUMBER"),
            ("\ud800", "REPO-SPEC-CANONICAL-JSON-INVALID-UNICODE"),
            ({1: "value"}, "REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-VALUE"),
        ):
            with self.subTest(value=repr(value)):
                with self.assertRaises(MODULE.CanonicalJsonFailure) as caught:
                    MODULE.canonical_json_bytes(value)
                self.assertEqual(caught.exception.code, code)

    def test_cli_has_exact_stdout_and_deterministic_failure(self) -> None:
        success = subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), str(FIXTURES / "object-reordered.input.json")],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(success.returncode, 0)
        self.assertEqual(success.stdout, (FIXTURES / "object-reordered.canonical.json").read_bytes())
        self.assertEqual(success.stderr, b"")

        failure = subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), str(FIXTURES / "duplicate-key.input.json")],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(failure.returncode, 1)
        self.assertEqual(failure.stdout, b"")
        self.assertEqual(failure.stderr, b"REPO-SPEC-CANONICAL-JSON-DUPLICATE-KEY: a\n")

    def test_unsupported_cli_version_fails(self) -> None:
        completed = subprocess.run(
            [
                sys.executable, str(VALIDATOR_PATH),
                str(FIXTURES / "object-reordered.input.json"),
                "--canonicalization-version", "unknown",
            ],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stdout, b"")
        self.assertEqual(
            completed.stderr,
            b"REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-VERSION: unknown\n",
        )

    def test_canonicalizer_imports_only_standard_library_modules(self) -> None:
        allowed = {"argparse", "collections", "json", "pathlib", "sys", "typing", "__future__"}
        tree = ast.parse(VALIDATOR_PATH.read_text(encoding="utf-8"))
        observed = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                observed.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                observed.add((node.module or "").split(".", 1)[0])
        self.assertEqual(observed - allowed, set())

    def test_canonical_model_excludes_validator_interface_policy(self) -> None:
        model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("rejection_rules", model)
        decisions = model["decision_basis"]["repository_generic_decisions"]
        self.assertNotIn("deterministic-diagnostic-codes", decisions)
        self.assertNotIn("failure-exit-status", decisions)

    def test_every_canonical_construction_claim_is_closed(self) -> None:
        model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
        constrained = IDENTITY.EXPECTED_CANONICAL_CONSTRAINTS
        for field, allowed in constrained.items():
            with self.subTest(field=field):
                changed = copy.deepcopy(model)
                changed[field] = {"unexpected": True}
                with self.assertRaisesRegex(
                    IDENTITY.ValidationFailure,
                    "^REPO-SPEC-IDENTITY-CANONICAL-001:",
                ):
                    IDENTITY.validate_canonical(changed, "canonical")

                changed = copy.deepcopy(model)
                if isinstance(changed[field], dict):
                    changed[field]["unexpected"] = True
                    with self.assertRaisesRegex(
                        IDENTITY.ValidationFailure,
                        "^REPO-SPEC-IDENTITY-CANONICAL-001:",
                    ):
                        IDENTITY.validate_canonical(changed, "canonical")

    def test_schema_constraints_are_exact_and_closed(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        IDENTITY.validate_schema(schema, "schema")
        mutations = (
            ("target_construction_identity", "other"),
            ("closed", False),
            ("field_constraints", {}),
            ("forbidden_claim_fields", []),
        )
        for field, replacement in mutations:
            with self.subTest(field=field):
                changed = copy.deepcopy(schema)
                changed[field] = replacement
                with self.assertRaisesRegex(
                    IDENTITY.ValidationFailure,
                    "^REPO-SPEC-IDENTITY-SCHEMA-001:",
                ):
                    IDENTITY.validate_schema(changed, "schema")

        changed = copy.deepcopy(schema)
        changed["required_fields"].append("unexpected")
        with self.assertRaisesRegex(
            IDENTITY.ValidationFailure,
            "^REPO-SPEC-IDENTITY-SCHEMA-001:",
        ):
            IDENTITY.validate_schema(changed, "schema")


if __name__ == "__main__":
    unittest.main()
