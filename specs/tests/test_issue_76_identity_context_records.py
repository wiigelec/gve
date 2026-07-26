from __future__ import annotations

import json
import unittest
from pathlib import Path

from specs.tooling.identity import (
    IdentityFrameworkError,
    compute_identity,
    validate_identity_context,
)

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = json.loads(
    (ROOT / "identity/GVE-IDENTITY-FRAMEWORK.json").read_text(encoding="utf-8")
)


class IdentityContextRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.value = {"identity": "ignored", "contract": "alpha"}
        self.identity = compute_identity(FRAMEWORK, "gve-contract", self.value)

    def record(self, **changes):
        record = {
            "identity": self.identity,
            "family_id": "gve-contract",
            "accepted": True,
        }
        record.update(changes)
        return record

    def test_valid_context_returns_typed_identity_map(self) -> None:
        self.assertEqual(
            {self.identity: "gve-contract"},
            validate_identity_context(FRAMEWORK, [self.record()]),
        )

    def test_missing_context_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "identity verification context is required",
        ):
            validate_identity_context(FRAMEWORK, None)

    def test_unknown_identity_family_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "unknown family",
        ):
            validate_identity_context(
                FRAMEWORK,
                [self.record(family_id="gve-unknown")],
            )

    def test_context_family_conflict_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "family conflicts",
        ):
            validate_identity_context(
                FRAMEWORK,
                [self.record(family_id="gve-effect")],
            )

    def test_unaccepted_identity_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "unaccepted identity",
        ):
            validate_identity_context(
                FRAMEWORK,
                [self.record(accepted=False)],
            )

    def test_duplicate_identity_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "duplicate identity",
        ):
            validate_identity_context(
                FRAMEWORK,
                [self.record(), self.record()],
            )

    def test_conflicting_duplicate_fails_before_ambiguity_can_enter(self) -> None:
        with self.assertRaises(IdentityFrameworkError):
            validate_identity_context(
                FRAMEWORK,
                [
                    self.record(),
                    self.record(family_id="gve-effect"),
                ],
            )


if __name__ == "__main__":
    unittest.main()
