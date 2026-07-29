from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "validation/intrinsic/validate_identity_construction.py"
VECTOR_PATH = (
    ROOT
    / "validation/fixtures/identity/conformance/"
    "IDENTITY-CONFORMANCE-VECTORS.json"
)


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "identity_conformance_vector_tests", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class IdentityConformanceVectorTests(unittest.TestCase):
    def read_vectors(self) -> dict[str, object]:
        return json.loads(VECTOR_PATH.read_text(encoding="utf-8"))

    def test_vector_inventory_is_sorted_unique_and_closed(self) -> None:
        value = self.read_vectors()
        vectors = value["vectors"]
        identifiers = [item["vector_id"] for item in vectors]
        self.assertEqual(identifiers, sorted(identifiers))
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertGreaterEqual(len(vectors), 27)
        expected_fields = {
            "vector_id",
            "behavior_class",
            "classification",
            "input",
            "expected_outcome",
            "fixture_owner",
            "validator_owner",
            "coverage_tags",
        }
        for vector in vectors:
            self.assertEqual(set(vector), expected_fields)

    def test_every_vector_executes_through_intrinsic_validation(self) -> None:
        VALIDATOR.validate(ROOT)

    def test_duplicate_vector_identifier_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(ROOT, copy_root)
            path = (
                copy_root
                / "validation/fixtures/identity/conformance/"
                "IDENTITY-CONFORMANCE-VECTORS.json"
            )
            value = json.loads(path.read_text(encoding="utf-8"))
            value["vectors"][1]["vector_id"] = value["vectors"][0]["vector_id"]
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "duplicate vector identifier",
            ):
                VALIDATOR.validate(copy_root)

    def test_unknown_identity_case_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(ROOT, copy_root)
            path = (
                copy_root
                / "validation/fixtures/identity/conformance/"
                "IDENTITY-CONFORMANCE-VECTORS.json"
            )
            value = json.loads(path.read_text(encoding="utf-8"))
            target = next(
                item
                for item in value["vectors"]
                if item["input"]["kind"] == "identity-behavior-case"
            )
            target["input"]["case_name"] = "missing-governed-case"
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "unknown identity behavior case",
            ):
                VALIDATOR.validate(copy_root)

    def test_expected_outcome_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(ROOT, copy_root)
            path = (
                copy_root
                / "validation/fixtures/identity/conformance/"
                "IDENTITY-CONFORMANCE-VECTORS.json"
            )
            value = json.loads(path.read_text(encoding="utf-8"))
            target = next(
                item
                for item in value["vectors"]
                if item["input"]["kind"] == "identity-behavior-case"
            )
            target["expected_outcome"]["status"] = "rejected"
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "deterministic outcome mismatch",
            ):
                VALIDATOR.validate(copy_root)


    def test_required_coverage_is_exactly_closed(self) -> None:
        value = self.read_vectors()
        model = json.loads(
            (
                ROOT / "authoritative/conformance/IDENTITY-CONFORMANCE.json"
            ).read_text(encoding="utf-8")
        )
        observed = sorted(
            {
                tag
                for vector in value["vectors"]
                for tag in vector["coverage_tags"]
            }
        )
        self.assertEqual(observed, sorted(model["coverage_requirements"]))

    def test_missing_coverage_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(ROOT, copy_root)
            path = (
                copy_root
                / "validation/fixtures/identity/conformance/"
                "IDENTITY-CONFORMANCE-VECTORS.json"
            )
            value = json.loads(path.read_text(encoding="utf-8"))
            for vector in value["vectors"]:
                if "signed-64-bit-boundary" not in vector["coverage_tags"]:
                    continue
                replacement = next(
                    tag
                    for tag in value["vectors"][0]["coverage_tags"]
                    if tag != "signed-64-bit-boundary"
                )
                vector["coverage_tags"] = [
                    replacement
                    if tag == "signed-64-bit-boundary"
                    else tag
                    for tag in vector["coverage_tags"]
                ]
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "coverage mismatch: missing=signed-64-bit-boundary",
            ):
                VALIDATOR.validate(copy_root)

    def test_undeclared_coverage_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(ROOT, copy_root)
            path = (
                copy_root
                / "validation/fixtures/identity/conformance/"
                "IDENTITY-CONFORMANCE-VECTORS.json"
            )
            value = json.loads(path.read_text(encoding="utf-8"))
            value["vectors"][0]["coverage_tags"].append("future-undeclared-behavior")
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "coverage mismatch: undeclared=future-undeclared-behavior",
            ):
                VALIDATOR.validate(copy_root)


if __name__ == "__main__":
    unittest.main()
