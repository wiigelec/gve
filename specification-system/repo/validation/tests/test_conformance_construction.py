from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "validation/intrinsic/validate_skeleton.py"
BOUNDARY_PATH = ROOT / "authoritative/conformance/CONFORMANCE-BOUNDARY.json"
MODEL_PATH = ROOT / "authoritative/conformance/IDENTITY-CONFORMANCE.json"
SCHEMA_PATH = (
    ROOT
    / "authoritative/schemas/conformance/"
    "IDENTITY-CONFORMANCE-CONSTRUCTION-SCHEMA.json"
)
MANIFEST_PATH = ROOT / "REPOSITORY-SPECIFICATION-SET.json"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "conformance_construction_validator_tests", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class ConformanceConstructionTests(unittest.TestCase):
    def read_json(self, path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_models_are_closed_construction_only(self) -> None:
        boundary = self.read_json(BOUNDARY_PATH)
        model = self.read_json(MODEL_PATH)
        schema = self.read_json(SCHEMA_PATH)
        self.assertEqual(
            boundary["construction_identity"],
            "conformance-boundary-construction",
        )
        self.assertIs(boundary["authority_boundary"]["accepted-conformance"], False)
        self.assertIs(boundary["authority_boundary"]["vectors-define-new-semantics"], False)
        self.assertEqual(
            model["construction_identity"],
            "identity-conformance-construction",
        )
        self.assertIs(model["vector_envelope"]["closed"], True)
        self.assertEqual(
            schema["target_construction_identity"],
            "identity-conformance-construction",
        )
        self.assertIs(schema["closed"], True)

    def test_manifest_declares_all_conformance_artifacts(self) -> None:
        manifest = self.read_json(MANIFEST_PATH)
        self.assertIn(
            "conformance-boundary-construction",
            manifest["artifact_classes"],
        )
        self.assertIn(
            "identity-conformance-construction",
            manifest["artifact_classes"],
        )
        self.assertIn(
            "identity-conformance-construction-schema",
            manifest["artifact_classes"],
        )
        self.assertIn(
            "specification-identities-conformance-construction",
            manifest["artifact_classes"],
        )
        self.assertIn(
            "specification-identities-conformance-construction-schema",
            manifest["artifact_classes"],
        )
        self.assertIn(
            "authoritative/conformance/IDENTITY-CONFORMANCE.json",
            manifest["artifact_paths"],
        )
        self.assertIn(
            "authoritative/schemas/conformance/"
            "IDENTITY-CONFORMANCE-CONSTRUCTION-SCHEMA.json",
            manifest["artifact_paths"],
        )
        self.assertIn(
            "authoritative/conformance/SPECIFICATION-IDENTITIES-CONFORMANCE.json",
            manifest["artifact_paths"],
        )
        self.assertIn(
            "authoritative/schemas/conformance/"
            "SPECIFICATION-IDENTITIES-CONFORMANCE-SCHEMA.json",
            manifest["artifact_paths"],
        )

    def test_intrinsic_validator_rejects_authority_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(ROOT, copy_root)
            path = copy_root / "authoritative/conformance/CONFORMANCE-BOUNDARY.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["authority_boundary"]["accepted-conformance"] = True
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "authority boundary mismatch",
            ):
                VALIDATOR.validate(copy_root)

    def test_intrinsic_validator_rejects_open_vector_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(ROOT, copy_root)
            path = copy_root / "authoritative/conformance/IDENTITY-CONFORMANCE.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["vector_envelope"]["closed"] = False
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "closed object required",
            ):
                VALIDATOR.validate(copy_root)


if __name__ == "__main__":
    unittest.main()
