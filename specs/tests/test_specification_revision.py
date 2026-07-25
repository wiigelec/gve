from __future__ import annotations

import copy
import unittest

from specs.tooling.revision import (
    SpecificationRevisionError,
    build_specification_revision,
    validate_specification_revision,
)


def _document(identifier: str, text: str) -> dict:
    return {
        "$schema": "../../schemas/GVE-LEVEL.schema.json",
        "specification": {
            "id": identifier,
            "level": 2,
            "title": identifier,
            "version": "1.0.0",
            "status": "normative",
            "parent": "GVE-LEVEL-2",
        },
        "document": {
            "role": "subordinate",
            "root": "GVE-LEVEL-2",
            "imports": [],
        },
        "summary": text,
        "definitions": [],
        "requirements": [],
        "relationships": [],
        "scope": {"includes": [text], "excludes": ["None"]},
    }


class SpecificationRevisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.alpha = _document("GVE-LEVEL-2-ALPHA", "Alpha authority.")
        self.beta = _document("GVE-LEVEL-2-BETA", "Beta authority.")

    def test_repeated_construction_is_stable(self) -> None:
        first = build_specification_revision([self.alpha, self.beta])
        second = build_specification_revision([self.alpha, self.beta])
        self.assertEqual(first, second)

    def test_discovery_order_does_not_change_revision(self) -> None:
        forward = build_specification_revision([self.alpha, self.beta])
        reverse = build_specification_revision([self.beta, self.alpha])
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [member["id"] for member in forward["manifest"]["members"]],
            ["GVE-LEVEL-2-ALPHA", "GVE-LEVEL-2-BETA"],
        )

    def test_normative_content_change_changes_revision_without_version_change(self) -> None:
        changed = copy.deepcopy(self.beta)
        changed["summary"] = "Changed beta authority."
        original = build_specification_revision([self.alpha, self.beta])
        successor = build_specification_revision([self.alpha, changed])
        self.assertEqual(
            self.beta["specification"]["version"],
            changed["specification"]["version"],
        )
        self.assertNotEqual(original["identity"], successor["identity"])

    def test_duplicate_member_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "duplicate specification revision member GVE-LEVEL-2-ALPHA",
        ):
            build_specification_revision([self.alpha, self.alpha])

    def test_non_normative_member_fails_closed(self) -> None:
        draft = copy.deepcopy(self.beta)
        draft["specification"]["status"] = "draft"
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "must be normative; found draft",
        ):
            build_specification_revision([self.alpha, draft])

    def test_empty_revision_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "requires at least one normative document",
        ):
            build_specification_revision([])

    def test_exact_revision_validates(self) -> None:
        revision = build_specification_revision([self.alpha, self.beta])
        validate_specification_revision([self.beta, self.alpha], revision)

    def test_manifest_omission_fails_closed(self) -> None:
        revision = build_specification_revision([self.alpha, self.beta])
        revision["manifest"]["members"].pop()
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "membership mismatch",
        ):
            validate_specification_revision([self.alpha, self.beta], revision)

    def test_manifest_unexpected_member_fails_closed(self) -> None:
        revision = build_specification_revision([self.alpha, self.beta])
        revision["manifest"]["members"].append(
            {
                "id": "GVE-LEVEL-2-GAMMA",
                "version": "1.0.0",
                "content_sha256": "0" * 64,
            }
        )
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "unexpected=\\['GVE-LEVEL-2-GAMMA'\\]",
        ):
            validate_specification_revision([self.alpha, self.beta], revision)

    def test_manifest_duplicate_member_fails_closed(self) -> None:
        revision = build_specification_revision([self.alpha, self.beta])
        revision["manifest"]["members"].append(
            copy.deepcopy(revision["manifest"]["members"][0])
        )
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "duplicate specification revision member",
        ):
            validate_specification_revision([self.alpha, self.beta], revision)

    def test_conflicting_content_identity_fails_closed(self) -> None:
        revision = build_specification_revision([self.alpha, self.beta])
        revision["manifest"]["members"][0]["content_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "conflicting specification revision content_sha256",
        ):
            validate_specification_revision([self.alpha, self.beta], revision)

    def test_prior_revision_is_stale_after_normative_change(self) -> None:
        revision = build_specification_revision([self.alpha, self.beta])
        changed = copy.deepcopy(self.beta)
        changed["summary"] = "Successor beta authority."
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "conflicting specification revision content_sha256",
        ):
            validate_specification_revision([self.alpha, changed], revision)

    def test_manifest_identity_conflict_fails_closed(self) -> None:
        revision = build_specification_revision([self.alpha, self.beta])
        revision["identity"] = "0" * 64
        with self.assertRaisesRegex(
            SpecificationRevisionError,
            "identity conflicts with its manifest",
        ):
            validate_specification_revision([self.alpha, self.beta], revision)


if __name__ == "__main__":
    unittest.main()
