from __future__ import annotations

import unittest
from collections.abc import Mapping

from specs.tooling.planning_identity import (
    PlanningIdentityError,
    accepted_plan_identity,
    canonical_plan_candidate,
    contract_production_identity,
    execution_attempt_identity,
    plan_candidate_identity,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64
ZERO = "0" * 64
ONE = "1" * 64


class SingleReadMapping(Mapping):
    def __init__(self, values):
        self._values = dict(values)
        self._reads = {key: 0 for key in self._values}

    def __iter__(self):
        return iter(reversed(tuple(self._values)))

    def __len__(self):
        return len(self._values)

    def __getitem__(self, key):
        self._reads[key] += 1
        if self._reads[key] > 1:
            raise RuntimeError(f"second read of {key}")
        return self._values[key]


class UnsnapshotableMapping(Mapping):
    def __iter__(self):
        return iter(("format",))

    def __len__(self):
        return 1

    def __getitem__(self, key):
        raise RuntimeError("changed during read")


def operation(identity: str, content: str, plugin: str = "plugin-a") -> dict[str, str]:
    return {
        "operation_identity": identity,
        "operation_content_identity": content,
        "plugin_identity": plugin,
        "action_identity": "run",
        "action_registry_snapshot_identity": F,
    }


class PlanningIdentityTests(unittest.TestCase):
    def candidate(self, operations=None, ordering_identity=ZERO):
        return canonical_plan_candidate(
            workflow_identity="workflow-a",
            operations=(
                [operation("op-a", A), operation("op-b", B)]
                if operations is None
                else operations
            ),
            governance_binding_identity=C,
            plugin_registry_snapshot_identity=D,
            ordering_identity=ordering_identity,
            dependency_identity=E,
            handoff_identity=F,
        )

    def contract(
        self,
        candidate_id,
        operation_identity,
        *,
        interpreted_inputs_identity=A,
        ordinal=1,
        contract_identity=None,
    ):
        production = contract_production_identity(
            plan_candidate_identity=candidate_id,
            operation_identity=operation_identity,
            interpreted_inputs_identity=interpreted_inputs_identity,
            production_ordinal=ordinal,
        )
        identities = {"op-a": B, "op-b": C}
        return {
            "operation_identity": operation_identity,
            "plan_candidate_identity": candidate_id,
            "interpreted_inputs_identity": interpreted_inputs_identity,
            "production_ordinal": ordinal,
            "contract_identity": contract_identity or identities[operation_identity],
            "contract_production_identity": production,
        }

    def accepted_contracts(self, candidate):
        candidate_id = plan_candidate_identity(candidate)
        return [
            self.contract(candidate_id, "op-a"),
            self.contract(candidate_id, "op-b"),
        ]


    def test_explicit_empty_operations_fail(self):
        with self.assertRaisesRegex(PlanningIdentityError, "operations must not be empty"):
            self.candidate([])

    def test_nonmapping_candidate_uses_governed_exception(self):
        with self.assertRaisesRegex(PlanningIdentityError, "plan candidate must be an object"):
            plan_candidate_identity([])

    def test_nonmapping_operation_uses_governed_exception(self):
        with self.assertRaisesRegex(PlanningIdentityError, r"operations\[0\] must be an object"):
            self.candidate(["not-an-operation"])

    def test_candidate_mapping_is_snapshotted_once(self):
        candidate = self.candidate()
        self.assertEqual(
            plan_candidate_identity(SingleReadMapping(candidate)),
            plan_candidate_identity(candidate),
        )

    def test_operation_mapping_is_snapshotted_once(self):
        ordinary = self.candidate([operation("op-a", A)])
        snapshotted = self.candidate([SingleReadMapping(operation("op-a", A))])
        self.assertEqual(snapshotted, ordinary)

    def test_contract_mapping_is_snapshotted_once(self):
        candidate = self.candidate()
        contracts = self.accepted_contracts(candidate)
        self.assertEqual(
            accepted_plan_identity(
                candidate, [SingleReadMapping(item) for item in contracts]
            ),
            accepted_plan_identity(candidate, contracts),
        )

    def test_mapping_snapshot_failure_is_deterministic(self):
        with self.assertRaisesRegex(
            PlanningIdentityError, "plan candidate could not be snapshotted"
        ):
            plan_candidate_identity(UnsnapshotableMapping())

    def test_candidate_identity_is_discovery_order_independent(self):
        first = self.candidate([operation("op-b", B), operation("op-a", A)])
        second = self.candidate([operation("op-a", A), operation("op-b", B)])
        self.assertEqual(first, second)
        self.assertEqual(plan_candidate_identity(first), plan_candidate_identity(second))

    def test_ordering_identity_participates_in_candidate_identity(self):
        self.assertNotEqual(
            plan_candidate_identity(self.candidate(ordering_identity=ZERO)),
            plan_candidate_identity(self.candidate(ordering_identity=ONE)),
        )

    def test_contracts_bind_existing_candidate_before_acceptance(self):
        candidate = self.candidate()
        accepted = accepted_plan_identity(candidate, self.accepted_contracts(candidate))
        self.assertEqual(len(accepted), 64)

    def test_contract_order_does_not_change_accepted_plan(self):
        candidate = self.candidate()
        contracts = self.accepted_contracts(candidate)
        self.assertEqual(
            accepted_plan_identity(candidate, contracts),
            accepted_plan_identity(candidate, list(reversed(contracts))),
        )

    def test_changed_operation_requires_new_candidate(self):
        self.assertNotEqual(
            plan_candidate_identity(self.candidate([operation("op-a", A)])),
            plan_candidate_identity(self.candidate([operation("op-a", B)])),
        )

    def test_changed_plugin_requires_new_candidate(self):
        self.assertNotEqual(
            plan_candidate_identity(self.candidate([operation("op-a", A, "plugin-a")])),
            plan_candidate_identity(self.candidate([operation("op-a", A, "plugin-b")])),
        )

    def test_regeneration_is_distinct_from_replay(self):
        candidate_id = plan_candidate_identity(self.candidate())
        first = contract_production_identity(
            plan_candidate_identity=candidate_id,
            operation_identity="op-a",
            interpreted_inputs_identity=A,
            production_ordinal=1,
        )
        replay = contract_production_identity(
            plan_candidate_identity=candidate_id,
            operation_identity="op-a",
            interpreted_inputs_identity=A,
            production_ordinal=1,
        )
        regenerated = contract_production_identity(
            plan_candidate_identity=candidate_id,
            operation_identity="op-a",
            interpreted_inputs_identity=A,
            production_ordinal=2,
        )
        self.assertEqual(first, replay)
        self.assertNotEqual(first, regenerated)

    def test_contract_for_another_candidate_fails(self):
        candidate = self.candidate()
        with self.assertRaisesRegex(PlanningIdentityError, "another plan candidate"):
            accepted_plan_identity(
                candidate,
                [self.contract(A, "op-a"), self.contract(A, "op-b")],
            )

    def test_partial_contract_set_fails(self):
        candidate = self.candidate()
        candidate_id = plan_candidate_identity(candidate)
        with self.assertRaisesRegex(PlanningIdentityError, "exactly cover"):
            accepted_plan_identity(
                candidate, [self.contract(candidate_id, "op-a")]
            )

    def test_duplicate_candidate_operation_fails(self):
        with self.assertRaisesRegex(PlanningIdentityError, "duplicate operation_identity"):
            self.candidate([operation("op-a", A), operation("op-a", B)])

    def test_arbitrary_production_identity_fails(self):
        candidate = self.candidate()
        contracts = self.accepted_contracts(candidate)
        contracts[0]["contract_production_identity"] = F
        with self.assertRaisesRegex(PlanningIdentityError, "attribution is invalid"):
            accepted_plan_identity(candidate, contracts)

    def test_cross_operation_production_identity_fails(self):
        candidate = self.candidate()
        contracts = self.accepted_contracts(candidate)
        contracts[1]["contract_production_identity"] = contracts[0][
            "contract_production_identity"
        ]
        with self.assertRaisesRegex(
            PlanningIdentityError, "duplicate contract_production_identity"
        ):
            accepted_plan_identity(candidate, contracts)

    def test_changed_interpreted_inputs_with_reused_production_identity_fails(self):
        candidate = self.candidate()
        contracts = self.accepted_contracts(candidate)
        contracts[0]["interpreted_inputs_identity"] = D
        with self.assertRaisesRegex(PlanningIdentityError, "attribution is invalid"):
            accepted_plan_identity(candidate, contracts)

    def test_duplicate_contract_identity_fails(self):
        candidate = self.candidate()
        contracts = self.accepted_contracts(candidate)
        contracts[1]["contract_identity"] = contracts[0]["contract_identity"]
        with self.assertRaisesRegex(PlanningIdentityError, "duplicate contract_identity"):
            accepted_plan_identity(candidate, contracts)

    def test_duplicate_contract_operation_identity_fails(self):
        candidate = self.candidate()
        candidate_id = plan_candidate_identity(candidate)
        contracts = [
            self.contract(candidate_id, "op-a", contract_identity=B),
            self.contract(candidate_id, "op-a", contract_identity=C),
        ]
        with self.assertRaisesRegex(
            PlanningIdentityError, "duplicate contract operation_identity"
        ):
            accepted_plan_identity(candidate, contracts)

    def test_missing_ordering_identity_fails(self):
        candidate = self.candidate()
        del candidate["ordering_identity"]
        with self.assertRaises(PlanningIdentityError):
            plan_candidate_identity(candidate)

    def test_incomplete_contract_attribution_fails(self):
        candidate = self.candidate()
        contracts = self.accepted_contracts(candidate)
        del contracts[0]["production_ordinal"]
        with self.assertRaisesRegex(PlanningIdentityError, "fields invalid"):
            accepted_plan_identity(candidate, contracts)

    def test_execution_attempt_requires_accepted_plan_identity(self):
        candidate = self.candidate()
        accepted = accepted_plan_identity(candidate, self.accepted_contracts(candidate))
        first = execution_attempt_identity(
            accepted_plan_identity=accepted, operation_identity="op-a", attempt_ordinal=1
        )
        retry = execution_attempt_identity(
            accepted_plan_identity=accepted, operation_identity="op-a", attempt_ordinal=2
        )
        self.assertNotEqual(first, retry)

    def test_candidate_identity_fixed_vector(self):
        self.assertEqual(
            plan_candidate_identity(self.candidate()),
            "8e9f0b0c9315804a842d125316ead1090a5d785ca56b185e8efa8ca557d3e9f1",
        )


if __name__ == "__main__":
    unittest.main()
