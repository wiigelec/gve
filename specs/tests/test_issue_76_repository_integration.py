from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from specs.tooling.validate_identity import (
    IdentityIntegrationError,
    validate_repository_identity,
    validate_revision_tooling_binding,
)


ROOT = Path(__file__).resolve().parents[1]


def _manifest() -> dict:
    return json.loads(
        (ROOT / "GVE-SPECIFICATION-SET.json").read_text(encoding="utf-8")
    )


def _vectors() -> dict:
    return json.loads(
        (
            ROOT / "tests/fixtures/issue_76/identity_vectors.json"
        ).read_text(encoding="utf-8")
    )


class Issue76RepositoryIntegrationTests(unittest.TestCase):
    def test_repository_identity_integration_passes(self) -> None:
        validate_repository_identity(ROOT)

    def test_manifest_binding_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _manifest()
            manifest.pop("identity_framework")
            (root / "GVE-SPECIFICATION-SET.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                IdentityIntegrationError,
                "lacks identity_framework binding",
            ):
                validate_repository_identity(root)

    def test_manifest_revision_identity_format_is_domain_separated(self) -> None:
        manifest = _manifest()
        manifest["identity_format"] = (
            "gve-canonical-json-v1+sha256:lowercase-hex"
        )
        with self.assertRaisesRegex(
            IdentityIntegrationError,
            "identity format conflicts with revision tooling",
        ):
            validate_revision_tooling_binding(manifest, _vectors())

    def test_document_tooling_vector_is_required(self) -> None:
        vectors = _vectors()
        vectors["positive"] = [
            vector
            for vector in vectors["positive"]
            if vector["id"] != "spec-document-tooling-vector"
        ]
        with self.assertRaisesRegex(
            IdentityIntegrationError,
            "spec-document-tooling-vector must exist exactly once",
        ):
            validate_revision_tooling_binding(_manifest(), vectors)

    def test_revision_tooling_vector_mismatch_fails_closed(self) -> None:
        vectors = copy.deepcopy(_vectors())
        vector = next(
            item
            for item in vectors["positive"]
            if item["id"] == "spec-revision-tooling-vector"
        )
        vector["expected_identity"] = (
            "gve-spec-revision-sha256:" + "0" * 64
        )
        with self.assertRaisesRegex(
            IdentityIntegrationError,
            "revision tooling conflicts with fixed vector",
        ):
            validate_revision_tooling_binding(_manifest(), vectors)


if __name__ == "__main__":
    unittest.main()
