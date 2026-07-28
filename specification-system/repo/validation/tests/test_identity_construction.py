from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = SOURCE_ROOT / "validation/intrinsic/validate_identity_construction.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "identity_construction_validator_tests", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


class IdentityConstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE_ROOT, self.root, symlinks=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_failure(self, code: str, *, root: Path | None = None) -> str:
        with self.assertRaises(VALIDATOR.ValidationFailure) as raised:
            VALIDATOR.validate(root or self.root)
        message = str(raised.exception)
        self.assertTrue(message.startswith(code + ":"), message)
        return message

    def read_json(self, relative: str, *, root: Path | None = None) -> dict:
        return json.loads(((root or self.root) / relative).read_text(encoding="utf-8"))

    def write_json(self, relative: str, value: dict, *, root: Path | None = None) -> None:
        ((root or self.root) / relative).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def test_identity_construction_passes(self) -> None:
        VALIDATOR.validate(self.root)

    def test_each_identity_artifact_is_required(self) -> None:
        for relative in VALIDATOR.ARTIFACTS:
            with self.subTest(relative=relative):
                copy = Path(self.temporary.name) / Path(relative).stem
                shutil.copytree(self.root, copy, symlinks=True)
                (copy / relative).unlink()
                self.assert_failure("REPO-SPEC-IDENTITY-PATH-001", root=copy)

    def test_each_supporting_marker_is_required(self) -> None:
        for relative in VALIDATOR.SUPPORTING_PATHS:
            with self.subTest(relative=relative):
                copy = Path(self.temporary.name) / relative.replace("/", "-")
                shutil.copytree(self.root, copy, symlinks=True)
                (copy / relative).unlink()
                self.assert_failure("REPO-SPEC-IDENTITY-PATH-001", root=copy)

    def test_malformed_json_fails(self) -> None:
        (self.root / VALIDATOR.ARTIFACTS[0]).write_text("{", encoding="utf-8")
        self.assert_failure("REPO-SPEC-IDENTITY-JSON-001")

    def test_non_standard_json_constant_fails(self) -> None:
        path = self.root / VALIDATOR.ARTIFACTS[0]
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                '"normative": false', '"normative": NaN'
            ),
            encoding="utf-8",
        )
        self.assert_failure("REPO-SPEC-IDENTITY-JSON-001")

    def test_unknown_field_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["unrecognized"] = True
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-FIELD-001")

    def test_missing_field_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        del value["responsibility"]
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-FIELD-002")

    def test_each_forbidden_claim_field_fails_with_claim_code(self) -> None:
        for claim in sorted(VALIDATOR.FORBIDDEN_CLAIM_KEYS):
            with self.subTest(claim=claim):
                copy = Path(self.temporary.name) / claim.replace("_", "-")
                shutil.copytree(self.root, copy, symlinks=True)
                relative = VALIDATOR.ARTIFACTS[0]
                value = self.read_json(relative, root=copy)
                value[claim] = True
                self.write_json(relative, value, root=copy)
                self.assert_failure("REPO-SPEC-IDENTITY-CLAIM-001", root=copy)

    def test_invalid_identity_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["construction_identity"] = "Invalid Identity"
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-IDENTITY-001")

    def test_work_derived_identity_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["construction_identity"] = "identity-phase-construction"
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-NAME-001")

    def test_duplicate_identity_fails_with_duplicate_code(self) -> None:
        first, second = VALIDATOR.ARTIFACTS[:2]
        first_value = self.read_json(first)
        second_value = self.read_json(second)
        second_value["construction_identity"] = first_value["construction_identity"]
        self.write_json(second, second_value)
        self.assert_failure("REPO-SPEC-IDENTITY-IDENTITY-003")

    def test_unexpected_identity_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["construction_identity"] = "alternate-identity-construction"
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-IDENTITY-002")

    def test_invalid_status_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["construction_status"] = "candidate"
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-STATUS-001")

    def test_normative_true_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["normative"] = True
        self.write_json(relative, value)
        self.assert_failure("REPO-SPEC-IDENTITY-STATUS-002")

    def test_manifest_omission_fails(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        manifest = self.read_json(VALIDATOR.MANIFEST_PATH)
        manifest["artifact_paths"].remove(relative)
        self.write_json(VALIDATOR.MANIFEST_PATH, manifest)
        self.assert_failure("REPO-SPEC-IDENTITY-MANIFEST-001")

    def test_manifest_declared_missing_identity_artifact_fails(self) -> None:
        manifest = self.read_json(VALIDATOR.MANIFEST_PATH)
        manifest["artifact_paths"].append(
            "authoritative/identity/MISSING-IDENTITY.json"
        )
        self.write_json(VALIDATOR.MANIFEST_PATH, manifest)
        self.assert_failure("REPO-SPEC-IDENTITY-MANIFEST-003")

    def test_undeclared_identity_participant_fails(self) -> None:
        source = self.root / VALIDATOR.ARTIFACTS[0]
        target = self.root / "authoritative/identity/EXTRA-IDENTITY.json"
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        self.assert_failure("REPO-SPEC-IDENTITY-MANIFEST-004")

    def test_duplicate_manifest_path_fails(self) -> None:
        manifest = self.read_json(VALIDATOR.MANIFEST_PATH)
        manifest["artifact_paths"].append(manifest["artifact_paths"][0])
        self.write_json(VALIDATOR.MANIFEST_PATH, manifest)
        self.assert_failure("REPO-SPEC-IDENTITY-MANIFEST-002")

    def test_manifest_absolute_path_fails(self) -> None:
        manifest = self.read_json(VALIDATOR.MANIFEST_PATH)
        manifest["artifact_paths"].append("/tmp/identity.json")
        self.write_json(VALIDATOR.MANIFEST_PATH, manifest)
        self.assert_failure("REPO-SPEC-IDENTITY-PATH-003")

    def test_manifest_traversal_path_fails(self) -> None:
        manifest = self.read_json(VALIDATOR.MANIFEST_PATH)
        manifest["artifact_paths"].append("../identity.json")
        self.write_json(VALIDATOR.MANIFEST_PATH, manifest)
        self.assert_failure("REPO-SPEC-IDENTITY-PATH-003")

    def test_work_derived_manifest_path_fails(self) -> None:
        manifest = self.read_json(VALIDATOR.MANIFEST_PATH)
        manifest["artifact_paths"].append(
            "authoritative/identity/phase/IDENTITY.json"
        )
        self.write_json(VALIDATOR.MANIFEST_PATH, manifest)
        self.assert_failure("REPO-SPEC-IDENTITY-NAME-001")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support is required")
    def test_supporting_marker_symlink_escape_fails(self) -> None:
        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        (outside / "README.md").write_text("outside\n", encoding="utf-8")
        identity_dir = self.root / "authoritative/schemas/identity"
        shutil.rmtree(identity_dir)
        identity_dir.symlink_to(outside, target_is_directory=True)
        self.assert_failure("REPO-SPEC-IDENTITY-PATH-002")

    def test_product_reference_in_explanatory_text_is_not_semantically_rejected(self) -> None:
        relative = VALIDATOR.ARTIFACTS[0]
        value = self.read_json(relative)
        value["expected_relationships"].append(
            "gve-product-family is cited only as excluded provenance"
        )
        self.write_json(relative, value)
        VALIDATOR.validate(self.root)

    def test_main_returns_deterministic_failure_exit(self) -> None:
        (self.root / VALIDATOR.ARTIFACTS[0]).unlink()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = VALIDATOR.main(["--root", str(self.root)])
        self.assertEqual(result, 1)
        self.assertTrue(
            stderr.getvalue().startswith(
                "identity construction validation failed: REPO-SPEC-IDENTITY-PATH-001:"
            ),
            stderr.getvalue(),
        )


if __name__ == "__main__":
    unittest.main()
