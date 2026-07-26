from __future__ import annotations

import copy
import unittest
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "specs/schemas"
FIXTURES = ROOT / "specs/tests/fixtures/issue_83"

DIAGNOSTIC_IDENTITIES = {
    "request": {
        "required": {"request_id"},
        "forbidden": {"workflow_id", "operation_id"},
    },
    "workflow": {
        "required": {"request_id", "workflow_id"},
        "forbidden": {"operation_id"},
    },
    "operation": {
        "required": {"request_id", "workflow_id", "operation_id"},
        "forbidden": set(),
    },
    "result": {
        "required": set(),
        "forbidden": {"request_id", "workflow_id", "operation_id"},
    },
}

DIAGNOSTIC_CODE_STAGES = {
    "GVE-S2-INVALID-JSON": {"json-parsing"},
    "GVE-S2-INVALID-PAYLOAD": {"payload-validation"},
    "GVE-S2-DUPLICATE-IDENTITY": {"identity-validation"},
    "GVE-S2-PROCESSING-FAILURE": {"no-op-disposition"},
    "GVE-S2-RESULT-CONSTRUCTION-FAILURE": {"result-construction"},
}

FATAL_CODE_STAGES = {
    "GVE-S2-INVALID-UTF8": {"utf8-decoding"},
    "GVE-S2-INVALID-JSON": {"json-parsing"},
    "GVE-S2-RESULT-CONSTRUCTION-FAILURE": {"result-construction"},
}


def semantic_errors(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    workflow = result["workflow"]
    operations = workflow["operations"]
    operation_ids = [item["operation_id"] for item in operations]
    if len(operation_ids) != len(set(operation_ids)):
        errors.append("duplicate operation_id")

    states = [workflow["effects"]]
    states.extend(item["effects"] for item in operations)
    for state in states:
        if state["request"] == "not-requested":
            if state["authorization"] == "authorized":
                errors.append("unrequested effect cannot be authorized")
            if state["execution"] != "unattempted":
                errors.append("unrequested effect must be unattempted")
        if state["execution"] == "completed" and state["authorization"] != "authorized":
            errors.append("completed effect must be authorized")
        if state["verification"] == "verified" and state["observation"] != "observed":
            errors.append("verified effect must be observed")

    processing = result["processing"]
    process = result["process"]
    diagnostics = result["diagnostics"]
    if processing["status"] == "succeeded":
        if processing["failure_stage"] is not None:
            errors.append("success failure stage mismatch")
        if workflow["status"] != "no-op-completed":
            errors.append("success workflow status mismatch")
        if any(item["status"] != "no-op" for item in operations):
            errors.append("success operation status mismatch")
        if diagnostics or process["exit_code"] != 0:
            errors.append("success terminal mapping mismatch")
    elif processing["status"] == "rejected":
        if processing["failure_stage"] not in {
            "payload-validation",
            "identity-validation",
        }:
            errors.append("rejected failure stage mismatch")
        if workflow["status"] != "rejected":
            errors.append("rejected workflow status mismatch")
        if any(item["status"] != "unattempted" for item in operations):
            errors.append("rejected operation status mismatch")
        if not diagnostics or process["exit_code"] != 2:
            errors.append("rejected terminal mapping mismatch")
    elif processing["status"] == "failed":
        if processing["failure_stage"] not in {
            "no-op-disposition",
            "result-construction",
        }:
            errors.append("failed failure stage mismatch")
        if workflow["status"] != "failed":
            errors.append("failed workflow status mismatch")
        if any(item["status"] not in {"unattempted", "failed"} for item in operations):
            errors.append("failed operation status mismatch")
        if not diagnostics or process["exit_code"] != 3:
            errors.append("failed terminal mapping mismatch")

    diagnostic_ids = [item["diagnostic_id"] for item in diagnostics]
    if len(diagnostic_ids) != len(set(diagnostic_ids)):
        errors.append("duplicate diagnostic_id")
    for item in diagnostics:
        policy = DIAGNOSTIC_IDENTITIES[item["scope"]]
        present = {
            key
            for key in ("request_id", "workflow_id", "operation_id")
            if key in item
        }
        missing = policy["required"] - present
        forbidden = policy["forbidden"] & present
        if missing:
            errors.append("diagnostic identity required by scope")
        if forbidden:
            errors.append("diagnostic identity forbidden by scope")
        if item.get("request_id") not in (None, result["request_id"]):
            errors.append("diagnostic request identity mismatch")
        if item.get("workflow_id") not in (None, workflow["workflow_id"]):
            errors.append("diagnostic workflow identity mismatch")
        if "operation_id" in item and item["operation_id"] not in operation_ids:
            errors.append("diagnostic operation identity mismatch")
        if item["stage"] not in DIAGNOSTIC_CODE_STAGES[item["code"]]:
            errors.append("diagnostic code stage mismatch")
    return errors


def fatal_semantic_errors(failure: dict[str, Any]) -> list[str]:
    if failure["stage"] not in FATAL_CODE_STAGES[failure["code"]]:
        return ["fatal code stage mismatch"]
    return []


class Issue83AuthoritativeResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result_schema = load_strict(
            SCHEMAS / "GVE-STAGE-2-AUTHORITATIVE-RESULT.schema.json"
        )
        cls.fatal_schema = load_strict(
            SCHEMAS / "GVE-STAGE-2-FATAL-FAILURE.schema.json"
        )
        Draft202012Validator.check_schema(cls.result_schema)
        Draft202012Validator.check_schema(cls.fatal_schema)
        cls.result_validator = Draft202012Validator(cls.result_schema)
        cls.fatal_validator = Draft202012Validator(cls.fatal_schema)

    def test_canonical_authoritative_results_are_accepted(self) -> None:
        for filename in (
            "success.json",
            "invalid-input-result.json",
            "processing-failure-result.json",
        ):
            with self.subTest(filename=filename):
                value = load_strict(FIXTURES / "canonical" / filename)
                self.assertEqual(
                    list(self.result_validator.iter_errors(value)),
                    [],
                )
                self.assertEqual(semantic_errors(value), [])

    def test_canonical_fatal_failure_is_accepted(self) -> None:
        value = load_strict(FIXTURES / "canonical/fatal-no-result.json")
        self.assertEqual(list(self.fatal_validator.iter_errors(value)), [])
        self.assertEqual(fatal_semantic_errors(value), [])

    def test_schema_invalid_fixtures_are_rejected(self) -> None:
        for filename in (
            "unknown-result-member.json",
            "invalid-processing-status.json",
            "invalid-diagnostic-code.json",
            "invalid-failure-stage.json",
            "missing-required-member.json",
        ):
            with self.subTest(filename=filename):
                value = load_strict(FIXTURES / "invalid" / filename)
                self.assertTrue(list(self.result_validator.iter_errors(value)))

    def test_semantic_invalid_fixtures_are_rejected(self) -> None:
        for filename in (
            "duplicate-operation-id.json",
            "invalid-effect-progression.json",
            "diagnostic-scope-identity-mismatch.json",
            "diagnostic-code-stage-mismatch.json",
            "terminal-status-combination.json",
        ):
            with self.subTest(filename=filename):
                value = load_strict(FIXTURES / "invalid" / filename)
                self.assertEqual(
                    list(self.result_validator.iter_errors(value)),
                    [],
                )
                self.assertTrue(semantic_errors(value))

    def test_fatal_unknown_member_is_rejected(self) -> None:
        value = load_strict(FIXTURES / "invalid/fatal-unknown-member.json")
        self.assertTrue(list(self.fatal_validator.iter_errors(value)))

    def test_fatal_code_stage_matrix_is_exact(self) -> None:
        value = load_strict(FIXTURES / "canonical/fatal-no-result.json")
        invalid = copy.deepcopy(value)
        invalid["stage"] = "result-construction"
        self.assertEqual(list(self.fatal_validator.iter_errors(invalid)), [])
        self.assertEqual(
            fatal_semantic_errors(invalid),
            ["fatal code stage mismatch"],
        )

    def test_terminal_class_matrix_is_exact(self) -> None:
        matrix = load_strict(FIXTURES / "terminal-classes.json")
        self.assertEqual(
            matrix["terminal_classes"],
            [
                {
                    "id": "success",
                    "authoritative_result": True,
                    "processing_status": "succeeded",
                    "exit_code": 0,
                    "stdout": "authoritative-result",
                    "stderr": "empty",
                },
                {
                    "id": "invalid-input-result",
                    "authoritative_result": True,
                    "processing_status": "rejected",
                    "exit_code": 2,
                    "stdout": "authoritative-result",
                    "stderr": "empty",
                },
                {
                    "id": "processing-failure-result",
                    "authoritative_result": True,
                    "processing_status": "failed",
                    "exit_code": 3,
                    "stdout": "authoritative-result",
                    "stderr": "empty",
                },
                {
                    "id": "fatal-no-result",
                    "authoritative_result": False,
                    "processing_status": None,
                    "exit_code": 4,
                    "stdout": "empty",
                    "stderr": "fatal-failure",
                },
            ],
        )

    def test_no_op_never_claims_effect_progress(self) -> None:
        value = load_strict(FIXTURES / "canonical/success.json")
        self.assertEqual(value["diagnostics"], [])
        self.assertEqual(value["workflow"]["status"], "no-op-completed")
        self.assertEqual(value["processing"]["failure_stage"], None)
        self.assertEqual(value["process"]["exit_code"], 0)

        workflow_state = value["workflow"]["effects"]
        operations = value["workflow"]["operations"]
        self.assertTrue(operations)
        for operation in operations:
            self.assertEqual(operation["status"], "no-op")

        states = [workflow_state]
        states.extend(item["effects"] for item in operations)
        for state in states:
            self.assertEqual(state["request"], "not-requested")
            self.assertEqual(state["authorization"], "indeterminate")
            self.assertEqual(state["execution"], "unattempted")
            self.assertEqual(state["observation"], "unobserved")
            self.assertEqual(state["verification"], "unverified")


if __name__ == "__main__":
    unittest.main()
