from __future__ import annotations

import json
import unittest
from pathlib import Path

from specs.tooling.identity import IdentityFrameworkError, compute_identity

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = json.loads(
    (ROOT / "identity/GVE-IDENTITY-FRAMEWORK.json").read_text(encoding="utf-8")
)


class ByIdentityEnforcementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract_value = {"identity": "ignored", "contract": "alpha"}
        self.contract_identity = compute_identity(
            FRAMEWORK, "gve-contract", self.contract_value
        )
        self.effect_value = {
            "identity": "ignored",
            "operation": "read",
            "references": [{"identity": self.contract_identity}],
        }
        self.context = [{
            "identity": self.contract_identity,
            "family_id": "gve-contract",
            "accepted": True,
        }]

    def test_verified_by_identity_reference_succeeds(self) -> None:
        identity = compute_identity(
            FRAMEWORK,
            "gve-effect",
            self.effect_value,
            identity_context=self.context,
        )
        self.assertTrue(identity.startswith("gve-effect-sha256:"))

    def test_missing_context_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "verification context is required",
        ):
            compute_identity(FRAMEWORK, "gve-effect", self.effect_value)

    def test_identity_absent_from_context_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "absent from authoritative verification context",
        ):
            compute_identity(
                FRAMEWORK,
                "gve-effect",
                self.effect_value,
                identity_context=[],
            )

    def test_valid_looking_fabricated_identity_fails_without_authority(self) -> None:
        fabricated = {
            "identity": "ignored",
            "operation": "read",
            "references": [{
                "identity": "gve-contract-sha256:" + "a" * 64
            }],
        }
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "absent from authoritative verification context",
        ):
            compute_identity(
                FRAMEWORK,
                "gve-effect",
                fabricated,
                identity_context=[],
            )

    def test_context_family_conflict_fails_closed(self) -> None:
        with self.assertRaises(IdentityFrameworkError):
            compute_identity(
                FRAMEWORK,
                "gve-effect",
                self.effect_value,
                identity_context=[{
                    "identity": self.contract_identity,
                    "family_id": "gve-effect",
                    "accepted": True,
                }],
            )

    def test_specification_revision_members_require_context(self) -> None:
        document = {
            "specification": {
                "id": "GVE-ALPHA",
                "version": "1.0.0",
                "status": "normative",
            },
            "requirements": [],
        }
        document_identity = compute_identity(
            FRAMEWORK, "gve-spec-document", document
        )
        revision = {
            "schema_version": 1,
            "members": [{
                "id": "GVE-ALPHA",
                "version": "1.0.0",
                "document_identity": document_identity,
            }],
        }
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "verification context is required",
        ):
            compute_identity(
                FRAMEWORK,
                "gve-spec-revision",
                revision,
                member_identities=[document_identity],
            )
        identity = compute_identity(
            FRAMEWORK,
            "gve-spec-revision",
            revision,
            member_identities=[document_identity],
            identity_context=[{
                "identity": document_identity,
                "family_id": "gve-spec-document",
                "accepted": True,
            }],
        )
        self.assertTrue(identity.startswith("gve-spec-revision-sha256:"))


if __name__ == "__main__":
    unittest.main()
