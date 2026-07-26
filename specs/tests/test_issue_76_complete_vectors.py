from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from specs.tooling.identity import (
    IdentityFrameworkError,
    validate_fixed_identity_vectors,
)


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = json.loads(
    (ROOT / "identity/GVE-IDENTITY-FRAMEWORK.json").read_text(encoding="utf-8")
)
VECTORS = json.loads(
    (
        ROOT / "tests/fixtures/issue_76/identity_vectors.json"
    ).read_text(encoding="utf-8")
)


class Issue76CompleteVectorSurfaceTests(unittest.TestCase):
    def test_all_registered_families_have_positive_vectors(self) -> None:
        registered = {
            family["id"] for family in FRAMEWORK["identity_families"]
        }
        covered = {
            vector["family_id"] for vector in VECTORS["positive"]
        }
        self.assertEqual(registered, covered)
        self.assertEqual(11, len(registered))

    def test_required_negative_categories_are_covered(self) -> None:
        required = {
            "omitted-prefix",
            "stale-version",
            "mismatched-family",
            "ambiguous-reference",
            "incomplete-membership",
            "cycle",
        }
        covered = {
            vector.get("category") for vector in VECTORS["negative"]
        }
        self.assertTrue(required.issubset(covered))

    def test_cycle_scenarios_are_fixed_vectors(self) -> None:
        scenarios = {
            vector.get("scenario")
            for vector in VECTORS["negative"]
            if vector.get("category") == "cycle"
        }
        self.assertEqual(
            {
                "self-reference",
                "mutual-reference",
                "circular-aggregate",
            },
            scenarios,
        )

    def test_missing_family_vector_fails_closed(self) -> None:
        vectors = copy.deepcopy(VECTORS)
        vectors["positive"] = [
            vector
            for vector in vectors["positive"]
            if vector["family_id"] != "gve-production"
        ]
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "positive vector family coverage is incomplete",
        ):
            validate_fixed_identity_vectors(FRAMEWORK, vectors)

    def test_missing_negative_category_fails_closed(self) -> None:
        vectors = copy.deepcopy(VECTORS)
        vectors["negative"] = [
            vector
            for vector in vectors["negative"]
            if vector.get("category") != "omitted-prefix"
        ]
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "negative vector category coverage is incomplete",
        ):
            validate_fixed_identity_vectors(FRAMEWORK, vectors)


if __name__ == "__main__":
    unittest.main()
