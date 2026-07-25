from __future__ import annotations

import unittest

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


def operation(identity: str, content: str, plugin: str = "plugin-a") -> dict[str, str]:
    return {
        "operation_identity": identity,
        "operation_content_identity": content,
        "plugin_identity": plugin,
        "action_identity": "run",
        "action_registry_snapshot_identity": F,
    }


class PlanningIdentityTests(unittest.TestCase):
    def candidate(self, operations=None):
        return canonical_plan_candidate(
            workflow_identity="workflow-a",
            operations=operations or [operation("op-a", A), operation("op-b", B)],
            governance_binding_identity=C,
            plugin_registry_snapshot_identity=D,
            dependency_identity=E,
            handoff_identity=F,
        )

    def contract(self, candidate_id, operation_identity, ordinal=1):
        production = contract_production_identity(
            plan_candidate_identity=candidate_id,
            operation_identity=operation_identity,
            interpreted_inputs_identity=A,
            production_ordinal=ordinal,
        )
        return {
            "operation_identity": operation_identity,
            "plan_candidate_identity": candidate_id,
            "contract_identity": B,
            "contract_production_identity": production,
        }

    def test_candidate_identity_is_discovery_order_independent(self):
        first = self.candidate([operation("op-b", B), operation("op-a", A)])
        second = self.candidate([operation("op-a", A), operation("op-b", B)])
        self.assertEqual(first, second)
        self.assertEqual(plan_candidate_identity(first), plan_candidate_identity(second))

    def test_contracts_bind_existing_candidate_before_acceptance(self):
        candidate = self.candidate()
        candidate_id = plan_candidate_identity(candidate)
        contracts = [self.contract(candidate_id, "op-b"), self.contract(candidate_id, "op-a")]
        accepted = accepted_plan_identity(candidate, contracts)
        self.assertEqual(len(accepted), 64)
        self.assertEqual(candidate_id, plan_candidate_identity(candidate))

    def test_contract_order_does_not_change_accepted_plan(self):
        candidate = self.candidate()
        candidate_id = plan_candidate_identity(candidate)
        first = [self.contract(candidate_id, "op-a"), self.contract(candidate_id, "op-b")]
        self.assertEqual(
            accepted_plan_identity(candidate, first),
            accepted_plan_identity(candidate, list(reversed(first))),
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
        with self.assertRaisesRegex(PlanningIdentityError, "contract binds another plan candidate"):
            accepted_plan_identity(
                candidate,
                [self.contract(A, "op-a"), self.contract(A, "op-b")],
            )

    def test_partial_contract_set_fails(self):
        candidate = self.candidate()
        candidate_id = plan_candidate_identity(candidate)
        with self.assertRaisesRegex(PlanningIdentityError, "exactly cover candidate operations"):
            accepted_plan_identity(candidate, [self.contract(candidate_id, "op-a")])

    def test_duplicate_candidate_operation_fails(self):
        with self.assertRaisesRegex(PlanningIdentityError, "duplicate operation_identity"):
            self.candidate([operation("op-a", A), operation("op-a", B)])

    def test_execution_attempt_requires_accepted_plan_identity(self):
        candidate = self.candidate()
        candidate_id = plan_candidate_identity(candidate)
        accepted = accepted_plan_identity(
            candidate,
            [self.contract(candidate_id, "op-a"), self.contract(candidate_id, "op-b")],
        )
        first = execution_attempt_identity(
            accepted_plan_identity=accepted, operation_identity="op-a", attempt_ordinal=1
        )
        retry = execution_attempt_identity(
            accepted_plan_identity=accepted, operation_identity="op-a", attempt_ordinal=2
        )
        self.assertNotEqual(first, retry)

    def test_candidate_identity_fixed_vector(self):
        self.assertEqual(plan_candidate_identity(self.candidate()), "a1041ef0d09560e80efcf6152616752aca5b0e6d7dd0ceea0c6088c74726fd86")


if __name__ == "__main__":
    unittest.main()
