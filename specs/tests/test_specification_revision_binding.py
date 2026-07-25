from __future__ import annotations

import copy
import unittest

from specs.tooling.revision import build_specification_revision
from specs.tooling.revision_binding import (
    SpecificationRevisionBindingError,
    validate_current_revision_binding,
    validate_historical_revision_binding,
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


class SpecificationRevisionBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.alpha = _document("GVE-LEVEL-2-ALPHA", "Alpha authority.")
        self.beta = _document("GVE-LEVEL-2-BETA", "Beta authority.")
        self.documents = [self.alpha, self.beta]
        self.revision = build_specification_revision(self.documents)

    def test_current_contract_binding_accepts_exact_revision(self) -> None:
        validate_current_revision_binding(
            self.documents,
            {"specification_revision": self.revision},
        )

    def test_current_result_binding_accepts_exact_revision(self) -> None:
        validate_current_revision_binding(
            list(reversed(self.documents)),
            {"specification_revision": self.revision},
        )

    def test_missing_current_revision_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            SpecificationRevisionBindingError,
            "lacks a specification_revision binding",
        ):
            validate_current_revision_binding(self.documents, {})

    def test_unknown_current_revision_fails_closed(self) -> None:
        unknown = copy.deepcopy(self.revision)
        unknown["identity"] = "0" * 64
        with self.assertRaisesRegex(
            SpecificationRevisionBindingError,
            "identity conflicts with its manifest",
        ):
            validate_current_revision_binding(
                self.documents,
                {"specification_revision": unknown},
            )

    def test_incomplete_current_revision_fails_closed(self) -> None:
        incomplete = copy.deepcopy(self.revision)
        incomplete["manifest"]["members"].pop()
        with self.assertRaisesRegex(
            SpecificationRevisionBindingError,
            "membership mismatch",
        ):
            validate_current_revision_binding(
                self.documents,
                {"specification_revision": incomplete},
            )

    def test_prior_contract_revision_is_stale_after_normative_change(self) -> None:
        changed = copy.deepcopy(self.beta)
        changed["summary"] = "Successor beta authority."
        with self.assertRaisesRegex(
            SpecificationRevisionBindingError,
            "conflicting specification revision content_sha256",
        ):
            validate_current_revision_binding(
                [self.alpha, changed],
                {"specification_revision": self.revision},
            )

    def test_historical_record_retains_prior_revision(self) -> None:
        changed = copy.deepcopy(self.beta)
        changed["summary"] = "Successor beta authority."
        successor = build_specification_revision([self.alpha, changed])
        self.assertNotEqual(self.revision["identity"], successor["identity"])

        validate_historical_revision_binding(
            {"specification_revision": self.revision}
        )

    def test_historical_binding_does_not_claim_current_freshness(self) -> None:
        changed = copy.deepcopy(self.beta)
        changed["summary"] = "Successor beta authority."
        validate_historical_revision_binding(
            {"specification_revision": self.revision}
        )
        with self.assertRaises(SpecificationRevisionBindingError):
            validate_current_revision_binding(
                [self.alpha, changed],
                {"specification_revision": self.revision},
            )

    def test_duplicate_historical_member_fails_closed(self) -> None:
        duplicate = copy.deepcopy(self.revision)
        duplicate["manifest"]["members"].append(
            copy.deepcopy(duplicate["manifest"]["members"][0])
        )
        with self.assertRaisesRegex(
            SpecificationRevisionBindingError,
            "duplicate historical specification revision member",
        ):
            validate_historical_revision_binding(
                {"specification_revision": duplicate}
            )


if __name__ == "__main__":
    unittest.main()
