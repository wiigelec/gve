from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from specs.tooling.identity import (
    IdentityFrameworkError,
    validate_identity_framework,
)

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = json.loads(
    (ROOT / "identity/GVE-IDENTITY-FRAMEWORK.json").read_text(encoding="utf-8")
)


class GoverningRevisionBindingAuthorityTests(unittest.TestCase):
    def test_finalization_requires_exact_verified_revision(self) -> None:
        family = next(
            item for item in FRAMEWORK["identity_families"]
            if item["id"] == "gve-finalization"
        )
        binding = family["preimage"]["version_bindings"][
            "governing_specification_revision"
        ]
        self.assertEqual(
            {
                "required": True,
                "source": "verification-context",
                "family_id": "gve-spec-revision",
                "comparison": "exact",
            },
            binding,
        )

    def test_non_revision_bound_families_are_explicitly_not_applicable(self) -> None:
        for family in FRAMEWORK["identity_families"]:
            binding = family["preimage"]["version_bindings"][
                "governing_specification_revision"
            ]
            if family["id"] == "gve-finalization":
                continue
            self.assertEqual(
                {
                    "required": False,
                    "source": "not-applicable",
                    "family_id": None,
                    "comparison": "not-applicable",
                },
                binding,
            )

    def test_inconsistent_required_binding_fails_closed(self) -> None:
        changed = copy.deepcopy(FRAMEWORK)
        family = next(
            item for item in changed["identity_families"]
            if item["id"] == "gve-finalization"
        )
        family["preimage"]["version_bindings"][
            "governing_specification_revision"
        ]["comparison"] = "not-applicable"
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "invalid governing revision binding",
        ):
            validate_identity_framework(changed)


if __name__ == "__main__":
    unittest.main()
