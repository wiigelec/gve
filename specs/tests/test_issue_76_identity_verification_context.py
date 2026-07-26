from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from specs.tooling.identity import (
    IdentityFrameworkError,
    render_identity_framework_markdown,
    validate_identity_framework,
)

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_PATH = ROOT / "identity/GVE-IDENTITY-FRAMEWORK.json"
MARKDOWN_PATH = ROOT / "identity/GVE-IDENTITY-FRAMEWORK.md"


class IdentityVerificationContextAuthorityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.framework = json.loads(FRAMEWORK_PATH.read_text(encoding="utf-8"))

    def test_context_is_external_and_fail_closed(self) -> None:
        context = self.framework["identity_verification_context"]
        self.assertTrue(context["external_to_canonical_preimage"])
        for key in (
            "missing_context_policy",
            "missing_identity_policy",
            "unknown_family_policy",
            "family_conflict_policy",
            "unaccepted_identity_policy",
            "duplicate_identity_policy",
        ):
            self.assertEqual("reject", context[key])

    def test_by_identity_declarations_require_verified_identity_set(self) -> None:
        for family in self.framework["identity_families"]:
            preimage = family["preimage"]
            if preimage["reference_encoding"] == "by-identity":
                self.assertEqual(
                    {
                        "mode": "verified-identity-set",
                        "required": True,
                        "context_source": "caller-supplied",
                        "context_binding": "external-to-canonical-preimage",
                    },
                    preimage["identity_verification"],
                )
            aggregate = family["aggregate"]
            if aggregate and aggregate["member_reference_mode"] == "by-identity":
                self.assertEqual(
                    "verified-identity-set",
                    aggregate["identity_verification"]["mode"],
                )
                self.assertTrue(aggregate["identity_verification"]["required"])

    def test_inconsistent_declaration_fails_closed(self) -> None:
        changed = copy.deepcopy(self.framework)
        effect = next(
            item for item in changed["identity_families"]
            if item["id"] == "gve-effect"
        )
        effect["preimage"]["identity_verification"]["required"] = False
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "inconsistent identity verification semantics",
        ):
            validate_identity_framework(changed)

    def test_markdown_is_deterministic_projection(self) -> None:
        self.assertEqual(
            MARKDOWN_PATH.read_text(encoding="utf-8"),
            render_identity_framework_markdown(self.framework),
        )


if __name__ == "__main__":
    unittest.main()
