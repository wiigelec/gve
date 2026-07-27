from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"

VALID_OPERATION = {
    "operation_id": "operation-1",
    "plugin": {"plugin_id": "example.plugin", "action": "inspect"},
    "content": {"nested": {"unknown": [1, True, None]}},
}


def _payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 2,
        "lifecycle": "no-op",
        "workflow": {
            "workflow_id": "workflow-1",
            "operations": [VALID_OPERATION],
        },
    }
    payload.update(overrides)
    return payload


def _run(value: object) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SOURCE_ROOT)
    input_bytes = (json.dumps(value, separators=(",", ":")) + "\n").encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="gve-common-envelope-") as temporary:
        return subprocess.run(
            [sys.executable, "-m", "gve"],
            cwd=temporary,
            env=environment,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


class CommonPayloadValidationTests(unittest.TestCase):
    def test_missing_authoritative_identity_set_is_fatal_result_construction(self) -> None:
        cases = (
            [],
            {},
            {"workflow": None},
            {"workflow": {}},
            {"workflow": {"workflow_id": "", "operations": [VALID_OPERATION]}},
            {"workflow": {"workflow_id": "workflow-1", "operations": []}},
            {
                "workflow": {
                    "workflow_id": "workflow-1",
                    "operations": [{"plugin": {}, "content": {}}],
                }
            },
        )
        for value in cases:
            with self.subTest(value=value):
                completed = _run(value)
                self.assertEqual(completed.returncode, 4)
                self.assertEqual(completed.stdout, b"")
                failure = json.loads(completed.stderr)
                self.assertEqual(
                    failure["code"], "GVE-S2-RESULT-CONSTRUCTION-FAILURE"
                )
                self.assertEqual(failure["stage"], "result-construction")
                self.assertEqual(failure["process"]["exit_code"], 4)
                self.assertNotIn(b"Traceback", completed.stderr)

    def test_complete_identity_set_schema_failures_are_authoritative_rejections(self) -> None:
        malformed_operations = (
            {**VALID_OPERATION, "content": None},
            {**VALID_OPERATION, "content": []},
            {**VALID_OPERATION, "plugin": None},
            {
                **VALID_OPERATION,
                "plugin": {"plugin_id": "", "action": "inspect"},
            },
            {
                **VALID_OPERATION,
                "plugin": {"plugin_id": "example.plugin", "action": ""},
            },
            {**VALID_OPERATION, "unexpected": True},
        )
        cases = [
            _payload(schema_version=1),
            _payload(schema_version="2"),
            _payload(workflow={
                "workflow_id": "workflow-1",
                "operations": [VALID_OPERATION],
                "unexpected": True,
            }),
        ]
        cases.extend(
            _payload(
                workflow={
                    "workflow_id": "workflow-1",
                    "operations": [operation],
                }
            )
            for operation in malformed_operations
        )

        for value in cases:
            with self.subTest(value=value):
                completed = _run(value)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stderr, b"")
                result = json.loads(completed.stdout)
                self.assertEqual(result["processing"]["status"], "rejected")
                self.assertEqual(
                    result["processing"]["failure_stage"], "payload-validation"
                )
                self.assertEqual(result["workflow"]["status"], "rejected")
                self.assertEqual(
                    [item["operation_id"] for item in result["workflow"]["operations"]],
                    ["operation-1"],
                )
                self.assertEqual(
                    result["diagnostics"][0]["code"], "GVE-S2-INVALID-PAYLOAD"
                )
                self.assertNotIn(b"Traceback", completed.stdout)

    def test_arbitrary_nested_object_content_remains_opaque_and_accepted(self) -> None:
        completed = _run(_payload())
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stderr, b"")
        result = json.loads(completed.stdout)
        self.assertEqual(result["processing"]["status"], "succeeded")
        self.assertEqual(result["workflow"]["status"], "no-op-completed")
        self.assertEqual(result["workflow"]["operations"][0]["status"], "no-op")


if __name__ == "__main__":
    unittest.main()
