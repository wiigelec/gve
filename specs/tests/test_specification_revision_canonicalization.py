from __future__ import annotations

import copy
import unittest

from specs.tooling.canonical_json import canonical_json
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
            "gve-spec-revision-sha256:<digest>",
        )

    def test_document_identity_matches_fixed_domain_vector(self) -> None:
        document = {"z": 2, "a": "é"}
        expected_bytes = b'{"a":"\xc3\xa9","z":2}'
        self.assertEqual(canonical_json(document), expected_bytes)
        self.assertEqual(
            document_content_identity(document),
            "gve-spec-document-sha256:"
            "2c54188d9647239feb9954cd4f44018c8e8573b0809d6b20cac763aed2185188",
        )

    def test_revision_identity_matches_fixed_domain_vector(self) -> None:
        revision = build_specification_revision([self.alpha])
        self.assertEqual(
            revision["identity"],
            "gve-spec-revision-sha256:"
            "f3596e05ce1747905ecb378cd80e3b543ec665de3df5c93a928c12f5833e6f46",
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
        prefix, digest = revision["identity"].split(":", 1)
        revision["identity"] = prefix + ":" + digest.upper()
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "identity is missing or malformed",
        ):
            validate_specification_revision([self.alpha], revision)


if __name__ == "__main__":
    unittest.main()
