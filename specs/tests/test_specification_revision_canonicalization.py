from __future__ import annotations

import copy
import unittest

from specs.tooling.canonical_json import canonical_json, sha256_identity
from specs.tooling.revision import (
    SpecificationRevisionError,
    build_specification_revision,
    document_content_identity,
    validate_specification_revision,
)


def _document(identifier: str, summary: str) -> dict:
    return {
        "specification": {
            "id": identifier,
            "version": "1.0.0",
            "status": "normative",
        },
        "summary": summary,
        "requirements": [],
    }


class SpecificationRevisionCanonicalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.alpha = _document("GVE-ALPHA", "Alpha é.")
        self.beta = _document("GVE-BETA", "Beta.")

    def test_revision_declares_complete_identity_format(self) -> None:
        revision = build_specification_revision([self.beta, self.alpha])
        self.assertEqual(revision["canonicalization"], "gve-canonical-json-v1")
        self.assertEqual(revision["algorithm"], "sha256")
        self.assertEqual(
            revision["identity_format"],
            "gve-canonical-json-v1+sha256:lowercase-hex",
        )

    def test_document_identity_matches_fixed_canonical_bytes(self) -> None:
        document = {"z": 2, "a": "é"}
        expected_bytes = b'{"a":"\xc3\xa9","z":2}'
        self.assertEqual(canonical_json(document), expected_bytes)
        self.assertEqual(document_content_identity(document), sha256_identity(document))
        self.assertEqual(
            document_content_identity(document),
            "e8d6670b3c4e0636657d7b2dc771a552342df4c66f507ea504a2d5901ce6891f",
        )

    def test_revision_identity_matches_fixed_manifest_vector(self) -> None:
        revision = build_specification_revision([self.alpha])
        manifest = revision["manifest"]
        self.assertEqual(revision["identity"], sha256_identity(manifest))
        self.assertEqual(
            revision["identity"],
            "b75f248af07c7ccc6ef0828214e25ca0d7fc166e7789bfb65a686601abe6af09",
        )

    def test_floating_point_normative_content_fails_closed(self) -> None:
        document = copy.deepcopy(self.alpha)
        document["unsupported"] = 1.5
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "floating-point values are not canonicalizable",
        ):
            build_specification_revision([document])

    def test_unknown_canonicalization_fails_closed(self) -> None:
        revision = build_specification_revision([self.alpha])
        revision["canonicalization"] = "implementation-native-json"
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "canonicalization is missing or unsupported",
        ):
            validate_specification_revision([self.alpha], revision)

    def test_unknown_identity_format_fails_closed(self) -> None:
        revision = build_specification_revision([self.alpha])
        revision["identity_format"] = "sha256:unspecified"
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "identity format is missing or unsupported",
        ):
            validate_specification_revision([self.alpha], revision)

    def test_uppercase_digest_fails_closed(self) -> None:
        revision = build_specification_revision([self.alpha])
        revision["identity"] = revision["identity"].upper()
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "identity is missing or malformed",
        ):
            validate_specification_revision([self.alpha], revision)


if __name__ == "__main__":
    unittest.main()
