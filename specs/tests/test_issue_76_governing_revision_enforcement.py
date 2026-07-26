from __future__ import annotations

import json
import unittest
from pathlib import Path

from specs.tooling.identity import IdentityFrameworkError, compute_identity

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = json.loads(
    (ROOT / "identity/GVE-IDENTITY-FRAMEWORK.json").read_text(encoding="utf-8")
)
REVISION = "gve-spec-revision-sha256:f3596e05ce1747905ecb378cd80e3b543ec665de3df5c93a928c12f5833e6f46"
REVISION_2 = "gve-spec-revision-sha256:" + "d" * 64
RESULT_ID = "gve-authoritative-result-sha256:7686fbe851515c439de1858adb9ebd6ed93bb31a292234c75d4bb1e846f8674d"
VALUE = {
    "identity": "ignored",
    "status": "final",
    "references": [{
        "identity": RESULT_ID,
        "value": {"result_identity": "ignored", "result": "ok"},
    }],
}


class GoverningRevisionEnforcementTests(unittest.TestCase):
    def context(self, revision=REVISION):
        return [{
            "identity": revision,
            "family_id": "gve-spec-revision",
            "accepted": True,
        }]

    def compute(self, revision=REVISION, binding=REVISION, context=None):
        return compute_identity(
            FRAMEWORK,
            "gve-finalization",
            VALUE,
            version_bindings={
                "governing_specification_revision": binding,
            },
            identity_context=self.context(revision) if context is None else context,
            governing_specification_revision=revision,
        )

    def test_exact_authoritative_revision_succeeds(self):
        self.assertTrue(self.compute().startswith("gve-finalization-sha256:"))

    def test_identity_changes_with_authoritative_revision(self):
        first = self.compute()
        second = self.compute(revision=REVISION_2, binding=REVISION_2)
        self.assertNotEqual(first, second)

    def test_missing_authoritative_revision_fails(self):
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "authoritative governing specification revision is required",
        ):
            compute_identity(
                FRAMEWORK,
                "gve-finalization",
                VALUE,
                version_bindings={
                    "governing_specification_revision": REVISION,
                },
                identity_context=self.context(),
            )

    def test_verified_but_stale_revision_fails(self):
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "stale governing specification revision binding",
        ):
            self.compute(revision=REVISION, binding=REVISION_2, context=[
                *self.context(REVISION),
                *self.context(REVISION_2),
            ])

    def test_correct_revision_missing_from_context_fails(self):
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "absent from authoritative verification context",
        ):
            self.compute(context=[])


if __name__ == "__main__":
    unittest.main()
