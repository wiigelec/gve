from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from specs.tooling.identity import (
    IdentityFrameworkError,
    compute_identity,
    validate_identity_framework,
    verify_identity,
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


def _vector(vector_id: str) -> dict:
    return next(
        vector
        for vector in VECTORS["positive"]
        if vector["id"] == vector_id
    )


class Issue76ExecutablePreimageTests(unittest.TestCase):
    def test_every_family_has_machine_readable_preimage(self) -> None:
        for family in FRAMEWORK["identity_families"]:
            preimage = family["preimage"]
            self.assertEqual(preimage["value_source"], "complete-object")
            self.assertTrue(preimage["own_identity_paths"])
            self.assertIn(
                preimage["reference_encoding"],
                {"by-value", "by-identity", "identity-plus-value"},
            )
            self.assertEqual(
                set(preimage["version_bindings"]),
                {"canonicalization", "governing_specification_revision"},
            )

    def test_all_reference_modes_have_positive_vectors(self) -> None:
        ids = {vector["id"] for vector in VECTORS["positive"]}
        self.assertIn("reference-by-value", ids)
        self.assertIn("reference-by-identity", ids)
        self.assertIn("reference-identity-plus-value", ids)

    def test_by_value_changes_with_referenced_value(self) -> None:
        vector = _vector("reference-by-value")
        changed = copy.deepcopy(vector["value"])
        changed["references"][0]["value"]["count"] = 2
        self.assertNotEqual(
            vector["expected_identity"],
            compute_identity(FRAMEWORK, vector["family_id"], changed),
        )

    def test_by_identity_rejects_wrong_family(self) -> None:
        vector = _vector("reference-by-identity")
        changed = copy.deepcopy(vector["value"])
        changed["references"][0]["identity"] = _vector(
            "effect-object"
        )["expected_identity"]
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "reference identity family does not match",
        ):
            compute_identity(FRAMEWORK, vector["family_id"], changed)

    def test_identity_plus_value_rejects_mismatch(self) -> None:
        vector = _vector("reference-identity-plus-value")
        changed = copy.deepcopy(vector["value"])
        changed["references"][0]["value"]["operation"] = "delete"
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "claimed identity does not match its canonical preimage",
        ):
            compute_identity(FRAMEWORK, vector["family_id"], changed)

    def test_missing_reference_representation_fails_closed(self) -> None:
        vector = _vector("reference-by-identity")
        changed = copy.deepcopy(vector["value"])
        changed["references"][0] = {}
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "missing or ambiguous",
        ):
            compute_identity(FRAMEWORK, vector["family_id"], changed)

    def test_ambiguous_reference_representation_fails_closed(self) -> None:
        vector = _vector("reference-by-value")
        changed = copy.deepcopy(vector["value"])
        changed["references"][0]["identity"] = _vector(
            "effect-object"
        )["expected_identity"]
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "missing or ambiguous",
        ):
            compute_identity(FRAMEWORK, vector["family_id"], changed)

    def test_unknown_own_identity_path_fails_closed(self) -> None:
        framework = copy.deepcopy(FRAMEWORK)
        framework["identity_families"][0]["preimage"][
            "own_identity_paths"
        ] = ["identity..value"]
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "unknown own-identity paths",
        ):
            validate_identity_framework(framework)

    def test_family_declared_digest_is_used(self) -> None:
        framework = copy.deepcopy(FRAMEWORK)
        family = next(
            item
            for item in framework["identity_families"]
            if item["id"] == "gve-plan"
        )
        family["digest_algorithm"] = "sha1"
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "unknown digest algorithm",
        ):
            compute_identity(framework, "gve-plan", {"plan": "alpha"})

    def test_stale_canonicalization_binding_is_rejected(self) -> None:
        vector = _vector("reference-by-value")
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "stale canonicalization binding",
        ):
            compute_identity(
                FRAMEWORK,
                vector["family_id"],
                vector["value"],
                version_bindings={"canonicalization": "stale-v0"},
            )

    def test_stale_governing_revision_binding_is_rejected(self) -> None:
        vector = _vector("governing-revision-binding")
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "stale governing specification revision binding",
        ):
            verify_identity(
                FRAMEWORK,
                vector["family_id"],
                vector["expected_identity"],
                vector["value"],
                version_bindings={
                    "governing_specification_revision": "legacy"
                },
            )

    def test_per_family_own_identity_path_is_executable(self) -> None:
        value = {"result_identity": "one", "result": "ok"}
        changed = {"result_identity": "two", "result": "ok"}
        self.assertEqual(
            compute_identity(FRAMEWORK, "gve-authoritative-result", value),
            compute_identity(FRAMEWORK, "gve-authoritative-result", changed),
        )


if __name__ == "__main__":
    unittest.main()
