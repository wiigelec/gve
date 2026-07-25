"""Deterministic non-circular planning identities for GVE conformance tests."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping, Sequence

from .canonical_json import canonical_json

PLAN_CANDIDATE_FORMAT = "gve-plan-candidate-v1"
CONTRACT_PRODUCTION_FORMAT = "gve-contract-production-v1"
ACCEPTED_PLAN_FORMAT = "gve-accepted-plan-v1"
EXECUTION_ATTEMPT_FORMAT = "gve-execution-attempt-v1"

_SHA256 = re.compile(r"[0-9a-f]{64}")


class PlanningIdentityError(ValueError):
    """Raised when planning identity facts are incomplete or noncanonical."""


def _identity(value: Any, location: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise PlanningIdentityError(f"{location} must be lowercase SHA-256")
    return value


def _nonempty(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise PlanningIdentityError(f"{location} must be a nonempty string")
    return value


def _positive_integer(value: Any, location: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise PlanningIdentityError(f"{location} must be an integer")
    if value < 1:
        raise PlanningIdentityError(f"{location} must be positive")
    return value


def _exact(value: Any, fields: set[str], location: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PlanningIdentityError(f"{location} must be an object")
    actual = set(value)
    if actual != fields:
        missing = sorted(fields - actual)
        unknown = sorted(actual - fields)
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if unknown:
            detail.append("unknown " + ", ".join(unknown))
        raise PlanningIdentityError(f"{location} fields invalid: {'; '.join(detail)}")
    return value


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def canonical_plan_candidate(
    *,
    workflow_identity: str,
    operations: Sequence[Mapping[str, Any]],
    governance_binding_identity: str,
    plugin_registry_snapshot_identity: str,
    ordering_identity: str,
    dependency_identity: str,
    handoff_identity: str,
) -> dict[str, Any]:
    _nonempty(workflow_identity, "workflow_identity")
    _identity(governance_binding_identity, "governance_binding_identity")
    _identity(plugin_registry_snapshot_identity, "plugin_registry_snapshot_identity")
    _identity(ordering_identity, "ordering_identity")
    _identity(dependency_identity, "dependency_identity")
    _identity(handoff_identity, "handoff_identity")

    required = {
        "operation_identity",
        "operation_content_identity",
        "plugin_identity",
        "action_identity",
        "action_registry_snapshot_identity",
    }
    canonical_operations = []
    seen = set()
    for index, raw in enumerate(operations):
        item = _exact(raw, required, f"operations[{index}]")
        operation_identity = _nonempty(
            item["operation_identity"], f"operations[{index}].operation_identity"
        )
        if operation_identity in seen:
            raise PlanningIdentityError("duplicate operation_identity")
        seen.add(operation_identity)
        canonical_operations.append(
            {
                "operation_identity": operation_identity,
                "operation_content_identity": _identity(
                    item["operation_content_identity"],
                    f"operations[{index}].operation_content_identity",
                ),
                "plugin_identity": _nonempty(
                    item["plugin_identity"], f"operations[{index}].plugin_identity"
                ),
                "action_identity": _nonempty(
                    item["action_identity"], f"operations[{index}].action_identity"
                ),
                "action_registry_snapshot_identity": _identity(
                    item["action_registry_snapshot_identity"],
                    f"operations[{index}].action_registry_snapshot_identity",
                ),
            }
        )
    if not canonical_operations:
        raise PlanningIdentityError("operations must not be empty")
    canonical_operations.sort(key=lambda item: item["operation_identity"])
    return {
        "format": PLAN_CANDIDATE_FORMAT,
        "workflow_identity": workflow_identity,
        "operations": canonical_operations,
        "governance_binding_identity": governance_binding_identity,
        "plugin_registry_snapshot_identity": plugin_registry_snapshot_identity,
        "ordering_identity": ordering_identity,
        "dependency_identity": dependency_identity,
        "handoff_identity": handoff_identity,
    }


def plan_candidate_identity(candidate: Mapping[str, Any]) -> str:
    validate_plan_candidate(candidate)
    return _digest(candidate)


def validate_plan_candidate(candidate: Mapping[str, Any]) -> None:
    rebuilt = canonical_plan_candidate(
        workflow_identity=candidate.get("workflow_identity"),
        operations=candidate.get("operations", ()),
        governance_binding_identity=candidate.get("governance_binding_identity"),
        plugin_registry_snapshot_identity=candidate.get(
            "plugin_registry_snapshot_identity"
        ),
        ordering_identity=candidate.get("ordering_identity"),
        dependency_identity=candidate.get("dependency_identity"),
        handoff_identity=candidate.get("handoff_identity"),
    )
    if dict(candidate) != rebuilt:
        raise PlanningIdentityError("plan candidate is noncanonical")


def contract_production_identity(
    *,
    plan_candidate_identity: str,
    operation_identity: str,
    interpreted_inputs_identity: str,
    production_ordinal: int,
) -> str:
    _identity(plan_candidate_identity, "plan_candidate_identity")
    _nonempty(operation_identity, "operation_identity")
    _identity(interpreted_inputs_identity, "interpreted_inputs_identity")
    _positive_integer(production_ordinal, "production_ordinal")
    return _digest(
        {
            "format": CONTRACT_PRODUCTION_FORMAT,
            "plan_candidate_identity": plan_candidate_identity,
            "operation_identity": operation_identity,
            "interpreted_inputs_identity": interpreted_inputs_identity,
            "production_ordinal": production_ordinal,
        }
    )


def accepted_plan_identity(
    candidate: Mapping[str, Any], contracts: Sequence[Mapping[str, Any]]
) -> str:
    """Validate complete contract attribution and construct accepted-plan identity."""
    candidate_id = plan_candidate_identity(candidate)
    required = {
        "operation_identity",
        "plan_candidate_identity",
        "interpreted_inputs_identity",
        "production_ordinal",
        "contract_identity",
        "contract_production_identity",
    }
    by_operation = {}
    seen_contract_identities = set()
    seen_production_identities = set()
    for index, raw in enumerate(contracts):
        item = _exact(raw, required, f"contracts[{index}]")
        operation_identity = _nonempty(
            item["operation_identity"], f"contracts[{index}].operation_identity"
        )
        if operation_identity in by_operation:
            raise PlanningIdentityError("duplicate contract operation_identity")
        bound_candidate = _identity(
            item["plan_candidate_identity"],
            f"contracts[{index}].plan_candidate_identity",
        )
        if bound_candidate != candidate_id:
            raise PlanningIdentityError("contract binds another plan candidate")
        interpreted_inputs_identity = _identity(
            item["interpreted_inputs_identity"],
            f"contracts[{index}].interpreted_inputs_identity",
        )
        production_ordinal = _positive_integer(
            item["production_ordinal"], f"contracts[{index}].production_ordinal"
        )
        contract_identity = _identity(
            item["contract_identity"], f"contracts[{index}].contract_identity"
        )
        if contract_identity in seen_contract_identities:
            raise PlanningIdentityError("duplicate contract_identity")
        seen_contract_identities.add(contract_identity)
        production_identity = _identity(
            item["contract_production_identity"],
            f"contracts[{index}].contract_production_identity",
        )
        expected_production_identity = contract_production_identity(
            plan_candidate_identity=candidate_id,
            operation_identity=operation_identity,
            interpreted_inputs_identity=interpreted_inputs_identity,
            production_ordinal=production_ordinal,
        )
        if production_identity in seen_production_identities:
            raise PlanningIdentityError("duplicate contract_production_identity")
        seen_production_identities.add(production_identity)
        if production_identity != expected_production_identity:
            raise PlanningIdentityError("contract production attribution is invalid")
        by_operation[operation_identity] = {
            "operation_identity": operation_identity,
            "plan_candidate_identity": bound_candidate,
            "interpreted_inputs_identity": interpreted_inputs_identity,
            "production_ordinal": production_ordinal,
            "contract_identity": contract_identity,
            "contract_production_identity": production_identity,
        }

    expected = {item["operation_identity"] for item in candidate["operations"]}
    if set(by_operation) != expected:
        raise PlanningIdentityError("contracts do not exactly cover candidate operations")
    return _digest(
        {
            "format": ACCEPTED_PLAN_FORMAT,
            "plan_candidate_identity": candidate_id,
            "contracts": [by_operation[key] for key in sorted(by_operation)],
        }
    )


def execution_attempt_identity(
    *, accepted_plan_identity: str, operation_identity: str, attempt_ordinal: int
) -> str:
    _identity(accepted_plan_identity, "accepted_plan_identity")
    _nonempty(operation_identity, "operation_identity")
    _positive_integer(attempt_ordinal, "attempt_ordinal")
    return _digest(
        {
            "format": EXECUTION_ATTEMPT_FORMAT,
            "accepted_plan_identity": accepted_plan_identity,
            "operation_identity": operation_identity,
            "attempt_ordinal": attempt_ordinal,
        }
    )
