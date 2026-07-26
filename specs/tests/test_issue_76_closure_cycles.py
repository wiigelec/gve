from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from specs.tooling.identity import (
    IdentityFrameworkError,
    compute_identity,
)


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = json.loads(
    (ROOT / "identity/GVE-IDENTITY-FRAMEWORK.json").read_text(encoding="utf-8")
)


class AggregateClosureAndCycleTests(unittest.TestCase):
    def test_direct_closure_rejects_undeclared_descendant_identity(self) -> None:
        leaf_value = {"contract": "leaf"}
        leaf_identity = compute_identity(FRAMEWORK, "gve-contract", leaf_value)
        parent_value = {
            "contract": "parent",
            "members": [{"identity": leaf_identity, "value": leaf_value}],
        }
        parent_identity = compute_identity(FRAMEWORK, "gve-contract", parent_value)
        root = {
            "composition": "root",
            "members": [{"identity": parent_identity, "value": parent_value}],
        }
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "membership is incomplete or inconsistent",
        ):
            compute_identity(
                FRAMEWORK,
                "gve-governance-composition",
                root,
                member_identities=[parent_identity, leaf_identity],
            )

    def test_transitive_closure_includes_every_reachable_member_once(self) -> None:
        framework = copy.deepcopy(FRAMEWORK)
        family = next(
            item
            for item in framework["identity_families"]
            if item["id"] == "gve-governance-composition"
        )
        family["object_kind"] = "transitive-closure"
        family["aggregate"]["closure_boundary"] = "transitive"

        leaf_value = {"contract": "leaf"}
        leaf_identity = compute_identity(framework, "gve-contract", leaf_value)
        parent_value = {
            "contract": "parent",
            "members": [{"identity": leaf_identity, "value": leaf_value}],
        }
        parent_identity = compute_identity(framework, "gve-contract", parent_value)
        root = {
            "composition": "root",
            "members": [{"identity": parent_identity, "value": parent_value}],
        }
        identity = compute_identity(
            framework,
            "gve-governance-composition",
            root,
            member_identities=[parent_identity, leaf_identity],
        )
        self.assertTrue(identity.startswith("gve-governance-composition-sha256:"))

        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "membership is incomplete or inconsistent",
        ):
            compute_identity(
                framework,
                "gve-governance-composition",
                root,
                member_identities=[parent_identity],
            )

    def test_transitive_closure_rejects_reachable_duplicate(self) -> None:
        framework = copy.deepcopy(FRAMEWORK)
        family = next(
            item
            for item in framework["identity_families"]
            if item["id"] == "gve-governance-composition"
        )
        family["object_kind"] = "transitive-closure"
        family["aggregate"]["closure_boundary"] = "transitive"

        leaf_value = {"contract": "leaf"}
        leaf_identity = compute_identity(framework, "gve-contract", leaf_value)
        parent_value = {
            "contract": "parent",
            "members": [
                {"identity": leaf_identity, "value": leaf_value},
                {"identity": leaf_identity, "value": leaf_value},
            ],
        }
        parent_identity = compute_identity(framework, "gve-contract", parent_value)
        root = {
            "composition": "root",
            "members": [{"identity": parent_identity, "value": parent_value}],
        }
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "duplicate or cyclic members",
        ):
            compute_identity(
                framework,
                "gve-governance-composition",
                root,
                member_identities=[parent_identity, leaf_identity],
            )

    def test_self_referential_object_graph_is_rejected(self) -> None:
        value = {"plan": "self"}
        value["references"] = [{"value": value}]
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "circular object identity construction",
        ):
            compute_identity(FRAMEWORK, "gve-plan", value)

    def test_two_object_reference_cycle_is_rejected(self) -> None:
        first = {"plan": "first"}
        second = {"plan": "second"}
        first["references"] = [{"value": second}]
        second["references"] = [{"value": first}]
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "circular object identity construction",
        ):
            compute_identity(FRAMEWORK, "gve-plan", first)

    def test_cycle_hidden_through_aggregate_member_is_rejected(self) -> None:
        root = {"composition": "root"}
        root["members"] = [
            {
                "identity": "gve-contract-sha256:" + "0" * 64,
                "value": root,
            }
        ]
        with self.assertRaisesRegex(
            IdentityFrameworkError,
            "circular object identity construction",
        ):
            compute_identity(
                FRAMEWORK,
                "gve-governance-composition",
                root,
                member_identities=["gve-contract-sha256:" + "0" * 64],
            )


if __name__ == "__main__":
    unittest.main()
